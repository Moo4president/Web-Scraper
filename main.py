"""
Entry point for CyberJob Scraper.

Overall flow:
  1. Ensure the database table exists (init_db).
  2. Collect job listings from all configured sources.
  3. Persist new listings to PostgreSQL, deduplicating by URL (save_jobs).
  4. Retrieve only the jobs inserted this run (get_new_jobs).
  5. Print a human-readable digest to the terminal.

Run with: python main.py
Schedule with cron for daily automated runs (see README).
"""

from db.database import init_db, save_jobs, get_new_jobs
from scrapers.greenhouse import scrape_greenhouse
from scrapers.lever import scrape_lever
from scrapers.workday import scrape_workday
from scrapers.company_pages import scrape_company_pages
from config import KEYWORDS, GREENHOUSE_COMPANIES, LEVER_COMPANIES, WORKDAY_COMPANIES, COMPANY_PAGES
from datetime import date


def print_digest(new_jobs):
    """Print a formatted summary of jobs found in this run.

    Args:
        new_jobs: List of RealDictRow objects returned by get_new_jobs().
                  Each row matches the 'jobs' table schema.
    """
    print(f"\n[{date.today()}] {len(new_jobs)} new job(s) found:\n")
    if not new_jobs:
        print("  No new postings since last run.\n")
        return
    for job in new_jobs:
        print(f"  [NEW] {job['title']} @ {job['company']}")
        print(f"        Location : {job['location']}")
        print(f"        Source   : {job['source']}")
        print(f"        Posted   : {job['posted_date']}")
        print(f"        URL      : {job['url']}\n")


def main():
    """Orchestrate a full scrape-store-report cycle."""
    init_db()

    jobs = []
    jobs += scrape_greenhouse(GREENHOUSE_COMPANIES, KEYWORDS)
    jobs += scrape_lever(LEVER_COMPANIES, KEYWORDS)
    # Workday is the slowest step — launches a real browser to render JS-heavy pages
    jobs += scrape_workday(WORKDAY_COMPANIES, KEYWORDS)
    jobs += scrape_company_pages(COMPANY_PAGES)

    save_jobs(jobs)
    new_jobs = get_new_jobs()
    print_digest(new_jobs)


if __name__ == "__main__":
    main()
