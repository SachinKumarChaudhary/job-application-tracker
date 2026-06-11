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
2. **Parses them** using Gemini AI (primary) or regex (fallback) — extracts company name, job role, date, email type, and summary
3. **Logs to Google Sheets** — one spreadsheet per user, auto-created with typed columns
4. **Sends alerts** to Telegram, Slack, or WhatsApp
5. **Runs 24/7** on PythonAnywhere free tier, kept alive by cron-job.org

**Target users:** Anyone applying to 50+ jobs who wants automatic tracking without manual data entry.

**Key differentiator:** $0 infrastructure cost — free-tier everything (PythonAnywhere, Gemini API, Google Sheets, Telegram Bot API, cron-job.org).

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
│  (user UI)  │     │   webui.py       │     │   (3 OAuth users) │
└─────────────┘     └────────┬─────────┘     └─────────┬─────────┘
                             │                         │
                             ▼                         ▼
                    ┌──────────────────┐     ┌───────────────────┐
                    │   Gemini AI      │     │   Regex Parser    │
                    │  (primary parse) │────▶│  (fallback parse) │
                    └────────┬─────────┘     └─────────┬─────────┘
                             │                         │
                             ▼                         ▼
                    ┌──────────────────┐     ┌───────────────────┐
                    │ Google Sheets    │     │   Notifier        │
                    │ (per-user, auto) │     │ TG / Slack / WA   │
                    └──────────────────┘     └───────────────────┘
```

### Data Flow (one poll cycle)

```
Gmail API ──[fetch 20 matching emails]──► Poller
    │
    ▼
Parser ──[try AI first]──► Gemini/Groq/NVIDIA ──[JSON]──► Parser
    │                                  │
    │              [if AI fails]       │
    └─────[regex fallback]─────────────┘
    │
    ▼
Validator ──[is company_name valid?]──► skip if not
    │
    ▼
Dedup Check ──[Message-ID already in sheet?]──► skip if yes
    │
    ▼
Sheets Writer ──[append row A-J]──► Google Sheets
    │
    ▼
Notifier ──[send alert]──► Telegram / Slack / WhatsApp
    │
    ▼
