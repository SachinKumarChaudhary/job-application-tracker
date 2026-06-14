# Job Application Auto-Tracker — Complete Project Reference

> **Live demo:** https://SachinKumarChaudhary.pythonanywhere.com/
> **Source:** https://github.com/SachinKumarChaudhary/job-application-tracker
> **Telegram bot:** @GotJobAlert_bot

---

## Table of Contents

1. [What It Does](#1-what-it-does)
2. [Architecture Overview](#2-architecture-overview)
3. [File-by-File Breakdown](#3-file-by-file-breakdown)
4. [Core Data Flow](#4-core-data-flow)
5. [Configuration Reference](#5-configuration-reference)
6. [API Endpoints](#6-api-endpoints)
7. [Parser Deep Dive](#7-parser-deep-dive)
8. [Notification Channels](#8-notification-channels)
9. [OAuth Flow](#9-oauth-flow)
10. [Deployment](#10-deployment)
11. [Testing](#11-testing)
12. [Known Issues & Roadmap](#12-known-issues--roadmap)
13. [Session History Summary](#13-session-history-summary)

---

## 1. What It Does

A multi-user web app that:

1. **Polls Gmail** every 15 minutes for job application emails
2. **Parses them** using Gemini/Groq/NVIDIA AI (primary) or regex (fallback) — extracts company name, job role, date, email type (8 stages), location, salary, next step, and summary
3. **Logs to Google Sheets** — one spreadsheet per user, auto-created with 13 typed columns, in-place updates when status progresses
4. **Sends alerts** to Telegram, Slack, Discord, WhatsApp (3 providers), or Pushover
5. **Runs 24/7** on PythonAnywhere free tier, kept alive by cron-job.org

**Target users:** Anyone applying to 50+ jobs who wants automatic tracking without manual data entry.

**Key differentiator:** $0 infrastructure cost — free-tier everything (PythonAnywhere, Gemini/Groq/NVIDIA API, Google Sheets, Telegram Bot API, cron-job.org).

---

## 2. Architecture Overview

```
                    ┌──────────────────────┐
                    │    cron-job.org      │
                    │   (pings every 15m)  │
                    └──────────┬───────────┘
                               │ GET /cron/<secret>
                               ▼
┌─────────────┐     ┌──────────────────┐     ┌───────────────────┐
│   Browser   │────▶│   Flask App      │────▶│   Gmail API       │
│  (user UI)  │     │   webui.py       │     │   (per-user OAuth)│
└─────────────┘     └────────┬─────────┘     └─────────┬─────────┘
                             │                         │
                             ▼                         ▼
                    ┌──────────────────┐     ┌───────────────────┐
                    │   AI Provider    │     │   Regex Parser    │
                    │ (Gemini/Groq/NV) │────▶│  (fallback parse) │
                    └────────┬─────────┘     └─────────┬─────────┘
                             │                         │
                             ▼                         ▼
                    ┌──────────────────┐     ┌───────────────────┐
                    │ Google Sheets    │     │   Notifier        │
                    │ (per-user, auto) │     │ 7 channels        │
                    └──────────────────┘     └───────────────────┘
```

### Data Flow (one poll cycle)

```
Gmail API ──[fetch 20 matching emails]──► Poller
    │
    ▼
quick_is_job_email() ──[regex filter]──► skip if non-job (no AI wasted)
    │
    ▼
Parser ──[try AI first]──► Gemini/Groq/NVIDIA ──[JSON]──► Parser
    │                                │
    │         [if AI fails/skipped]  │
    └─────[regex fallback]───────────┘
    │
    ▼
In-place check ──[company+role in sheet?]──► UPDATE row if new status > old
    │                                                (progress never regression)
    └── if no match ──► APPEND new row A-M
    │
    ▼
Notifier ──[send alert]──► Telegram / Slack / Discord / WhatsApp / Pushover
    │
    ▼
Mark as Read ──[remove UNREAD label]──► Gmail
```

---

## 3. File-by-File Breakdown

### Entry Points

| File | Lines | Role |
|------|-------|------|
| `webui.py` | 1250 | Flask app — routes, OAuth, scheduler, per-user polling, in-place updates, sheet formatting, email normalization |
| `wsgi.py` | 11 | PythonAnywhere WSGI bridge |

### Source Modules (`src/`)

| File | Lines | Role |
|------|-------|------|
| `email_utils.py` | 40 | Gmail header extraction, MIME body decode, Message-ID lookup |
| `config.py` | 60 | Env var loading, logging setup, constants, validation |
| `parser.py` | 283 | Email parsing — company/role extraction, 8-stage type classifier, 60+ company aliases, two-pass AI filter, date parsing |
| `ai.py` | 134 | AI provider abstraction — Gemini, Groq, NVIDIA API calls with JSON response parsing |
| `models.py` | 88 | Pydantic `JobApplication` model — validation, 13-column sheet rows, alert text with emoji |
| `notifier.py` | 244 | 8-channel notification dispatch (Telegram, Slack, Discord, WhatsApp x3, Pushover, ntfy) |

### Web Layer

| File | Lines | Role |
|------|-------|------|
| `templates/index.html` | 599 | Material Design 3 — dark/light theme, 4 tab nav, responsive mobile-first, HTMX |
| `templates/_dashboard.html` | 248 | Dashboard partial — action buttons, stat cards, entries table with pipeline progress bars, per-channel alert cards |

### Tests

| File | Tests | What It Covers |
|------|-------|----------------|
| `test_parser.py` | 9 | Company extraction, date parsing, full email parsing, domain fallback, message IDs, body date |
| `test_models.py` | 3 | Model validation, sheet row format, alert text format |

### Config & Build

| File | Role |
|------|------|
| `.env.example` | All config vars with documentation |
| `requirements.txt` | 9 dependencies |
| `setup.sh` | One-command environment setup |
| `.gitignore` | 21 patterns (secrets, caches, IDE, PDFs, session logs) |
| `generate_docs.py` | Markdown→PDF converter (WeasyPrint) |
| `gmail_filter.xml` | Gmail filter rules for auto-labeling application emails |
| `n8n-workflow.json` | Archived n8n workflow design (8 nodes, preserved for reference) |

### Documentation

| File | Size | Purpose |
|------|------|---------|
| `README.md` | ~9K | Quickstart, custom SVGs, architecture, config, deployment |
| `PROJECT_COMPLETE.md` | 40K+ | Single-file A-Z reference — history, architecture, every file, endpoints, parser, OAuth, config, deployment, testing, known issues, appendices |
| `PROJECT_REFERENCE.md` | — | This file — concise technical reference |
| `docs/n8n-workflow.md` | 5.5K | n8n workflow breakdown, code, why rejected |
| `docs/DEVICE_ARCHITECTURE.md` | 3K | Device hardware, OS, env spec |
| `GITHUB.md` | 1K | Public Git info for contributors |

### Visual Assets

| File | Size | Purpose |
|------|------|---------|
| `assets/hero-banner.svg` | 3K | Dark gradient banner — title, tagline, stat badges |
| `assets/badges.svg` | 4K | Custom dark-themed SVG badges (license, python, tests, hosting, AI, cost) |
| `assets/architecture.svg` | 8K | Full system architecture — 7-color scheme, pill labels, shadows |
| `assets/how-it-works.svg` | 4K | Visual flow: User → OAuth → Gmail → Parser → Sheets + Alerts |

---

## 4. Core Data Flow

### webui.py — The Orchestrator

The Flask app runs two parallel systems:

**System 1: User-facing web UI**
- `/` — Dashboard with live stats, recent entries, activity log
- `/auth` `/callback` — Google OAuth flow
- `/save-prefs` — Notification channel selection (7 channels)
- `/trigger` — Manual poll trigger
- `/send-test-email` — Sends a self-addressed test application email
- `/test-notification` — Tests the configured notification channel
- `/upload-credentials` — Admin uploads Google Cloud OAuth JSON
- `/export-xlsx` — Downloads sheet as formatted Excel file
- `/format-sheet` — Beautifies Google Sheet
- `/dedup-sheet` — Removes duplicate rows by Message-ID

**System 2: Background scheduler**
- `scheduler_loop()` runs in a daemon thread, polls every `POLL_INTERVAL_MINUTES`
- Iterates over all users with valid tokens and calls `run_poll(email)`
- `/cron/<secret>` — External trigger endpoint for cron-job.org (polls ALL users)

### run_poll(email) — One User's Poll Cycle

```python
def run_poll(email):
    1. Get valid OAuth credentials (refresh if expired)
    2. Find or create Google Sheet for this user
    3. Build Gmail service + Sheets service
    4. Search Gmail: q='(subject:"application received" OR ...) is:unread'
    5. Read existing sheet rows → build company+role→row_number map
    6. For each matching message:
       a. Get full message (format="full")
       b. Extract Message-ID, check against known_ids (column F)
       c. Call parse_email(full) from parser.py (two-pass: quick filter → AI → regex)
       d. Check company+role match in existing rows
          - If match: UPDATE row if new status priority > old (never regress)
          - If no match: APPEND new row
       e. Notify user via configured channel
       f. Mark as read (remove UNREAD label)
    7. Update last_run/last_count/last_error
```

### In-Place Update Logic

```python
STATUS_PRIORITY = {
    "rejection": 1, "other": 2, "application_received": 3,
    "assessment": 4, "phone_screen": 5, "interview_invitation": 6,
    "technical_interview": 7, "offer_letter": 8,
}

# When a new email matches existing company+role:
if new_priority > old_priority:
    UPDATE row  # progress — never regress
else:
    SKIP        # no regression allowed
```

### Per-User Token Isolation

```
credentials/token_<base64url(email)>.json
```

Example: `credentials/token_c2FjaGluQGV4YW1wbGUuY29t.json`

Token auto-refresh and scope mismatch detection are handled in `get_creds()`.

### Email Normalization

Gmail ignores dots and case in usernames. `normalize_email()` lowercases and strips dots before `@gmail.com` to prevent duplicate user entries and token file mismatches. Applied in `get_user_email()`, `get_user_prefs()`, `set_user_pref()`, and `get_creds()`.

---

## 5. Configuration Reference

All config is loaded from `.env` by `src/config.py`.

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `GMAIL_QUERY` | `subject:"application received" OR ...` | Gmail search query |
| `POLL_INTERVAL_MINUTES` | `15` | Poll cycle interval |
| `SHEET_NAME` | `Job Application Tracker` | Google Sheet name |
| `LOG_LEVEL` | `INFO` | Python logging level |

### Notifications

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `TELEGRAM_BOT_USERNAME` | ✅ | Bot username (users DM this to connect) |
| `PUSHOVER_TOKEN` | ❌ | Pushover app token for admin fallback |
| `PUSHOVER_USER` | ❌ | Pushover user key for admin fallback |
| `WHATSAPP_CLOUD_PHONE_NUMBER_ID` | ❌ | WhatsApp Cloud API phone number ID |
| `WHATSAPP_CLOUD_ACCESS_TOKEN` | ❌ | WhatsApp Cloud API access token |
| `TWILIO_ACCOUNT_SID` | ❌ | Twilio account SID for WhatsApp |
| `TWILIO_AUTH_TOKEN` | ❌ | Twilio auth token for WhatsApp |

### AI / LLM

| Variable | Default | Options |
|----------|---------|---------|
| `AI_PROVIDER` | `none` | `gemini`, `groq`, `nvidia`, `none` |
| `AI_MODEL` | `gemini-2.0-flash` | Model name for provider |
| `GEMINI_API_KEY` | — | Required if `AI_PROVIDER=gemini` |
| `GROQ_API_KEY` | — | Required if `AI_PROVIDER=groq` |
| `NVIDIA_API_KEY` | — | Required if `AI_PROVIDER=nvidia` |

### Security

| Variable | Required | Description |
|----------|----------|-------------|
| `CRON_SECRET` | ✅ | Secret path segment in `/cron/<secret>` |
| `FLASK_ENV` | No | Set to `production` on PythonAnywhere |

---

## 6. API Endpoints

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard (authed) or landing page |
| GET | `/auth` | Initiate Google OAuth flow |
| GET | `/callback` | OAuth callback — creates token, redirects to `/` |
| GET | `/logout` | Clear session |
| POST | `/upload-credentials` | Admin uploads `credentials.json` |

### Preferences

| Method | Path | Description |
|--------|------|-------------|
| POST | `/save-prefs` | Save notification channel + channel-specific config |
| GET | `/change-channel` | Reset channel to "none" |

### Actions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/trigger` | Run poll for authenticated user |
| GET | `/send-test-email` | Send self-addressed test application email |
| POST | `/test-notification` | Send test notification on configured channel |
| POST | `/save-whatsapp-apikey` | Save WhatsApp API key after activation |
| POST | `/save-pushover-key` | Save Pushover user key |
| GET | `/format-sheet` | Beautify Google Sheet (header style, banding, borders, auto-resize) |
| GET | `/dedup-sheet` | Remove duplicate rows by Message-ID |
| GET | `/export-xlsx` | Download sheet as formatted Excel file |
| GET | `/download-contacts` | Download CallMeBot contact VCF |

### Status

| Method | Path | Description |
|--------|------|-------------|
| GET | `/status` | JSON: authed state, prefs, last run, last error |
| GET | `/logs` | JSON: last 50 log lines |
| GET | `/automation-status` | JSON: scheduler alive, poll interval |
| GET | `/verify-telegram` | Check if user DM'd the bot |
| GET | `/cron/<secret>` | External trigger — polls all users (cron-job.org) |

---

## 7. Parser Deep Dive

### Two-Pass AI Pipeline (`src/parser.py` + `src/ai.py`)

Before calling the AI, `quick_is_job_email()` runs a fast regex filter:

```python
keywords = (
    r"offer\s*letter|interview|application|hiring|recruit"
    r"|job\s*alert|opportunity|position|role\s+at"
    r"|assessment|coding\s*test|hackerrank|walk[- ]?in|off[- ]?campus"
    r"|graduate\s+trainee|fresher|engineer\s+trainee"
)
```

Non-job emails skip the API call entirely — saves credits and speeds up processing.

### AI Path

When `AI_PROVIDER` is set, the AI receives this prompt:

```
You are an email parser for a job application tracker.
Extract the following fields from the email and return ONLY valid JSON:

{
  "company_name": "...",
  "job_role": "...",
  "date": "YYYY-MM-DD or null",
  "email_type": "offer_letter|technical_interview|interview_invitation|phone_screen|assessment|application_received|rejection|other",
  "location": "city, state or 'Remote'",
  "salary": "e.g. '₹50,000/mo', '$120k/yr'",
  "summary": "2-3 sentence summary with key details",
  "next_step": "interview|offer|follow_up|waiting|rejected|none"
}
```

The response is parsed with `_clean_json()` which strips markdown code fences and extracts `{...}`.

**Supported AI providers:**

| Provider | API Endpoint | Free Tier |
|----------|-------------|-----------|
| Gemini | `generativelanguage.googleapis.com` | 60 req/min free |
| Groq | `api.groq.com/openai/v1` | 30 req/min free (rate-limited) |
| NVIDIA | `integrate.api.nvidia.com/v1` | Free tier available |

### Regex Fallback Path

**Company name extraction — four-layer strategy:**

1. **Domain extraction** (always): `re.search(r"@([\w-]+)\.", sender)` → check `COMPANY_ALIASES` (60+ mappings) → `.title()`
2. **Known company patterns** (subject + body): 60+ Indian + global companies in regex alternation
3. **Generic "at/for/with" patterns**: `r"(?:at|for|with)\s+(.+?)(?:\s+(?:is|we|the|position|role)|$)"`
4. **Last resort**: falls back to domain-based name

**Company aliases (60+ mappings):**

```python
COMPANY_ALIASES = {
    "tcs": "TCS", "infosys": "Infosys", "google": "Google",
    "microsoft": "Microsoft", "goldmansachs": "Goldman Sachs",
    "byjus": "BYJU'S", "flipkart": "Flipkart",
    # ... 60+ total
}
```

**Role extraction — multi-pattern matching:**

1. Indian roles: `Graduate Trainee`, `GET`, `Fresher`, `Associate Software`, `Junior Developer`
2. Keyword combo: `Frontend|Backend|Full-Stack|DevOps` + `Engineer|Developer|Intern`
3. Known prefixes: `Software|Data|ML|QA|iOS|Android` + `Engineer|Scientist|Architect`
4. Extra patterns: `Offer Letter | <role>`, `Application received: <role>`
5. Fallback: `position|role|job title: <role>`, `for the|as a <role>`
6. Last resort: `"Unknown Position"`

**Email type classification — 8 pipeline stages:**

| Type | Priority | Keywords |
|------|----------|----------|
| `rejection` | 1 | `regret to inform`, `unfortunately`, `not moving forward`, `rejected` |
| `other` | 2 | Everything else |
| `application_received` | 3 | `application received`, `thank you for applying`, `we received` |
| `assessment` | 4 | `coding test`, `assessment`, `hackerrank`, `hackerearth` |
| `phone_screen` | 5 | `phone screen`, `video screen`, `introductory call`, `quick chat` |
| `interview_invitation` | 6 | `interview`, `invitation to`, `schedule an interview`, `shortlisted` |
| `technical_interview` | 7 | `technical interview`, `coding round`, `system design`, `pair programming` |
| `offer_letter` | 8 | `offer letter`, `offer of`, `internship offer`, `you are hired` |

**Date parsing — tries three formats:**

| Format | Pattern | Example |
|--------|---------|---------|
| ISO | `YYYY-MM-DD` | `2025-06-08` |
| US | `MM/DD/YYYY` | `06/08/2025` |
| Long | `Month DD, YYYY` | `June 8, 2025` |

If AI provides a date, it's used first. If regex finds one, it's used second. Otherwise, the email's `internalDate` timestamp is used.

### Parser Flow (`parse_email()`)

```
parse_email(msg)
    ├── extract subject, sender, body, message_id, internal_date
    ├── quick_is_job_email()  ← Two-pass filter before AI
    │   └── if false: skip AI call, fall through to regex
    ├── if job-related: try parse_email_with_ai()
    │   └── if AI returns valid dict:
    │       ├── company = AI result or regex fallback
    │       ├── role = AI result or regex fallback
    │       ├── email_type = AI result
    │       ├── location/salary/summary/next_step = AI result
    │       ├── date = AI date or regex date or internal_date
    │       └── parser = provider name ("Gemini"/"Groq"/"NVIDIA")
    └── else (AI not configured or failed or non-job email):
        ├── company = extract_company()  ← uses COMPANY_ALIASES
        ├── role = extract_role()
        ├── email_type = classify_email_type()  ← 8 stages
        ├── summary = ""
        ├── date = regex date or internal_date
        └── parser = "Regex"
    └── return JobApplication(...)
```

---

## 8. Notification Channels

### Telegram (recommended — most reliable)

**User setup:**
1. Select Telegram in preferences
2. Enter their @username
3. Open Telegram, search for `@GotJobAlert_bot`, send `/start`
4. App auto-detects the DM within 60 seconds (polls `/verify-telegram` every 3s)

**Technical:**
- Bot token stored in `.env` — shared across all users
- Chat ID resolved via `getUpdates` API
- Messages sent as Markdown via `sendMessage`

### Discord (webhook-based, no setup friction)

**User setup:**
1. Select Discord in preferences
2. Open Discord → Server Settings → Integrations → Create Webhook
3. Name it "Offer Tracker", pick a channel, copy webhook URL
4. Paste URL in preferences → Save

**Technical:**
- Uses Discord webhook URL per user (no bot token needed)
- URL format: `https://discord.com/api/webhooks/...`
- Messages sent as JSON `{"content": "..."}` via POST
- Dashboard shows webhook status, test/change buttons

### Slack

**User setup:**
1. Create Slack app at `api.slack.com/apps`
2. Enable Incoming Webhooks
3. Add webhook to a channel
4. Paste webhook URL in preferences

**Technical:**
- Uses webhook URL per user (no bot token needed)
- Messages sent as JSON `{"text": "..."}` via POST
- Known issue: "No channels" picker — needs workspace refresh

### WhatsApp (CallMeBot — DEPRECATED)

Gateway numbers are unreliable and get banned. Original setup sent "I allow callmebot" to `+34 644 59 90 43` to receive an API key, then stored in prefs.

### WhatsApp Cloud API

Admin sets `WHATSAPP_CLOUD_PHONE_NUMBER_ID` and `WHATSAPP_CLOUD_ACCESS_TOKEN` in `.env`. User enters their phone number in prefs. Messages sent via Meta's Graph API.

### Twilio WhatsApp

Admin sets `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` in `.env`. User enters their phone number. Messages sent via Twilio's API.

### Pushover

Admin sets `PUSHOVER_TOKEN` in `.env`. User enters their user key in prefs. Can also be used as app-level fallback.

---

## 9. OAuth Flow

### Google Cloud Setup (one-time, by admin)

1. Create project at `console.cloud.google.com`
2. Enable Gmail API + Google Sheets API
3. Create OAuth 2.0 credentials → Web application
4. Add redirect URI: `https://your-app.com/callback`
5. Download `credentials.json` → upload via the web UI

### Scopes Requested

```python
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.modify",   # read + mark as read
    "https://www.googleapis.com/auth/gmail.send",     # send test emails
    "https://www.googleapis.com/auth/spreadsheets",    # create + write sheets
]
```

### Per-User Token Storage

- Token file: `credentials/token_<base64(email)>.json`
- Auto-refresh: `creds.refresh(Request())` if expired
- Scope mismatch detection: if scope changes, token is deleted and user re-auths
- Email normalization: Gmail dots/case normalized to prevent duplicate tokens

---

## 10. Deployment

### PythonAnywhere (free tier)

```
1. Upload code via git clone or web console
2. Create virtualenv: mkvirtualenv offertracker --python=python3.10
3. pip install -r requirements.txt
4. Set up WSGI file → webui.py → app
5. Set env vars in PythonAnywhere Secrets tab
6. Upload credentials.json via web UI
7. Reload web app
```

**WSGI file (`wsgi.py`):**
```python
path = '/home/SachinKumarChaudhary/Gotjobalert'
sys.path.insert(0, path)
os.chdir(path)
os.environ['FLASK_ENV'] = 'production'
from webui import app as application
```

### cron-job.org (free 24/7 keep-alive)

```
URL: https://your-app.pythonanywhere.com/cron/gotjobalert_auto_2026
Schedule: Every 15 minutes
```

The `/cron/<secret>` endpoint polls all users with valid tokens in a single request. This keeps the app alive (PythonAnywhere free tier sleeps after inactivity) and runs regular polls.

### Local Development

```bash
git clone https://github.com/SachinKumarChaudhary/job-application-tracker
cd job-application-tracker
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
python webui.py   # Runs at http://localhost:8080
```

---

## 11. Testing

### Running Tests

```bash
cd /path/to/project
pytest -v
```

### Current Coverage

| Test File | Tests | Lines | What It Covers |
|-----------|-------|-------|----------------|
| `test_parser.py` | 9 | 108 | Company extraction, date parsing, full email parsing, domain fallback, message IDs, body date |
| `test_models.py` | 3 | 51 | Model creation, sheet row format, alert text format with emoji |

### Test Patterns

```python
# Mock Gmail message
def make_mock_msg(subject, sender, body, date_str=None):
    return {
        "id": "test123",
        "internalDate": "1717800000000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": sender},
                {"name": "Message-ID", "value": "<test123@mail>"},
            ],
            "mimeType": "text/plain",
            "body": {
                "data": base64.urlsafe_b64encode(body.encode()).decode()
            },
        },
    }
```

---

## 12. Known Issues & Roadmap

### Recently Fixed

| Issue | Fix |
|-------|-----|
| Briefcase icon didn't render | Replaced `briefcase` ligature with `description` |
| OAuth callback URL caching | `Cache-Control: no-store` on all responses |
| Missing `is:unread` in Gmail query | Now uses `(query) is:unread` in `run_poll()` |
| Hardcoded Gmail query | `webui.py:324` now uses `GMAIL_QUERY` env var |

### Bugs

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| WhatsApp CallMeBot unreliable | `notifier.py:65` | Low | Gateway numbers often don't respond with API key |
| In-memory state | `webui.py:48-52` | Low | `last_run`, `last_count`, `log_buffer` lost on restart |

### Technical Debt

| Issue | Location | Description |
|-------|----------|-------------|
| Single-threaded scheduler | `webui.py:424` | One slow user poll delays others |
| Tokens on filesystem | `webui.py:121-123` | Not suitable for multi-instance deployment |
| No rate limiting on `/cron/` | `webui.py:726-740` | Anyone with the secret can trigger polls |
| No token revocation detection | `webui.py:126-149` | Silent retry until token expires |

### Roadmap

| Feature | Priority | Status | Description |
|---------|----------|--------|-------------|
| Dashboard charts | Medium | ❌ | Application trends, response rates, company breakdown |
| Multi-language | Low | ❌ | Parse Hindi, Spanish emails via AI |
| Persistent state | Medium | ❌ | Move from in-memory dicts to SQLite |
| Async worker queue | Low | ❌ | Celery or Redis queue instead of single-threaded scheduler |

---

## 13. Session History Summary

This project was built across 13 AI coding sessions:

| Session | Date | Key Events |
|---------|------|------------|
| 1 | Jun 8 | Initial Flask app — Gmail API, regex parser, Google Sheets, Telegram |
| 2 | Jun 8-9 | Multi-user OAuth, per-user token isolation, prefs, notification UI |
| 3 | Jun 9 | Telegram auto-verify, test notification, UI polish |
| 4 | Jun 9-10 | n8n workflow design — 8 nodes, hit Android tracing-stop bug |
| 5 | Jun 10 | n8n debugging — CONT daemon fix, partial success |
| 6 | Jun 10-11 | Manus AI — hit 300 credit/day limit |
| 7 | Jun 11 | Return to Flask — merged n8n AI code, PythonAnywhere deploy, WhatsApp/Slack |
| 8 | Jun 11 | 11 tests passing, error handling polish |
| 9 | Jun 11 | Documentation — README, CASE_STUDY.pdf, GitHub push |
| 10 | Jun 11-12 | AI migration Gemini→NVIDIA, sheet formatting, 13-col schema, OAuth scope fix |
| 11 | Jun 13 | Frontend polish — Material Symbols, theme toggle, "none" channel card, email normalization, Cache-Control |
| 12 | Jun 12 | Visual SVGs — hero banner, badges, architecture diagram, how-it-works flow, designer skill |
| 13 | Jun 12 | Discord, in-place sheet updates, two-pass AI, 60+ company aliases, 8-stage pipeline, WhatsApp deprecated |

### Why Custom Flask Won

- **n8n:** Android Termux proot kills Node.js threads (tracing-stop state)
- **Manus AI:** 300 credits/day insufficient for 672 polls/day
- **Custom Flask + cron-job.org:** Full control, $0 infra, multi-user, all notification channels

---

## Appendix D: Architectural Patterns

The codebase uses several established patterns:

| Pattern | Implementation | Files |
|---------|--------------|-------|
| **Pipeline** | Sequential: poll → parse → dedup → sheets → notify | `webui.py:run_poll()` |
| **Strategy** | AI providers (Gemini/Groq/NVIDIA) with unified interface + regex fallback | `src/ai.py:parse_email_with_ai()` |
| **Observer/Polling** | Scheduler polls Gmail at intervals; Telegram verification polls `getUpdates` | `webui.py:scheduler_loop()`, JS auto-poll |
| **Factory** | `_call_gemini`, `_call_groq`, `_call_nvidia` are factory-like dispatch | `src/ai.py` |
| **Background Worker** | Daemon thread runs `scheduler_loop` alongside Flask | `webui.py:905` |

## Appendix E: Error Handling & Resilience

| Layer | Error Source | Handling |
|-------|-------------|----------|
| Config | Missing `credentials.json` | `validate()` returns False, cycle skipped |
| Gmail | Network failure, API quota | Caught → returns `[]`, logged |
| Gmail | Mark-as-read failure | Logged as warning, non-fatal |
| Parser | Unparseable email | Returns `None`, message marked read |
| AI | Network/API/JSON decode failure | Returns `None`, falls through to regex |
| Sheets | Sheet not found | Auto-created in `ensure_sheet()` |
| Sheets | Append failure | Caught in process loop, logged as error |
| Duplicate | Refresh failure | Logged as warning, cache remains empty |
| Notifications | API failures | All caught individually, logged as warnings, non-blocking |
| OAuth | Token refresh failure | Returns `None`, user must re-auth |
| Scheduler | General exception | Caught, logged with traceback, 60s wait, retry |

## Appendix F: Security Considerations

| Issue | Severity | Notes |
|-------|----------|-------|
| OAuth client_secret in plaintext | Critical | `credentials/credentials.json` — gitignored but present in working tree |
| No token rotation | Medium | Token files are long-lived; refresh tokens never revoked |
| Session secret per-process | Low | `app.secret_key = os.urandom(24).hex()` — resets on restart |
| No HTTPS enforcement in app | Medium | `redirect_uri()` trusts `X-Forwarded-Proto` header |
| No rate limiting | Medium | `/trigger`, `/cron/secret` have no rate limits |
| No CSRF protection | Low | Flask forms lack CSRF tokens |

## Appendix G: Test Coverage Gaps

| Component | Tests | Missing |
|-----------|-------|---------|
| `src/notifier.py` | 0 | No HTTP mock tests for 8 channels |
| `src/ai.py` | 0 | No provider mock tests (Gemini/Groq/NVIDIA) |
| `src/email_utils.py` | 0 | No header/body extraction tests |
| `webui.py` | 0 | No Flask client tests |

---

## Appendix H: Full Gmail Query

```
subject:"application received" OR
subject:"thank you for applying" OR
subject:"application confirmation" OR
subject:"offer letter" OR
subject:"we received your application"
```

## Appendix I: Google Sheet Columns

| Column | Header | Source |
|--------|--------|--------|
| A | Company Name | Parser (AI or regex) |
| B | Job Role | Parser (AI or regex) |
| C | Application Date | Parser or email internalDate |
| D | Email Subject | Gmail header |
| E | Sender Email | Gmail header |
| F | Message ID | Gmail header (dedup key) |
| G | Alert Sent | Always "Yes" |
| H | Email Type | Classifier (8 stages) |
| I | Summary | AI generated (2-3 sentence description) |
| J | Location | AI extracted |
| K | Salary | AI extracted |
| L | Next Step | AI classified |
| M | Parser | Provider name ("NVIDIA"/"Gemini"/"Groq"/"Regex") |

## Appendix J: Dependencies

```
flask>=3.0
google-api-python-client>=2.0
google-auth-oauthlib>=1.0
google-auth-httplib2>=0.1
gspread>=6.0
pydantic>=2.0
python-dotenv>=1.0
requests>=2.28
openpyxl>=3.0
pytest
```

## Appendix K: Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Flask over FastAPI** | Simpler WSGI deployment on PythonAnywhere; no async complexity |
| **pydantic for models** | Built-in validation, serialization, and type hints; lightweight |
| **gspread over raw Sheets API** | Higher-level API (auto-find sheet, append rows, col values); fewer lines |
| **Per-user tokens (not single account)** | Each user connects their own Gmail; no central account needed |
| **NVIDIA over Gemini** | Gemini hit 429 rate limits; NVIDIA works without rate limiting |
| **AI primary + regex fallback** | AI more accurate but regex works when API is down |
| **Parser stores provider name** | Column M stores provider name — enables auditing |
| **cron-job.org over in-app scheduler** | PythonAnywhere free tier sleeps; external ping wakes it |
| **Single HTML file (no JS framework)** | Zero build step; deployable as-is; works without npm |
| **Base64-encoded token filenames** | Safe for filesystem (no @ or / in filenames); reversible for debugging |
| **In-place updates over always-append** | Same application emails no longer create duplicate rows; priority system prevents regression |
| **Two-pass AI pipeline** | Quick regex filter before API call saves credits on non-job emails |
| **COMPANY_ALIASES for domain normalization** | Maps ATS/company domains to canonical names instead of raw title-case |
| **8-stage pipeline instead of 5** | Separate phone_screen, assessment, and technical_interview stages for granular tracking |
| **Email normalization** | Gmail ignores dots and case — normalize to prevent duplicate user entries |
| **Cache-Control: no-store** | Prevents browser caching OAuth callback URL — eliminates spurious "Session expired" errors |
