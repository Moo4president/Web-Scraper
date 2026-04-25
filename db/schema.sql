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