Mark as Read ──[remove UNREAD label]──► Gmail
```

---

## 3. File-by-File Breakdown

### Entry Points

| File | Lines | Role |
|---|---|---|
| `webui.py` | 563 | Flask app — routes, OAuth, scheduler, per-user polling |
| `wsgi.py` | 11 | PythonAnywhere WSGI bridge |

### Source Modules (`src/`)

| File | Lines | Role |
|---|---|---|
| `config.py` | 52 | Env var loading, logging setup, constants, validation |
| `main.py` | 61 | `OfferTracker` class — orchestrates one poll cycle |
| `poller.py` | 85 | Gmail API fetch, header extraction, body decode, mark-as-read |
| `parser.py` | 183 | Email parsing — company/role extraction, type classification, date parsing |
| `ai.py` | 126 | AI provider abstraction — Gemini, Groq, NVIDIA API calls |
| `models.py` | 67 | Pydantic `JobApplication` model — validation, sheet rows, alert text |
| `notifier.py` | 89 | Multi-channel notification dispatch |
| `sheets_writer.py` | 47 | Google Sheets CRUD — auto-create, append, dedup |
| `duplicate_checker.py` | 27 | Message-ID dedup cache |
| `scheduler.py` | 43 | Standalone scheduler daemon (CLI mode) |
| `setup_oauth.py` | — | One-time OAuth setup script |

### Web Layer

| File | Lines | Role |
|---|---|---|
| `templates/index.html` | 602 | Single-page HTML/JS app — dashboard, prefs, logs |

### Tests

| File | Tests | What It Covers |
|---|---|---|
| `test_parser.py` | 9 | Company extraction, date parsing, full email parsing, fallback, message IDs |
| `test_models.py` | 3 | Model validation, sheet row format, alert text format |

### Config & Build

| File | Role |
|---|---|
| `.env.example` | All config vars with documentation |
| `requirements.txt` | 9 dependencies |
| `setup.sh` | One-command environment setup |
| `.gitignore` | 21 patterns (secrets, caches, IDE, PDFs, session logs) |
| `generate_docs.py` | Markdown→PDF converter (WeasyPrint) |
| `gmail_filter.xml` | Gmail filter rules for auto-labeling application emails |
| `n8n-workflow.json` | Archived n8n workflow design (8 nodes, preserved for reference) |

### Documentation

| File | Lines | Purpose |
|---|---|---|
| `READme.md` | 158 | Quickstart, badges, architecture, config, deployment |
| `CASE_STUDY.md` | 850+ | Narrative case study for hiring managers |
| `PROJECT_REFERENCE.md` | — | This file — complete technical reference |

---

## 4. Core Data Flow

### webui.py — The Orchestrator

The Flask app runs two parallel systems:

**System 1: User-facing web UI**
- `/` — Dashboard with live stats, recent entries, activity log
- `/auth` `/callback` — Google OAuth flow
- `/save-prefs` — Notification channel selection
- `/trigger` — Manual poll trigger
- `/send-test-email` — Sends a self-addressed test application email
- `/test-notification` — Tests the configured notification channel
- `/upload-credentials` — Admin uploads Google Cloud OAuth JSON

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
    4. Search Gmail: q='subject:"application received" OR subject:"offer letter"...'
    5. For each matching message:
       a. Get full message (format="full")
       b. Extract Message-ID, check against known_ids (column F of sheet)
       c. Skip if duplicate
       d. Call parse_email(full) from parser.py
       e. If parse succeeds: append to sheet, notify user, mark as read
       f. If parse fails: mark as read (skip)
    6. Update last_run/last_count/last_error
```

### Per-User Token Isolation

Each user's OAuth token is stored as:
```
credentials/token_<base64url(email)>.json
```

Example: `credentials/token_c2FjaGluQGV4YW1wbGUuY29t.json`

This allows multiple users to have independent Gmail + Sheets sessions.

---

## 5. Configuration Reference

All config is loaded from `.env` by `src/config.py`.

### Core

| Variable | Default | Description |
|---|---|---|
| `GMAIL_QUERY` | `subject:"application received" OR ...` | Gmail search query |
| `POLL_INTERVAL_MINUTES` | `15` | Poll cycle interval |
| `SHEET_NAME` | `Job Application Tracker` | Google Sheet name |
| `LOG_LEVEL` | `INFO` | Python logging level |

### Notifications

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `TELEGRAM_BOT_USERNAME` | Yes | Bot username (users DM this to connect) |
| `SLACK_BOT_TOKEN` | No | Legacy (not currently used for broadcast) |
| `WHATSAPP_APIKEY` | No | Admin WhatsApp API key (users can set own) |

### AI / LLM

| Variable | Default | Options |
|---|---|---|
| `AI_PROVIDER` | `none` | `gemini`, `groq`, `nvidia`, `none` |
| `AI_MODEL` | `gemini-2.0-flash` | Model name for provider |
| `GEMINI_API_KEY` | — | Required if `AI_PROVIDER=gemini` |
| `GROQ_API_KEY` | — | Required if `AI_PROVIDER=groq` |
| `NVIDIA_API_KEY` | — | Required if `AI_PROVIDER=nvidia` |

### Security

| Variable | Required | Description |
|---|---|---|
| `CRON_SECRET` | Yes | Secret path segment in `/cron/<secret>` |
| `FLASK_ENV` | No | Set to `production` on PythonAnywhere |

---

## 6. API Endpoints

### Authentication

| Method | Path | Description |
|---|---|---|
| GET | `/` | Dashboard (authed) or landing page |
| GET | `/auth` | Initiate Google OAuth flow |
| GET | `/callback` | OAuth callback — creates token, redirects to `/` |
| GET | `/logout` | Clear session |
| POST | `/upload-credentials` | Admin uploads `credentials.json` |

