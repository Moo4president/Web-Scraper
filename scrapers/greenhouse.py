"""
Greenhouse ATS scraper.

Greenhouse exposes a free, unauthenticated public JSON API for companies that
use it as their applicant tracking system. This scraper fetches all open roles
for each configured company and filters them by keyword against the job title.

API endpoint: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
No authentication or rate limiting — safe to call on every run.
"""

import requests

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


def _matches_keywords(title, keywords):
    """Return True if any keyword appears (case-insensitive) in the job title."""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in keywords)


def scrape_greenhouse(companies, keywords):
    """Fetch and filter job listings from Greenhouse for a list of companies.

    Because the API returns ALL open roles, keyword filtering happens client-side
    here rather than server-side — Greenhouse's API offers no search parameter.

    Args:
        companies: List of dicts with "name" and "slug" keys (from config.py).
        keywords:  List of strings to match against job titles.

    Returns:
        List of job dicts with keys: title, company, location, source, url, posted_date.
        posted_date is always None — Greenhouse does not expose it in this endpoint.
    """
    jobs = []
    for company in companies:
        name = company["name"]
        slug = company["slug"]
        url = BASE_URL.format(slug=slug)

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as e:
            # 404 usually means the company's Greenhouse slug has changed or they left Greenhouse
            print(f"  [greenhouse] Failed to fetch {name}: {e}")
            continue
        except ValueError:
            # Greenhouse occasionally returns HTML error pages instead of JSON
            print(f"  [greenhouse] Invalid JSON response from {name}")
            continue

        listings = data.get("jobs", [])
        matched = 0
        for job in listings:
            title = job.get("title", "")
            if not _matches_keywords(title, keywords):
                continue

            # 'offices' is a list; take the first office name if present
            location_list = job.get("offices", [])
            location = location_list[0].get("name", "N/A") if location_list else "N/A"

            job_url = job.get("absolute_url", "")
            if not job_url:
                # Skip malformed listings with no application link
                continue

            jobs.append({
                "title": title,
                "company": name,
                "location": location,
                "source": "Greenhouse",
                "url": job_url,
                "posted_date": None,
            })
            matched += 1

        print(f"  [greenhouse] {name} → {matched}/{len(listings)} listings matched")

    return jobs
