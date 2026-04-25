"""
Database layer for CyberJob Scraper.

Handles all PostgreSQL interaction: connection, schema creation, saving jobs,
and querying for new listings. Called by main.py after scraping is complete.

Connection credentials are read from environment variables (loaded from .env
by python-dotenv). See .env.example for required variables.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load DB credentials from .env before any connection is attempted
load_dotenv()


def get_conn():
    """Open and return a new PostgreSQL connection using environment variables.

    Returns:
        psycopg2 connection object. Caller is responsible for closing it.

    Note:
        On macOS with Homebrew PostgreSQL, DB_PASS can be left blank —
        local connections use trust authentication by default.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        dbname=os.getenv("DB_NAME", "cyberjobs"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", ""),
    )


def init_db():
    """Create the jobs table if it doesn't already exist.

    Safe to call on every run — CREATE TABLE IF NOT EXISTS is idempotent.
    Uses psycopg2's connection context manager, which auto-commits on success.
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          SERIAL PRIMARY KEY,
                title       TEXT NOT NULL,
                company     TEXT NOT NULL,
                location    TEXT,
                source      TEXT,
                url         TEXT UNIQUE NOT NULL,
                posted_date DATE,
                seen_at     TIMESTAMP DEFAULT NOW(),
                is_new      BOOLEAN DEFAULT TRUE
            );
        """)


def save_jobs(jobs):
    """Persist scraped jobs to the database with deduplication.

    Strategy:
      1. Mark every existing row as is_new = FALSE.
      2. Insert each job; skip silently if the URL already exists.
      3. New rows default to is_new = TRUE (set by the column default).
      4. Commit both steps as a single transaction — if something fails,
         the rollback ensures we never wipe is_new flags without saving results.

    Args:
        jobs: List of dicts with keys: title, company, location, source, url, posted_date.

    Side effects:
        Writes to the 'jobs' table. Commits or rolls back the transaction.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Reset all flags first so only jobs inserted THIS run show as new
            cur.execute("UPDATE jobs SET is_new = FALSE;")
            for j in jobs:
                cur.execute("""
                    INSERT INTO jobs (title, company, location, source, url, posted_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING;
                """, (j["title"], j["company"], j["location"],
                      j["source"], j["url"], j.get("posted_date")))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_new_jobs():
    """Return all jobs inserted during the most recent run.

    "New" is determined by the is_new flag, which save_jobs() manages:
    it resets all rows to FALSE then inserts fresh rows with the default TRUE.

    Returns:
        List of RealDictRow objects (behave like dicts), ordered newest first.
    """
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM jobs WHERE is_new = TRUE ORDER BY seen_at DESC;")
        return cur.fetchall()