### Preferences

| Method | Path | Description |
|---|---|---|
| POST | `/save-prefs` | Save notification channel + channel-specific config |
| GET | `/change-channel` | Reset channel to "none" |

### Actions

| Method | Path | Description |
|---|---|---|
| GET | `/trigger` | Run poll for authenticated user |
| GET | `/send-test-email` | Send self-addressed test application email |
| POST | `/test-notification` | Send test notification on configured channel |
| POST | `/save-whatsapp-apikey` | Save WhatsApp API key after activation |

### Status

| Method | Path | Description |
|---|---|---|
| GET | `/status` | JSON: authed state, prefs, last run, last error |
| GET | `/logs` | JSON: last 50 log lines |
| GET | `/automation-status` | JSON: scheduler alive, poll interval |
| GET | `/verify-telegram` | Check if user DM'd the bot |
| GET | `/cron/<secret>` | External trigger — polls all users (cron-job.org) |

---

## 7. Parser Deep Dive

### AI Path (`src/ai.py`)

When `AI_PROVIDER` is set (gemini/groq/nvidia), the AI receives this prompt:

```
You are an email parser for a job application tracker.
Extract the following fields from the email and return ONLY valid JSON:

{
  "company_name": "...",
  "job_role": "...",
  "date": "YYYY-MM-DD or null",
  "email_type": "offer_letter|interview_invitation|application_received|rejection|other",
  "summary": "one-line, 10-15 words"
}
```

The response is parsed with `_clean_json()` which strips markdown code fences and extracts `{...}`.

**Supported AI providers:**

| Provider | API Endpoint | Free Tier |
|---|---|---|
| Gemini | `generativelanguage.googleapis.com` | 60 req/min free |
| Groq | `api.groq.com/openai/v1` | 30 req/min free (rate-limited) |
| NVIDIA | `integrate.api.nvidia.com/v1` | Free tier available |

### Regex Fallback Path (`src/parser.py`)

**Company name extraction** — three-layer strategy:

1. **Domain extraction** (always): `re.search(r"@([\w-]+)\.", sender)` → `.title()`
2. **Known company patterns** (subject + body): 40+ big-tech companies in regex alternation
3. **Generic "at/for/with" patterns**: `r"(?:at|for|with)\s+(.+?)(?:\s+(?:is|we|the|position|role)|$)"`
4. **Last resort**: falls back to domain-based name

**Role extraction** — multi-pattern matching:

1. Keyword combo: `Frontend|Backend|Full-Stack|DevOps` + `Engineer|Developer|Intern`
2. Known prefixes: `Software|Data|ML|QA|iOS|Android` + `Engineer|Scientist|Architect`
3. Known roles: `Product|UX|UI|Graphic` + `Manager|Designer|Analyst`
4. Extra patterns: `Offer Letter | <role>`, `Application received: <role>`
5. Fallback: `position|role|job title: <role>`, `for the|as a <role>`
6. Last resort: `"Unknown Position"`

**Email type classification** — keyword detection:

| Type | Keywords |
|---|---|
| `rejection` | `regret to inform`, `unfortunately`, `not moving forward`, `rejected` |
| `offer_letter` | `offer letter`, `offer of`, `internship offer`, `letter of offer` |
| `interview_invitation` | `interview`, `invitation to`, `schedule an interview` |
| `application_received` | `application received`, `thank you for applying`, `we received` |
| `other` | Everything else |

**Date parsing** — tries three formats:

| Format | Pattern | Example |
|---|---|---|
| ISO | `YYYY-MM-DD` | `2025-06-08` |
| US | `MM/DD/YYYY` | `06/08/2025` |
| Long | `Month DD, YYYY` | `June 8, 2025` |

