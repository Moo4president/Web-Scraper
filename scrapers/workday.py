"""
Workday career page scraper.

Unlike Greenhouse and Lever, Workday has no public JSON API. Job listings are
rendered by JavaScript in the browser — a plain HTTP request returns an empty
shell. This scraper uses Playwright to launch a real headless Chromium browser,
wait for the page to render, then extract jobs from the live DOM.

Trade-offs vs. API scrapers:
  - Slower: each keyword search opens a real browser page (~5-15s per request).
  - Fragile: relies on CSS selectors and Workday's data-automation-id attributes,
    which could change in a Workday platform update.
  - Realistic user-agent: spoofs a real Chrome browser to avoid bot detection.

Prerequisite: run `playwright install chromium` once after pip install.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import quote


def _matches_keywords(title, keywords):
    """Return True if any keyword appears (case-insensitive) in the job title."""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in keywords)


def _scrape_company(page, company, keywords):
    """Scrape one Workday company for all keywords using an already-open browser page.

    Reusing the same `page` object across keywords avoids the overhead of
    creating a new browser context per search. Keywords map to separate URL
    queries because Workday's search is server-filtered (unlike Greenhouse/Lever).

    Args:
        page:     Playwright Page object (shared across all companies in a run).
        company:  Dict with "name" and "url" keys (from config.py).
        keywords: List of search terms to query one at a time.

    Returns:
        List of job dicts (may contain duplicates across keywords — deduped by caller).
    """
    name = company["name"]
    base_url = company["url"]
    jobs = []

    for keyword in keywords:
        # quote() handles spaces and special characters (e.g. "SOC analyst" → "SOC%20analyst")
        search_url = f"{base_url}?q={quote(keyword)}"

        try:
            page.goto(search_url, timeout=30000)
            # data-automation-id='jobTitle' is a stable Workday attribute across versions
            page.wait_for_selector(
                "a[data-automation-id='jobTitle']",
                timeout=15000,
            )
        except PlaywrightTimeoutError:
            # Fires when no results render within 15s — likely no matches or bot detection
            print(f"  [workday] {name} — timed out waiting for listings (keyword: '{keyword}')")
            continue
        except Exception as e:
            print(f"  [workday] {name} — navigation error (keyword: '{keyword}'): {e}")
            continue

        # Each job is a list item; the css- prefix class is Workday's generated styling class
        cards = page.query_selector_all("li[class*='css-']")
        for card in cards:
            try:
                title_el = card.query_selector("a[data-automation-id='jobTitle']")
                if not title_el:
                    continue
                title = title_el.inner_text().strip()

                # Secondary keyword check: Workday's search is fuzzy, so filter tightly here
                if not _matches_keywords(title, keywords):
                    continue

                href = title_el.get_attribute("href") or ""
                # Workday hrefs are sometimes relative (/job/...) — prepend the domain if needed
                full_url = href if href.startswith("http") else f"https://{base_url.split('/')[2]}{href}"

                loc_el = card.query_selector("dd[data-automation-id='locations']")
                location = loc_el.inner_text().strip() if loc_el else "N/A"

                jobs.append({
                    "title": title,
                    "company": name,
                    "location": location,
                    "source": "Workday",
                    "url": full_url,
                    "posted_date": None,
                })
            except Exception as e:
                print(f"  [workday] {name} — failed to parse card: {e}")
                continue

    return jobs


def scrape_workday(companies, keywords):
    """Launch a headless browser and scrape all configured Workday companies.

    A single browser and page are reused across all companies to minimize
    startup overhead. A URL-based deduplication set prevents the same job
    from being inserted twice when it appears under multiple keyword searches.

    Args:
        companies: List of dicts with "name" and "url" keys (from config.py).
        keywords:  List of search terms passed to each company's search page.

    Returns:
        List of unique job dicts (deduped by URL within this run).
        The database layer (save_jobs) also dedupes across runs via ON CONFLICT.
    """
    all_jobs = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Spoof a real Chrome user-agent — Workday may block Python's default UA
        page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        })

        for company in companies:
            jobs = _scrape_company(page, company, keywords)
            # Dedupe within this run before appending — save_jobs handles cross-run deduplication
            unique = [j for j in jobs if j["url"] not in seen_urls]
            seen_urls.update(j["url"] for j in unique)
            all_jobs += unique
            print(f"  [workday] {company['name']} → {len(unique)} listings found")

        browser.close()

    return all_jobs
