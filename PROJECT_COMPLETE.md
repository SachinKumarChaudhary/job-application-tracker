# Job Application Auto-Tracker — Complete Project A-Z

> **From first line of code to live deployment — every approach, every failure, every decision, every technical detail.**
>
> GitHub: https://github.com/SachinKumarChaudhary/job-application-tracker
> Live: https://SachinKumarChaudhary.pythonanywhere.com/
> Telegram: @GotJobAlert_bot

---

## Table of Contents

**Part I — Project History**
1. [The Problem](#1-the-problem)
2. [Approach 1: Custom Flask App (Session 1-3)](#2-approach-1-custom-flask-app-session-1-3)
3. [Approach 2: n8n Workflow (Session 4-5)](#3-approach-2-n8n-workflow-session-4-5)
4. [Approach 3: Manus AI (Session 6)](#4-approach-3-manus-ai-session-6)
5. [Approach 4: Flask Redux + PythonAnywhere (Session 7)](#5-approach-4-flask-redux--pythonanywhere-session-7)
6. [Testing & Polish (Session 7-8)](#6-testing--polish-session-7-8)
7. [Documentation & GitHub (Session 9)](#7-documentation--github-session-9)

**Part II — Technical Reference**
8. [Architecture (Final)](#8-architecture-final)
9. [File-by-File Breakdown](#9-file-by-file-breakdown)
10. [Core Data Flow](#10-core-data-flow)
11. [API Endpoints](#11-api-endpoints)
12. [Parser Deep Dive (AI + Regex)](#12-parser-deep-dive-ai--regex)
13. [Notification Channels](#13-notification-channels)
14. [OAuth Flow](#14-oauth-flow)
15. [Configuration Reference](#15-configuration-reference)
16. [Testing Reference](#16-testing-reference)
17. [Deployment Reference](#17-deployment-reference)
18. [Known Issues, Tech Debt & Roadmap](#18-known-issues-tech-debt--roadmap)

**Appendices**
- [A: Session Timeline](#appendix-a-session-timeline)
- [B: Why Each Approach Was Chosen/Rejected](#appendix-b-why-each-approach-was-chosenrejected)
- [C: What I'd Do Differently](#appendix-c-what-id-do-differently)
- [D: Full Gmail Query](#appendix-d-full-gmail-query)
- [E: Google Sheet Columns](#appendix-e-google-sheet-columns)
- [F: Dependencies](#appendix-f-dependencies)
- [G: Key Design Decisions](#appendix-g-key-design-decisions)

---

# Part I — Project History

## 1. The Problem

**Goal:** Build a job application auto-tracker that:
- Polls Gmail for application/offer/rejection emails
- Extracts company name, job role, date, and email type
- Logs everything to a Google Sheet
- Sends real-time notifications (Telegram, Slack, or WhatsApp)
- Supports multiple users (each connects their own Gmail)
- Runs 24/7 with zero infrastructure cost

**Constraints:**
- $0 budget — everything must be free-tier
- Must work on PythonAnywhere free tier
- Android/Termux development environment with ptrace bugs
- Must be demonstrable for a portfolio/review

---

## 2. Approach 1: Custom Flask App (Session 1-3)

**Date:** June 8-9, 2026

### Session 1 — Initial Build (Jun 8)

Built the first version in a single session:

- **Flask web app** with Google OAuth for Gmail access
- **Gmail API polling** — fetches emails matching application keywords
- **Regex parser** — extracts company (from domain + 40+ known companies), role (from 15+ patterns), and email type (offer/interview/rejection/received)
- **Google Sheets writer** — auto-creates spreadsheet, appends rows
- **Telegram notifier** — sends DMs via bot
- **Pydantic model** — `JobApplication` with validation, sheet rows, alert text

**Key files created:**
- `webui.py` — Flask app (OAuth, routes, scheduler)
- `src/parser.py` — Company/role extraction, type classification
- `src/poller.py` — Gmail API fetch, body decode
- `src/config.py` — Env var loading
- `src/models.py` — Pydantic model
- `src/notifier.py` — Telegram/Slack/WhatsApp/Pushover
- `src/sheets_writer.py` — Google Sheets CRUD
- `templates/index.html` — Single-page UI
- `tests/test_parser.py` — 9 parser tests
- `tests/test_models.py` — 3 model tests

### Session 2 — Multi-User OAuth (Jun 8-9)

Added multi-user support:
- **Per-user token storage:** `credentials/token_<base64(email)>.json`
- **User preferences:** `user_prefs.json` — notification channel, sheet ID, phone, API keys
- **Notification channel selection UI:** Telegram, Slack, WhatsApp, or None
- **Scheduler loop:** Background thread polls all users every 15 minutes
- **Improved index.html:** Dashboard with stats, logs, activity table

### Session 3 — Telegram Integration (Jun 9)

- Connected Telegram bot `@GotJobAlert_bot`
- Auto-detection: after user saves @username, app polls `getUpdates` every 3s to find their DM
- Send test notification button
- Verify Telegram button with auto-polling JS

---

## 3. Approach 2: n8n Workflow (Session 4-5)

**Date:** June 9-10, 2026

### The Idea

Replace the Flask app with a visual n8n workflow — same pipeline (Gmail → Parse → Sheets → Notify) but drag-and-drop.

### The n8n Workflow (8 nodes)

```
Gmail Trigger → Decode MIME → Gemini API → Parse & Validate → Is Valid?
                                                              ↓
                                           ┌── Yes → Append to Sheet → Send Telegram
                                           └── No  → End
```

| Node | What it does |
|---|---|
| **Gmail Trigger** | Polls every 15 min with application subject filter |
| **Decode MIME** | JavaScript node — extracts headers, decodes base64 body |
| **Gemini API** | HTTP Request node — calls `gemini-2.0-flash:generateContent` |
| **Parse & Validate** | JavaScript node — strips markdown, parses JSON, validates fields |
| **Is Valid?** | IF node — skips if company_name is "Unknown" |
| **Append to Sheet** | Google Sheets node — appends parsed row |
| **Send Telegram** | Telegram node — sends Markdown alert |
| **End** | No-op terminal |

### The Bug That Killed n8n

On Android/Termux proot, Node.js processes enter **"tracing stop"** state immediately after fork:

```
$ cat /proc/PID/status | grep State
State:  t (tracing stop)
```

This is a Termux proot limitation — ptrace restrictions freeze all new threads.

**The fix (partial):**
```bash
npx n8n start &
for t in /proc/PID/task/*/; do kill -CONT $(basename "$t"); done
# Then run CONT daemon:
while true; do
  for pid in $(pgrep -f "node.*n8n"); do
    for t in /proc/$pid/task/*/; do kill -CONT $(basename "$t"); done
  done; sleep 1
done
```

**Why it was rejected:**
- Even with the CONT daemon, n8n would freeze during SQLite migrations or Express init
- Required ~200MB RAM (Flask uses ~30MB)
- No multi-user support (single Gmail account per workflow)
- Would need a real server (VPS) to run reliably — $0 budget violated

**Preserved:** `n8n-workflow.json` and `docs/n8n-workflow.md` in the repo.

---

## 4. Approach 3: Manus AI (Session 6)

**Date:** June 10-11, 2026

### The Idea

Use Manus AI (an autonomous AI agent) to handle the entire pipeline — it has browser automation, web research, and data processing capabilities.

### What Was Built

Manus was prompted to:
1. Search job boards (LinkedIn, Indeed, Wellfound) for "Software Engineer Intern" postings
2. Extract company, role, date, and application URL
3. Log to Google Sheets
4. Send Telegram alerts

### The Problem

Manus AI has **300 credits per day**. Each email poll costs ~1 credit. We needed polling every 15 minutes = 96 polls/day minimum. With multiple users (7), that's 672 polls/day — over 2x the daily limit. Additionally, Manus had no persistent storage, no multi-user support, and sessions timed out.

**Verdict:** Great for one-shot tasks, not for continuous 24/7 automation.

---

## 5. Approach 4: Flask Redux + PythonAnywhere (Session 7)

**Date:** June 11, 2026

### The Decision

After n8n (killed by Android bugs) and Manus (killed by credit limits), returned to the Flask app with key improvements:

**From n8n:** Ported the AI parsing code node logic → `src/ai.py`
- Gemini API integration with JSON response parsing
- Clean JSON extraction (strip markdown fences)
- Same prompt as the n8n version

**From Manus:** Multi-user architecture + cron-job.org automation

### Deployment

Deployed to PythonAnywhere free tier:

```python
# wsgi.py
path = '/home/SachinKumarChaudhary/Gotjobalert'
sys.path.insert(0, path)
os.chdir(path)
os.environ['FLASK_ENV'] = 'production'
from webui import app as application
```

**24/7 keep-alive:** cron-job.org pings `/cron/gotjobalert_auto_2026` every 15 min.

### Notification Channels Added

- **WhatsApp CallMeBot** — phone + API key via `api.callmebot.com/whatsapp.php`
- **Slack webhooks** — per-user webhook URLs
- **Pushover** — app-level fallback (not exposed in UI)

---

## 6. Testing & Polish (Session 7-8)

**Date:** June 11, 2026

### Test Suite — 11 passing

```
test_parser.py:
  ✓ test_extract_company_from_domain     — no-reply@google.com → Google
  ✓ test_parse_date_iso                   — 2025-06-08 → datetime
  ✓ test_parse_simple_email               — Software Engineer at Google → parsed
  ✓ test_parse_thank_you_email            — Backend Engineer Intern at Stripe → parsed
  ✓ test_parse_company_from_subject       — Data Scientist at Microsoft → Microsoft
  ✓ test_parse_unknown_company_fallback   — hr@some-startup.io → Some-Startup
  ✓ test_duplicate_message_id             — Message-ID preserved
  ✓ test_date_in_body                     — Date from body text

test_models.py:
  ✓ test_minimal_job_application          — Pydantic validation
  ✓ test_to_sheet_row                     — 9-column row format
  ✓ test_to_alert_text                    — Markdown alert with emoji
```

### Known Bugs Fixed

| Bug | Fix |
|---|---|
| Telegram broadcast used TELEGRAM_BOT_TOKEN as chat_id | Now uses per-user chat_id from prefs |
| Gmail query hardcoded in webui.py | Added `GMAIL_QUERY` env var (webui.py still hardcodes — not yet fixed) |
| Missing `is:unread` filter | Dedup via Message-ID mitigates re-processing |

---

## 7. Documentation & GitHub (Session 9)

**Date:** June 11, 2026

### Documentation Created

| File | Lines | Purpose |
|---|---|---|
| `README.md` | 158 | Quickstart, badges, architecture, config, deploy |
| `CASE_STUDY.md` | 850+ | Narrative case study for hiring managers |
| `PROJECT_REFERENCE.md` | 663 | Technical reference — every file, endpoint, config |
| `PROJECT_COMPLETE.md` | — | **This file** — single A-Z reference |
| `docs/n8n-workflow.md` | 153 | n8n workflow breakdown, code, why rejected |
| `GITHUB.md` | 36 | Public Git info for contributors |
| `generate_docs.py` | — | Markdown→PDF converter script |

### GitHub Setup

```
Repo:   https://github.com/SachinKumarChaudhary/job-application-tracker
Branch: main
Commits: 5
Files:  28
```

**Commit history:**
1. `c0907b7` — Initial commit (25 source files)
2. `fdc7ec2` — Add PROJECT_REFERENCE.md
3. `8505649` — Add docs/n8n-workflow.md
4. `29b38bd` — Add GITHUB.md
5. `41bbaa1` — Add PROJECT_COMPLETE.md

### Documentation Skill

Created a reusable **documentation skill** at `~/.config/opencode/skills/documentation/SKILL.md`:
- 4-phase workflow: Audit → Outline → Generate → Polish
- Diátaxis framework (Tutorial, How-to, Reference, Explanation)
- PDF generation with WeasyPrint
- Mermaid diagram support

---

# Part II — Technical Reference

## 8. Architecture (Final)

### System Diagram

```
                    ┌─────────────────────────┐
                    │    cron-job.org         │
                    │   (pings every 15m)     │
                    └────────────┬────────────┘
                                 │ GET /cron/<secret>
                                 ▼
┌─────────────┐     ┌────────────────────┐     ┌─────────────────────┐
│   Browser   │────▶│   Flask App        │────▶│   Gmail API         │
│  (user UI)  │     │   webui.py         │     │   (3 OAuth users)   │
└─────────────┘     └────────┬───────────┘     └──────────┬──────────┘
                             │                            │
                             ▼                            ▼
                    ┌────────────────────┐     ┌─────────────────────┐
                    │   Gemini AI        │     │   Regex Parser      │
                    │  (primary parse)   │────▶│  (fallback)         │
                    └────────┬───────────┘     └──────────┬──────────┘
                             │                            │
                             ▼                            ▼
                    ┌────────────────────┐     ┌─────────────────────┐
                    │ Google Sheets      │     │   Notifier          │
                    │ (per-user, auto)   │     │ Telegram/Slack/WA   │
                    └────────────────────┘     └─────────────────────┘
```

### Data Flow (one poll cycle)

```
Gmail API ──fetch 20 matching emails──► Poller
    │
    ▼
Parser ──try AI first──► Gemini/Groq/NVIDIA ──JSON──► Parser
    │                                │
    │         if AI fails            │
    └─────regex fallback─────────────┘
    │
    ▼
Validator ──is company_name valid?──► skip if not
    │
    ▼
Dedup ──Message-ID in sheet?──► skip if yes
    │
    ▼
Sheets ──append row A-J──► Google Sheets
    │
    ▼
Notifier ──send alert──► Telegram / Slack / WhatsApp
    │
    ▼
Mark Read ──remove UNREAD label──► Gmail
```

### Components Summary

| Component | File | Lines | Role |
|---|---|---|---|
| Flask app | `webui.py` | 563 | Routes, OAuth, scheduler, per-user polling |
| Poller | `src/poller.py` | 85 | Gmail fetch, header extraction, body decode |
| Parser | `src/parser.py` | 183 | Company/role extraction, type classification |
| AI layer | `src/ai.py` | 126 | Gemini/Groq/NVIDIA API calls |
| Models | `src/models.py` | 67 | Pydantic JobApplication |
| Notifier | `src/notifier.py` | 89 | Telegram/Slack/WhatsApp/Pushover |
| Sheets | `src/sheets_writer.py` | 47 | Google Sheets CRUD |
| Dedup | `src/duplicate_checker.py` | 27 | Message-ID cache |
| Scheduler | `src/scheduler.py` | 43 | Standalone CLI daemon |
| HTML UI | `templates/index.html` | 602 | Dashboard + prefs + logs |

---

## 9. File-by-File Breakdown

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
| `n8n-workflow.json` | Archived n8n workflow design (8 nodes) |

### Documentation

| File | Size | Purpose |
|---|---|---|
| `README.md` | 6.7K | Quickstart, badges, architecture, config, deployment |
| `CASE_STUDY.md` | 46K | Narrative case study for hiring managers |
| `PROJECT_REFERENCE.md` | 25K | Standalone technical reference |
| `PROJECT_COMPLETE.md` | — | This file — single A-Z reference |
| `docs/n8n-workflow.md` | 5.5K | n8n workflow breakdown, code, why rejected |
| `GITHUB.md` | 1K | Public Git info for contributors |

---

## 10. Core Data Flow

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

This allows multiple users to have independent Gmail + Sheets sessions. Token auto-refresh and scope mismatch detection are handled in `get_creds()`.

---

## 11. API Endpoints

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

## 12. Parser Deep Dive (AI + Regex)

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

**Company name extraction — three-layer strategy:**

1. **Domain extraction** (always): `re.search(r"@([\w-]+)\.", sender)` → `.title()`
2. **Known company patterns** (subject + body): 40+ big-tech companies in regex alternation (Google, Microsoft, Amazon, Meta, Apple, Stripe, etc.)
3. **Generic "at/for/with" patterns**: `r"(?:at|for|with)\s+(.+?)(?:\s+(?:is|we|the|position|role)|$)"`
4. **Last resort**: falls back to domain-based name

**Role extraction — multi-pattern matching:**

1. Keyword combo: `Frontend|Backend|Full-Stack|DevOps` + `Engineer|Developer|Intern`
2. Known prefixes: `Software|Data|ML|QA|iOS|Android` + `Engineer|Scientist|Architect`
3. Known roles: `Product|UX|UI|Graphic` + `Manager|Designer|Analyst`
4. Extra patterns: `Offer Letter | <role>`, `Application received: <role>`
5. Fallback: `position|role|job title: <role>`, `for the|as a <role>`
6. Last resort: `"Unknown Position"`

**Email type classification — keyword detection:**

| Type | Keywords |
|---|---|
| `rejection` | `regret to inform`, `unfortunately`, `not moving forward`, `rejected` |
| `offer_letter` | `offer letter`, `offer of`, `internship offer`, `letter of offer` |
| `interview_invitation` | `interview`, `invitation to`, `schedule an interview` |
| `application_received` | `application received`, `thank you for applying`, `we received` |
| `other` | Everything else |

**Date parsing — tries three formats:**

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

## 13. Notification Channels

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
- Known issue: API key delivery is unreliable (gateway numbers sometimes don't respond)
- Two gateway numbers: `+34 644 64 60 89` and `+34 623 78 64 49`

### Pushover (app-level fallback)

- Configured in `.env` with `PUSHOVER_TOKEN` and `PUSHOVER_USER`
- Used by `notify_all()` — not exposed to users in web UI

---

## 14. OAuth Flow

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

## 15. Configuration Reference

All config is loaded from `.env` by `src/config.py`.

### Core

| Variable | Default | Description |
|---|---|---|
| `GMAIL_QUERY` | `subject:"application received" OR subject:"offer letter" OR ...` | Gmail search query |
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

## 16. Testing Reference

### Run Tests

```bash
cd /path/to/project
pytest -v
```

### Current Coverage

| Test | What It Checks |
|---|---|
| `test_extract_company_from_domain` | `no-reply@google.com` → `Google` |
| `test_parse_date_iso` | `2025-06-08` parses correctly |
| `test_parse_simple_email` | Full pipeline: Google + Software Engineer |
| `test_parse_thank_you_email` | Stripe + Backend Engineer Intern |
| `test_parse_company_from_subject` | Microsoft from subject line |
| `test_parse_unknown_company_fallback` | Domain fallback for startups |
| `test_duplicate_message_id` | Message-ID preserved through parse |
| `test_date_in_body` | Date extracted from body text |
| `test_minimal_job_application` | Pydantic model validation |
| `test_to_sheet_row` | 9-column row format |
| `test_to_alert_text` | Markdown + emoji format |

### Mock Pattern Used in Tests

```python
def make_mock_msg(subject, sender, body):
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

## 17. Deployment Reference

### PythonAnywhere (free tier)

```bash
# Upload code via git clone or web console
# Create virtualenv
mkvirtualenv offertracker --python=python3.10
pip install -r requirements.txt

# Set env vars in PythonAnywhere Secrets tab:
#   TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME,
#   CRON_SECRET, GEMINI_API_KEY (if using AI), AI_PROVIDER

# Upload credentials.json via web UI
# Reload web app
```

**WSGI file (`wsgi.py`):**
```python
path = '/home/SachinKumarChaudhary/Gotjobalert'
sys.path.insert(0, path)
os.chdir(path)
os.environ['FLASK_ENV'] = 'production'
from webui import app as application
```

### cron-job.org (24/7 automation)

```
URL: https://SachinKumarChaudhary.pythonanywhere.com/cron/gotjobalert_auto_2026
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
python webui.py   # http://localhost:8080
```

---

## 18. Known Issues, Tech Debt & Roadmap

### Bugs

| Issue | Location | Severity | Description |
|---|---|---|---|
| Missing `is:unread` in Gmail query | `webui.py:167` | Medium | Without `is:unread`, already-processed emails may be re-fetched. Dedup mitigates but adds API overhead |
| Hardcoded Gmail query | `webui.py:167` | Low | String literal instead of `config.GMAIL_QUERY` |
| WhatsApp CallMeBot unreliable | `notifier.py:48` | Low | Gateway numbers often don't respond with API key |
| In-memory state | `webui.py:43-47` | Low | `last_run`, `last_count`, `log_buffer` lost on restart |

### Technical Debt

| Issue | Location | Description |
|---|---|---|
| Single-threaded scheduler | `webui.py:232` | One slow user poll delays others |
| Tokens on filesystem | `webui.py:82-84` | Not suitable for multi-instance deployment |
| No rate limiting on `/cron/` | `webui.py:464` | Anyone with the secret can trigger polls |
| No token revocation detection | `webui.py:87-104` | Silent retry until token expires |

### Roadmap

| Feature | Priority | Description |
|---|---|---|
| Dashboard charts | Medium | Application trends, response rates, company breakdown |
| CSV/Excel export | Low | One-click data export |
| AI categorization | Low | Auto-tag by industry, role level, location |
| Multi-language | Low | Parse Hindi, Spanish emails via Gemini |
| Email reply detection | Low | Detect company follow-ups |
| Custom webhook | Low | Pipe to Zapier/Make/n8n |

---

# Appendices

## Appendix A: Session Timeline

| Session | Date | Duration | Key Events |
|---|---|---|---|
| **1** | Jun 8 | ~Full day | Initial Flask app — Gmail API, regex parser, Google Sheets, Telegram, 12 tests |
| **2** | Jun 8-9 | ~Evening | Multi-user OAuth, per-user token isolation, prefs, notification channel UI |
| **3** | Jun 9 | ~Afternoon | Telegram auto-verify, test notification, UI polish |
| **4** | Jun 9-10 | ~Evening | n8n workflow design — 8 nodes, Gmail→Decode→Gemini→Validate→Sheets→Telegram |
| **5** | Jun 10 | ~Morning | n8n Android tracing-stop bug — CONT daemon fix, partial success |
| **6** | Jun 10-11 | ~Afternoon | Manus AI approach — hit 300 credit/day limit for 672/day need |
| **7** | Jun 11 | ~Morning | Returned to Flask — merged n8n AI code, PythonAnywhere deploy, WhatsApp/Slack |
| **8** | Jun 11 | ~Late morning | 11 tests passing, session history extraction, error handling polish |
| **9** | Jun 11 | ~Afternoon | Documentation — README, CASE_STUDY.pdf, GitHub push, documentation skill |

## Appendix B: Why Each Approach Was Chosen/Rejected

| Approach | Chosen Because | Rejected Because |
|---|---|---|
| **Flask (v1)** | Full control, lightweight, familiar | No UI, single-user, no AI parsing |
| **n8n** | Visual workflow, no-code, built-in integrations | Android tracing-stop bug kills Node.js threads |
| **Manus AI** | Autonomous, browser automation, "set and forget" | 300 credits/day insufficient for 672 polls/day |
| **Flask (v2)** | All previous learnings combined | — (final solution) |

## Appendix C: What I'd Do Differently

1. **Use `is:unread` in Gmail query** — prevents re-fetching already-seen emails
2. **Database instead of in-memory dicts** — SQLite for persistent state (last_run, logs)
3. **Async worker queue** — Celery or Redis queue instead of single-threaded scheduler
4. **Test Gmail OAuth earlier** — scope mismatch issues were caught late
5. **Skip WhatsApp CallMeBot** — Telegram-only is more reliable; WhatsApp adds complexity
6. **Better error handling** — per-email try/except could be more granular

## Appendix D: Full Gmail Query

```
subject:"application received" OR
subject:"thank you for applying" OR
subject:"application confirmation" OR
subject:"offer letter" OR
subject:"we received your application"
```

## Appendix E: Google Sheet Columns

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

## Appendix F: Dependencies

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

## Appendix G: Key Design Decisions

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

---

*End of PROJECT_COMPLETE.md — single-file A-Z reference covering history, architecture, every file, endpoints, parser internals, OAuth flow, config, deployment, testing, known issues, and appendices. Generated 2026-06-11.*