If AI provides a date, it's used first. If regex finds one, it's used second. Otherwise, the email's `internalDate` timestamp is used.

### Parser Flow (`parse_email()`)

```
parse_email(msg)
    ├── extract subject, sender, body, message_id, internal_date
    ├── try parse_email_with_ai()
    │   └── if AI returns valid dict:
    │       ├── company = AI result or regex fallback
    │       ├── role = AI result or regex fallback
    │       ├── email_type = AI result
    │       ├── summary = AI result
    │       ├── date = AI date or regex date or internal_date
    │       └── parser = "AI"
    └── else (AI not configured or failed):
        ├── company = extract_company()
        ├── role = extract_role()
        ├── email_type = classify_email_type()
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

### Slack

**User setup:**
1. Create Slack app at `api.slack.com/apps`
2. Enable Incoming Webhooks
3. Add webhook to a channel
4. Paste webhook URL in preferences

**Technical:**
- Uses webhook URL per user (no bot token needed)
- Messages sent as JSON `{"text": "..."}` via POST
- No verification needed — webhooks work immediately

### WhatsApp (CallMeBot — least reliable)

**User setup:**
1. Select WhatsApp in preferences, enter phone number
2. Tap activation link → opens WhatsApp → send "I allow CallMeBot" to gateway number
3. CallMeBot replies with API key → paste in app

**Technical:**
- Uses `api.callmebot.com/whatsapp.php` with phone + apikey + text
- Known issues: API key delivery is unreliable (gateway numbers sometimes don't respond)
- Two gateway numbers: `+34 644 64 60 89` and `+34 623 78 64 49`

### Pushover (app-level fallback)

- Configured in `.env` with `PUSHOVER_TOKEN` and `PUSHOVER_USER`
- Used by `notify_all()` — not exposed to users in web UI

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
|---|---|---|---|
| `test_parser.py` | 9 | 108 | Company extraction, date parsing, full email parsing, domain fallback, message IDs, body date parsing |
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

# Test cases:
# - Domain extraction: "no-reply@google.com" → "Google"
# - Full parse: "Software Engineer at Google" → company="Google", role="Software Engineer"
# - Thank you: "Thank you for applying to Stripe!" → company="Stripe"
# - Subject extraction: "Data Scientist at Microsoft" → company="Microsoft"
# - Domain fallback: "hr@some-startup.io" → company="Some-Startup"
# - Body date: "Application Date: 2025-06-08" → date="2025-06-08"
```

---

## 12. Known Issues & Roadmap

### Bugs

| Issue | File | Severity | Description |
|---|---|---|---|
| Missing `is:unread` in Gmail query | `webui.py:167` | Medium | Without `is:unread`, already-processed emails may be re-fetched. The dedup check mitigates this but adds API overhead |
| Hardcoded Gmail query | `webui.py:167` | Low | Query string is hardcoded instead of using `GMAIL_QUERY` from config.py |
| WhatsApp CallMeBot unreliable | `notifier.py:48` | Low | Gateway numbers often don't respond with API key |
| Slack `channels:read` scope | — | Low | Bot token approach needs `channels:read` scope for channel discovery |

### Technical Debt

| Issue | Location | Description |
|---|---|---|
| `last_run` / `last_count` / `last_error` are in-memory dicts | `webui.py:43-45` | Lost on app restart; no persistence |
| `log_buffer` is in-memory | `webui.py:47` | Lost on restart; no log rotation |
| Single-threaded scheduler | `webui.py:232` | If one user's poll hangs, subsequent users are delayed |
| No rate limiting on `/cron/` | `webui.py:464` | Anyone with the secret can trigger polls |
| Tokens stored on filesystem | `webui.py:82-84` | Not suitable for multi-instance deployment |
| No token revocation detection | `webui.py:87-104` | If user revokes access, app retries silently until token expires |

### Roadmap

