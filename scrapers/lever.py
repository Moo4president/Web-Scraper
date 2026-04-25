"""
Lever ATS scraper.

Lever exposes a free, unauthenticated public JSON API for companies that use
it as their applicant tracking system. This scraper fetches all open postings
for each configured company and filters them by keyword against the job title.

API endpoint: https://api.lever.co/v0/postings/{slug}?mode=json
No authentication required. Returns a flat JSON array of postings.

NOTE: Few major US cybersecurity companies have been confirmed on Lever's
public API. LEVER_COMPANIES in config.py is intentionally empty until verified
slugs are found. To check if a company uses Lever:
  curl https://api.lever.co/v0/postings/<slug>?mode=json
A 200 response with JSON confirms it; a 404 means they don't use Lever publicly.
"""

import requests

BASE_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


def _matches_keywords(title, keywords):
    """Return True if any keyword appears (case-insensitive) in the job title."""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in keywords)


def scrape_lever(companies, keywords):
    """Fetch and filter job postings from Lever for a list of companies.

    Like Greenhouse, the API returns ALL open roles — keyword filtering is
    done client-side because Lever's public API has no search parameter.

    Args:
        companies: List of dicts with "name" and "slug" keys (from config.py).
        keywords:  List of strings to match against job titles.

    Returns:
        List of job dicts with keys: title, company, location, source, url, posted_date.
        posted_date is always None — not available in the public Lever API response.
    """
    jobs = []
    for company in companies:
        name = company["name"]
        slug = company["slug"]
        url = BASE_URL.format(slug=slug)

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            listings = r.json()
        except requests.RequestException as e:
            # 404 typically means the company doesn't use Lever or their slug changed
            print(f"  [lever] Failed to fetch {name}: {e}")
            continue
        except ValueError:
            # Guard against HTML error pages that return 200 but aren't JSON
            print(f"  [lever] Invalid JSON response from {name}")
            continue

        matched = 0
        for job in listings:
            title = job.get("text", "")
            if not _matches_keywords(title, keywords):
                continue

            # Location lives inside a nested 'categories' object in Lever's schema
            categories = job.get("categories", {})
            location = categories.get("location", "N/A") or "N/A"

            job_url = job.get("hostedUrl", "")
            if not job_url:
                # Skip listings with no application link
                continue

            jobs.append({
                "title": title,
                "company": name,
                "location": location,
                "source": "Lever",
                "url": job_url,
                "posted_date": None,
            })
            matched += 1

        print(f"  [lever] {name} → {matched}/{len(listings)} listings matched")

    return jobs
