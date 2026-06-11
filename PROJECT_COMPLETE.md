# Job Application Auto-Tracker — Complete Project History

> **From first line of code to live deployment — every approach, every failure, every decision.**
>
> GitHub: https://github.com/SachinKumarChaudhary/job-application-tracker
> Live: https://SachinKumarChaudhary.pythonanywhere.com/
> Telegram: @GotJobAlert_bot

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [Approach 1: Custom Flask App (Session 1-3)](#2-approach-1-custom-flask-app-session-1-3)
3. [Approach 2: n8n Workflow (Session 4-5)](#3-approach-2-n8n-workflow-session-4-5)
4. [Approach 3: Manus AI (Session 6)](#4-approach-3-manus-ai-session-6)
5. [Approach 4: Flask Redux + PythonAnywhere (Session 7)](#5-approach-4-flask-redux--pythonanywhere-session-7)
6. [Testing & Polish (Session 7-8)](#6-testing--polish-session-7-8)
7. [Documentation & GitHub (Session 9)](#7-documentation--github-session-9)
8. [Architecture (Final)](#8-architecture-final)
9. [All Files in the Repo](#9-all-files-in-the-repo)
10. [Configuration Reference](#10-configuration-reference)
11. [Testing Reference](#11-testing-reference)
12. [Deployment Reference](#12-deployment-reference)
13. [Known Issues](#13-known-issues)
14. [Appendix: Session Timeline](#14-appendix-session-timeline)

---

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
# Step 1: Start n8n
npx n8n start &

# Step 2: Manually unstuck (kill -CONT each thread)
for t in /proc/PID/task/*/; do
  kill -CONT $(basename "$t")
done

# Step 3: CONT daemon (send CONT every 1s to keep it alive)
while true; do
  for pid in $(pgrep -f "node.*n8n"); do
    for t in /proc/$pid/task/*/; do
      kill -CONT $(basename "$t")
    done
  done
  sleep 1
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

Manus AI has **300 credits per day**. Each email poll costs ~1 credit. We needed polling every 15 minutes = 96 polls/day minimum. With multiple users (7), that's 672 polls/day — over 2x the daily limit.

Additionally, Manus had no persistent storage, no multi-user support, and sessions timed out.

**Verdict:** Great for one-shot tasks, not for continuous 24/7 automation.

---

## 5. Approach 4: Flask Redux + PythonAnywhere (Session 7)

**Date:** June 11, 2026

### The Decision

After n8n (killed by Android bugs) and Manus (killed by credit limits), returned to the Flask app with key improvements:

### What Changed

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

### Test Suite

```
cd /path/to/project && pytest -v

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

11 passed
```

### Known Bugs Fixed

| Bug | Fix |
|---|---|
| Telegram broadcast used TELEGRAM_BOT_TOKEN as chat_id | Fixed — now uses per-user chat_id from prefs |
| Gmail query hardcoded in webui.py | Added GMAIL_QUERY env var (but webui.py still hardcodes — not yet fixed) |
| Missing `is:unread` filter | Dedup via Message-ID mitigates re-processing |

### Known Bugs Remaining

1. `webui.py:167` — Gmail query hardcoded instead of using config
2. `webui.py:165-168` — Missing `is:unread` (dedup mitigates but adds API overhead)
3. `notifier.py:48` — WhatsApp CallMeBot unreliable
4. `webui.py:43-47` — In-memory state (lost on restart)

---

## 7. Documentation & GitHub (Session 9)

**Date:** June 11, 2026

### Documentation Created

| File | Lines | Purpose |
|---|---|---|
| `README.md` | 158 | Quickstart, badges, architecture, config, deploy |
| `CASE_STUDY.md` | 850+ | Narrative case study for hiring managers |
| `PROJECT_REFERENCE.md` | 663 | Complete technical reference — every file, endpoint, config |
| `PROJECT_COMPLETE.md` | — | **This file** — entire project history |
| `docs/n8n-workflow.md` | 153 | n8n workflow breakdown, code, why rejected |
| `GITHUB.md` | 36 | Public Git info for contributors |
| `generate_docs.py` | — | Markdown→PDF converter script |

### GitHub Setup

```
Repo:   https://github.com/SachinKumarChaudhary/job-application-tracker
Branch: main
Commits: 4
Files:  27
```

**Commit history:**
1. `c0907b7` — Initial commit (25 source files)
2. `fdc7ec2` — Add PROJECT_REFERENCE.md
3. `8505649` — Add docs/n8n-workflow.md
4. `29b38bd` — Add GITHUB.md

### Documentation Skill

Created a reusable **documentation skill** at `~/.config/opencode/skills/documentation/SKILL.md`:
- 4-phase workflow: Audit → Outline → Generate → Polish
- Diátaxis framework (Tutorial, How-to, Reference, Explanation)
- PDF generation with WeasyPrint
- Mermaid diagram support

---

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

### Components

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

## 9. All Files in the Repo

```
job-application-tracker/
├── .env.example          # All config vars with documentation
├── .gitignore            # 21 patterns (secrets, caches, PDFs, sessions)
├── CASE_STUDY.md         # 850-line hiring case study
├── GITHUB.md             # Public Git info
├── PROJECT_COMPLETE.md   # This file — complete history
├── PROJECT_REFERENCE.md  # 663-line technical reference
├── README.md             # Quickstart with badges and architecture
├── docs/
│   └── n8n-workflow.md   # n8n workflow reference (archived)
├── generate_docs.py      # Markdown→PDF converter
├── gmail_filter.xml      # Gmail filter rules
├── n8n-workflow.json      # Archived n8n workflow (8 nodes)
├── requirements.txt       # 9 Python dependencies
├── setup.sh               # One-command setup
├── src/
│   ├── ai.py              # AI provider abstraction (Gemini/Groq/NVIDIA)
│   ├── config.py          # Env var loading and constants
│   ├── duplicate_checker.py # Message-ID dedup
│   ├── main.py            # OfferTracker orchestration class
│   ├── models.py          # Pydantic JobApplication model
│   ├── notifier.py        # Multi-channel notification dispatch
│   ├── parser.py          # Email parsing (AI + regex)
│   ├── poller.py          # Gmail API operations
│   ├── scheduler.py       # Standalone scheduler daemon
│   ├── setup_oauth.py     # One-time OAuth setup
│   └── sheets_writer.py   # Google Sheets CRUD
├── templates/
│   └── index.html         # Single-page web UI (602 lines)
├── tests/
│   ├── test_models.py     # 3 model tests
│   └── test_parser.py     # 9 parser tests
├── webui.py               # Main Flask app (563 lines)
└── wsgi.py                # PythonAnywhere WSGI bridge
```

---

## 10. Configuration Reference

### Core

| Variable | Default | Description |
|---|---|---|
| `GMAIL_QUERY` | `subject:"application received" OR subject:"offer letter" OR ...` | Gmail search query |
| `POLL_INTERVAL_MINUTES` | `15` | Poll cycle interval |
| `SHEET_NAME` | `Job Application Tracker` | Google Sheet name |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `CRON_SECRET` | Required | Secret path in `/cron/<secret>` |

### Notifications

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `TELEGRAM_BOT_USERNAME` | Yes | Bot username (users DM this) |

### AI Providers

| Variable | Default | Options |
|---|---|---|
| `AI_PROVIDER` | `none` | `gemini`, `groq`, `nvidia`, `none` |
| `AI_MODEL` | `gemini-2.0-flash` | Model name |
| `GEMINI_API_KEY` | Conditional | Required if `AI_PROVIDER=gemini` |
| `GROQ_API_KEY` | Conditional | Required if `AI_PROVIDER=groq` |
| `NVIDIA_API_KEY` | Conditional | Required if `AI_PROVIDER=nvidia` |

---

## 11. Testing Reference

```bash
pytest -v
```

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

---

## 12. Deployment Reference

### PythonAnywhere

```bash
# Upload code (via git clone or web console)
# Create virtualenv
mkvirtualenv offertracker --python=python3.10
pip install -r requirements.txt

# Set env vars in PythonAnywhere Secrets tab:
#   TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME,
#   CRON_SECRET, GEMINI_API_KEY (if using AI),
#   AI_PROVIDER

# Upload credentials.json via web UI (Settings → Upload)
# Reload web app
```

### cron-job.org (24/7 automation)

```
URL: https://SachinKumarChaudhary.pythonanywhere.com/cron/gotjobalert_auto_2026
Schedule: Every 15 minutes
```

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

## 13. Known Issues

### Bugs

| Issue | Location | Severity | Detail |
|---|---|---|---|
| Hardcoded Gmail query | `webui.py:167` | Medium | String literal instead of `config.GMAIL_QUERY` |
| Missing `is:unread` | `webui.py:165-168` | Medium | Dedup works but adds API calls |
| WhatsApp unreliable | `notifier.py:48` | Low | CallMeBot gateways sometimes don't deliver API key |
| In-memory state | `webui.py:43-47` | Low | `last_run`, `last_count`, `log_buffer` lost on restart |

### Technical Debt

| Issue | Location | Description |
|---|---|---|
| Single-threaded scheduler | `webui.py:232` | One slow user poll delays others |
| Tokens on filesystem | `webui.py:82-84` | Not suitable for multi-instance |
| No rate limiting | `webui.py:464` | `/cron/` accessible to anyone with secret |
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

## 14. Appendix: Session Timeline

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

### Why Each Approach Was Chosen (and Rejected)

| Approach | Chosen Because | Rejected Because |
|---|---|---|
| **Flask (v1)** | Full control, lightweight, familiar | No UI, single-user, no AI parsing |
| **n8n** | Visual workflow, no-code, built-in integrations | Android tracing-stop bug kills Node.js threads |
| **Manus AI** | Autonomous, browser automation, "set and forget" | 300 credits/day insufficient for 672 polls/day |
| **Flask (v2)** | All previous learnings combined | — (final solution) |

### What I'd Do Differently

1. **Use `is:unread` in Gmail query** — prevents re-fetching already-seen emails
2. **Database instead of in-memory dicts** — SQLite for persistent state (last_run, logs)
3. **Async worker queue** — Celery or Redis queue instead of single-threaded scheduler
4. **Test Gmail OAuth earlier** — scope mismatch issues were caught late
5. **Skip WhatsApp CallMeBot** — Telegram-only is more reliable; WhatsApp adds complexity
6. **Better error handling** — per-email try/except could be more granular

---

*End of PROJECT_COMPLETE.md — generated 2026-06-11*