| Feature | Priority | Description |
|---|---|---|
| Dashboard charts | Medium | Application trend line, response rate pie, company breakdown bar |
| AI categorization | Low | Auto-tag applications by industry, role level, location |
| CSV/Excel export | Low | One-click export of sheet data |
| Multi-language support | Low | Parse emails in Hindi, Spanish, etc. (Gemini supports 100+ languages) |
| Email reply detection | Low | Detect when a company replies to your application |
| Webhook for custom integrations | Low | Generic webhook so users can pipe to Zapier/Make/n8n |

---

## 13. Session History Summary

This project was built across 9 AI coding sessions. Key milestones:

| Session | Date | Key Events |
|---|---|---|
| 1 | Jun 8 | Initial Flask app + Gmail API + regex parser |
| 2 | Jun 8-9 | Multi-user OAuth, per-user tokens, notification channels |
| 3 | Jun 9 | Telegram integration, preference persistence, local testing |
| 4 | Jun 9-10 | n8n approach — designed workflow, hit Android tracing-stop bug |
| 5 | Jun 10 | n8n debugging — CONT daemon fix, partial success |
| 6 | Jun 10-11 | Manus AI attempt — hit credit limits (300/day, needed 672) |
| 7 | Jun 11 | Returned to Flask — merged best of all approaches, PythonAnywhere deploy |
| 8 | Jun 11 | 11 tests passing, WhatsApp + Slack channels, session history extraction |
| 9 | Jun 11 | Documentation — README, CASE_STUDY.pdf, GitHub push, documentation skill |

### Why Custom Flask (Approach #4) Won

- **n8n (Approach #2):** Android Termux proot kills Node.js threads (tracing-stop state). Even with CONT daemon, unreliable for 24/7.
- **Manus AI (Approach #3):** 300 credits/day insufficient for 672 emails/day (every 15 min polling). No multi-user support. No persistent storage.
- **Custom Flask + cron-job.org:** Full control, $0 infra, multi-user, 15-min polling interval, all notification channels.

---

## Appendix A: Full Gmail Query

```
subject:"application received" OR
subject:"thank you for applying" OR
subject:"application confirmation" OR
subject:"offer letter" OR
subject:"we received your application"
```

## Appendix B: Google Sheet Columns

| Column | Header | Source |
|---|---|---|
| A | Company Name | Parser (AI or regex) |
| B | Job Role | Parser (AI or regex) |
| C | Application Date | Parser or email internalDate |
| D | Email Subject | Gmail header |
| E | Sender Email | Gmail header |
| F | Message ID | Gmail header (dedup key) |
| G | Alert Sent | Always "Yes" |
| H | Email Type | Classifier (Offer/Interview/Received/Rejection/Other) |
| I | Summary | AI only (empty for regex) |
| J | Parser | "AI" or "Regex" |

## Appendix C: Dependencies

```
flask>=3.0
google-api-python-client>=2.0
google-auth-oauthlib>=1.0
google-auth-httplib2>=0.1
gspread>=6.0
pydantic>=2.0
python-dotenv>=1.0
requests>=2.28
pytest
```

## Appendix D: Key Design Decisions

| Decision | Rationale |
|---|---|
| **Flask over FastAPI** | Simpler WSGI deployment on PythonAnywhere; no async complexity needed |
| **pydantic for models** | Built-in validation, serialization, and type hints; lightweight |
| **gspread over raw Sheets API** | Higher-level API (auto-find sheet, append rows, col values); fewer lines |
| **Per-user tokens (not single account)** | Each user connects their own Gmail; no central account needed |
| **AI primary + regex fallback** | AI is more accurate (company/role/summary) but regex works when API is down |
| **cron-job.org over in-app scheduler** | PythonAnywhere free tier sleeps; external ping wakes it |
| **Single HTML file (no JS framework)** | Zero build step; deployable as-is; works without npm |
| **Base64-encoded token filenames** | Safe for filesystem (no @ or / in filenames); reversible for debugging |
