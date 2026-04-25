"""
Central configuration for CyberJob Scraper.

Edit this file to control what gets scraped:
  - KEYWORDS     : Terms filtered against job titles (Greenhouse, Lever, Workday).
  - GREENHOUSE_COMPANIES : Companies using the Greenhouse ATS (free public JSON API).
  - LEVER_COMPANIES      : Companies using the Lever ATS (free public JSON API).
  - WORKDAY_COMPANIES    : Companies using Workday (requires Playwright browser rendering).
  - COMPANY_PAGES        : Fallback for companies not on any of the above platforms.

Finding slugs:
  - Greenhouse slug: visit boards.greenhouse.io/<slug> until you find the company.
  - Lever slug: visit jobs.lever.co/<slug> until you find the company.
  - Workday URL: visit the company careers page and look for *.myworkdayjobs.com in the URL.
"""

# Applied as a case-insensitive substring filter on job titles.
# Greenhouse and Lever return all open roles per company — keywords narrow results
# to security-relevant positions. Workday passes keywords as URL query params.
KEYWORDS = [
    "vulnerability",
    "threat intelligence",
    "security engineer",
    "SOC analyst",
    "application security",
]

# Each entry requires a "slug" — the subdomain used in the Greenhouse board URL.
# Example: {"name": "Cloudflare", "slug": "cloudflare"}
#          → https://boards-api.greenhouse.io/v1/boards/cloudflare/jobs
GREENHOUSE_COMPANIES = [
    {"name": "Cloudflare",      "slug": "cloudflare"},
    {"name": "Recorded Future", "slug": "recordedfuture"},
    {"name": "Huntress",        "slug": "huntress"},
    {"name": "Dragos",          "slug": "dragos"},
    {"name": "Orca Security",   "slug": "orcasecurity"},
    {"name": "Wiz",             "slug": "wizinc"},
]

# NOTE: Few major US cybersecurity companies have been confirmed on Lever's public API.
# Add entries here as {"name": "Company", "slug": "slug"} when found.
# Verify a slug exists before adding: curl https://api.lever.co/v0/postings/<slug>?mode=json
LEVER_COMPANIES = [
]

# Each entry requires the full Workday career portal URL (*.myworkdayjobs.com/<board>).
# Not all companies use the public myworkdayjobs.com URL — some have custom career sites
# that look like Workday but won't work here (e.g. Palo Alto Networks).
WORKDAY_COMPANIES = [
    {"name": "CrowdStrike", "url": "https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers"},
    {"name": "NVIDIA",      "url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"},
]

# Fallback scraper for companies not on Greenhouse, Lever, or Workday.
# Uses broad keyword matching on page links — less precise than the API scrapers.
# Format: {"name": "Company", "url": "https://company.com/careers"}
COMPANY_PAGES = [
]
