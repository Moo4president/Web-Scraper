"""
Generic company career page scraper (HTML fallback).

Used for companies that don't use Greenhouse, Lever, or Workday. Instead of
hitting a structured API, this scraper fetches the raw HTML of a career page
and looks for anchor tags whose text or href suggests a job listing.

Limitations vs. API scrapers:
  - No structured data — we infer "is this a job?" from keyword matching on
    the link text and URL, which produces more false positives.
  - Location is unknown — no structured field to extract, so we default to
    "See posting" and let the user check the actual page.
  - JavaScript-rendered pages won't work here (use workday.py pattern instead).
"""

import requests
from bs4 import BeautifulSoup

# Mimic a real browser to reduce the chance of being blocked by basic bot detection
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Broad set of terms used to decide whether a page link looks like a job posting.
# Intentionally wide — it's better to capture a false positive than miss a real role.
JOB_KEYWORDS = {
    "engineer", "analyst", "security", "developer", "researcher",
    "architect", "manager", "consultant", "specialist", "intelligence",
    "vulnerability", "detection", "incident", "forensic", "pentest",
    "red team", "blue team", "soc", "devops", "cloud",
}


def _looks_like_job_link(text, href):
    """Return True if the link text or URL contains any job-related keyword.

    Checks both the visible link text and the href so that links like
    '/careers/software-engineer-123' are caught even with generic anchor text.
    """
    combined = (text + " " + href).lower()
    return any(kw in combined for kw in JOB_KEYWORDS)


def scrape_company_pages(companies):
    """Scrape raw HTML career pages and extract likely job links.

    Args:
        companies: List of dicts with "name" and "url" keys (from config.py).
                   The URL should point directly to the careers/jobs listing page,
                   not the company homepage — reduces irrelevant link noise.

    Returns:
        List of job dicts with keys: title, company, location, source, url, posted_date.
        title is truncated to 200 chars (raw link text can be arbitrarily long).
        location defaults to "See posting" — not extractable from unstructured HTML.
        posted_date is always None for the same reason.
    """
    jobs = []
    for company in companies:
        name = company["name"]
        url = company["url"]

        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"  [company] Failed to fetch {name} ({url}): {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        found = 0
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or not _looks_like_job_link(text, href):
                continue

            # Resolve relative hrefs (e.g. /jobs/123) against the base URL
            full_url = href if href.startswith("http") else url.rstrip("/") + "/" + href.lstrip("/")

            jobs.append({
                "title": text[:200],
                "company": name,
                "location": "See posting",
                "source": "Company Page",
                "url": full_url,
                "posted_date": None,
            })
            found += 1

        print(f"  [company] {name} → {found} listing(s) found")

    return jobs
