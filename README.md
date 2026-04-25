# 🔍 CyberJob Scraper

A Python-based job scraper that monitors cybersecurity job postings from Greenhouse, Lever, Workday, and company career pages.

It stores new listings in a PostgreSQL database and prints a daily digest to the CLI.

Built as a practical automation project to mirror real-world vulnerability intelligence pipelines (collect → parse → store → alert).

---

## 📸 Demo

```
[2026-04-25] 3 new job(s) found:

  [NEW] Vulnerability Management Engineer @ Cloudflare
        Location : Austin, TX
        Source   : Greenhouse
        Posted   : None
        URL      : https://boards.greenhouse.io/cloudflare/jobs/7579269

  [NEW] Sr. Engineer - Vulnerability Detection @ CrowdStrike
        Location : N/A
        Source   : Workday
        Posted   : None
        URL      : https://crowdstrike.wd5.myworkdayjobs.com/en-US/crowdstrikecareers/job/...

  [NEW] Senior Threat Intelligence Engineer @ Cloudflare
        Location : Austin, TX
        Source   : Greenhouse
        Posted   : None
        URL      : https://boards.greenhouse.io/cloudflare/jobs/7558153
```

---

## 🚀 Features

- Scrapes **Greenhouse** and **Lever** job boards via their public JSON APIs
- Scrapes **Workday** career pages using a headless Playwright browser (JS-rendered)
- Scrapes **company career pages** directly as a fallback (configurable list)
- Filters all results by configurable **keywords** (e.g. "security engineer", "SOC analyst")
- Stores all listings in **PostgreSQL** with deduplication
- Detects and flags **new postings** since the last run
- Clean **CLI digest** output on every run
- Easily extensible — add new sources by dropping in a new scraper module

---

## 🛠 Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core language |
| Requests | HTTP client (Greenhouse, Lever APIs) |
| Playwright | Headless browser for JS-rendered pages (Workday) |
| BeautifulSoup4 | HTML parsing (company career pages) |
| psycopg2 | PostgreSQL adapter |
| python-dotenv | Loads .env credentials automatically |
| PostgreSQL | Job listing storage |

---

## 📁 Project Structure

```
Web-Scraper-main/
├── scrapers/
│   ├── __init__.py
│   ├── greenhouse.py      # Greenhouse public JSON API
│   ├── lever.py           # Lever public JSON API
│   ├── workday.py         # Workday via Playwright headless browser
│   └── company_pages.py   # Generic HTML career page scraper
├── db/
│   ├── __init__.py
│   ├── database.py        # DB connection, schema, queries
│   └── schema.sql         # Standalone DDL for manual DB setup
├── config.py              # Keywords and target companies per platform
├── main.py                # Entry point — run this
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/Moo4president/Web-Scraper.git
cd Web-Scraper
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install the Playwright browser (one-time)
```bash
playwright install chromium
```

### 5. Configure PostgreSQL
On macOS with Homebrew: Your superuser is your system username (not `postgres`):
```bash
brew services start postgresql@18
psql -U YOUR_USERNAME -d postgres -c "CREATE DATABASE cyberjobs;"
psql -U YOUR_USERNAME -d cyberjobs -f db/schema.sql
```

### 6. Set environment variables
Copy the example file and fill in your details:
```bash
cp .env.example .env
```

Edit `.env`:
```
DB_HOST=localhost
DB_NAME=cyberjobs
DB_USER=YOUR_USERNAME
DB_PASS=
```

On macOS with Homebrew PostgreSQL: `DB_PASS` can be left blank — no password is required for local connections.

### 7. Configure your search
Edit `config.py` to set your keywords and target companies per platform:
```python
KEYWORDS = ["vulnerability", "threat intelligence", "security engineer", "SOC analyst"]

GREENHOUSE_COMPANIES = [
    {"name": "Cloudflare",      "slug": "cloudflare"},
    {"name": "Recorded Future", "slug": "recordedfuture"},
    {"name": "Huntress",        "slug": "huntress"},
    {"name": "Wiz",             "slug": "wizinc"},
]

LEVER_COMPANIES = [
    # Add entries here as {"name": "Company", "slug": "slug"} when found
]

WORKDAY_COMPANIES = [
    {"name": "CrowdStrike", "url": "https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers"},
    {"name": "NVIDIA",      "url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"},
]
```

### 8. Run it
```bash
python main.py
```

---

## 🗄 Database Schema

```sql
CREATE TABLE jobs (
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
```

---

## 🔄 Automating Daily Runs (Optional)

Run automatically every morning with cron:
```bash
# Run at 8am daily
0 8 * * * /path/to/cyberjob-scraper/.venv/bin/python /path/to/cyberjob-scraper/main.py
```

---

## 📋 Next Steps for Improvement

- [ ] Slack/email notifications for new postings
- [ ] Filter by seniority level (junior, mid, senior)
- [ ] Resume keyword match scoring
- [ ] Support for LinkedIn job boards
- [ ] Apache Airflow DAG for orchestrated scheduling
