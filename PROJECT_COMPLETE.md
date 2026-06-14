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
8. [AI Migration & Sheet Formatting (Session 10)](#7b-ai-migration--sheet-formatting-session-10)
9. [Discord, Pipeline & Indian Market (Session 12)](#7c-session-12--discord-pipeline--indian-market-tuning-jun-12)
10. [Polish & Reliability + Test Notification Fix (Session 11)](#7d-polish--reliability-session-11)
11. [Telegram Relay, ntfy.sh & UI Polish (Session 14)](#7e-telegram-relay-ntfysh--ui-polish-session-14)

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

## 7b. AI Migration & Sheet Formatting (Session 10)

**[content unchanged through this section]**

## 7c. Session 12 — Discord, Pipeline, & Indian Market Tuning (Jun 12)

**Date:** June 12, 2026

### Discord Notifications

Added Discord as a notification channel (webhook-based, ~1 min setup):

- **Backend:** `_send_discord()` in `notifier.py` — POSTs JSON payload to Discord webhook URL
- **Channel routing:** `"discord"` added to `notify_single()` channel switch
- **Web UI:** Discord radio button in channel selector, Discord webhook URL field with how-to instructions, Discord section on dashboard (connected status, test/change buttons)
- **Validation:** URL must start with `https://discord.com/api/webhooks/`
- **Live on PA** after upload + reload

### In-Place Sheet Updates

Replaced always-append logic with intelligent in-place updates:

- **Before:** Every email created a new row — same application produced multiple rows
- **After:** `run_poll()` reads all existing rows, builds a `(company, role) → row_number` map
- **Status priority system:** Each email type gets a numeric priority:
  - `rejection` (1) → `other` (2) → `received` (3) → `assessment` (4) → `phone_screen` (5) → `interview` (6) → `tech_interview` (7) → `offer` (8)
- When a new email matches an existing company+role, it only updates the row if the **new priority > old priority** (progress, never regression)
- New entries with no existing match still append a fresh row

### Two-Pass AI Pipeline

Added `quick_is_job_email()` — a fast regex filter that runs **before** calling NVIDIA:

- Uses 15+ keyword patterns (offer letter, interview, application, hiring, walk-in, off-campus, etc.)
- Non-job emails skip the NVIDIA API call entirely — falls through to regex-only parsing
- Saves API credits and speeds up processing for spam/newsletter emails

### Alias-Based Company Matching

Added `COMPANY_ALIASES` dict (60+ mappings) to `parser.py`:

- Maps common ATS domains and company-specific domains to canonical names
- `@tcsrecruit.com` → "TCS", `@goldmansachs.com` → "Goldman Sachs", `@byjus.com` → "BYJU'S"
- Applied in `extract_company_from_address()` as the first-look fallback

### Full Status Pipeline — 8 Stages

Expanded the email type system from 5 to 8 pipeline stages:

| Stage | Emoji | Priority | Regex Keywords |
|---|---|---|---|
| `application_received` | 📋 | 3 | `application received`, `thank you for applying` |
| `assessment` | 📝 | 4 | `coding test`, `assessment`, `hackerrank` |
| `phone_screen` | 📞 | 5 | `phone screen`, `video screen`, `introductory call` |
| `interview_invitation` | 🎯 | 6 | `interview`, `schedule an interview`, `shortlisted` |
| `technical_interview` | 💻 | 7 | `technical interview`, `coding round`, `system design` |
| `offer_letter` | 🎉 | 8 | `offer letter`, `you are hired` |
| `rejection` | ❌ | 1 | `regret to inform`, `not moving forward` |

- AI prompt updated to recognize all 8 stages
- Dashboard shows pipeline progress bar (green gradient from received→offer, red for rejected)
- `classify_email_type()` regex updated with phone_screen and technical_interview detection

### WhatsApp CallMeBot — Dead

- Latest number `+34 644 59 90 43` — WhatsApp says "isn't on WhatsApp"
- User contacted `@callmebot_com` on Telegram (last seen within a month) — no response
- QuackAPI registration has internal error — deferred
- Slack webhook setup has "No channels" picker issue — needs workspace refresh

### File Structure Changes

| File | Lines (Session 12) | Key Changes |
|---|---|---|
| `webui.py` | 860 | Discord save-prefs, in-place update logic in `run_poll()`, `STATUS_PRIORITY` 8 stages |
| `src/notifier.py` | +10 | `_send_discord()`, `"discord"` in `notify_single()` |
| `src/parser.py` | 238 | `quick_is_job_email()`, `COMPANY_ALIASES`, updated `classify_email_type()` |
| `src/ai.py` | 134 | Updated prompt with pipeline stages, phone_screen, technical_interview |
| `src/models.py` | 86 | `phone_screen` 📞, `technical_interview` 💻 in EMAIL_TYPE_EMOJI/LABEL |
| `templates/index.html` | 764 | Discord setup UI, pipeline progress bar, updated badge rendering |

## 7d. Session 11 — Polish & Reliability (Jun 13)

**Date:** June 13, 2026

### Frontend Fixes

**Material Symbols restored:** Re-added Google Fonts CDN link with all axes (`FILL@0..1`). Restored `.material-symbols-outlined` CSS class with `font-family`, `font-feature-settings: 'liga'`, and `font-variation-settings`.

**Briefcase icon → description:** The original `briefcase` ligature didn't render on the user's device. Replaced with `description` (document icon) for both the Entries tab and login page icon.

**Theme toggle restored:** Uses `dark_mode`/`light_mode` Material Symbols ligatures (had been removed during earlier cleanup).

**Nav tab fill restored:** JavaScript logic for `font-variation-settings: 'FILL' 1` on the active navigation tab was re-added.

**"None" channel fix:** When user selects no notification channel, the app now saves `notification_channel: "none"` instead of deleting the key entirely. A "Notifications disabled" card appears in the Alerts tab for this state.

### Backend Fixes

**Email normalization:** Added `normalize_email()` function that lowercases and strips dots before `@gmail.com` (Google ignores dots in usernames). Applied to:
- `get_user_email()` — normalizes session email, migrates old unnormalized prefs/tokens
- `get_user_prefs()` — falls back to unnormalized key search if normalized key not found
- `set_user_pref()` — merges old unnormalized prefs into normalized key
- `get_creds()` — renames old token files to normalized path

**Callback redirect:** Changed the "Session expired" error render in the OAuth callback to `redirect("/")` — prevents an error screen when the browser replays the callback URL.

**Cache-Control headers:** Added `@app.after_request` handler that sets `Cache-Control: no-store` on all responses, preventing the callback URL from being cached by the browser.

**Test notification dispatches all channels:** The `test_notification` route previously only handled `slack`, `telegram`, and `whatsapp` (CallMeBot). `discord`, `whatsapp_cloud`, `twilio_whatsapp`, and `pushover` silently did nothing. Fixed by replacing the hand-rolled channel dispatch with `notify_single()` from `src/notifier.py` (which handles all 8 channels). Also handled the JSON/HTML split: the Home tab uses HTMX (expects HTML), the Alerts tab buttons call `testNotification()` JS (expects JSON).

**Visible action feedback:** `send_test_email_route`, `trigger`, and `test_notification` now pass `alert_message` to the dashboard template. Errors and successes appear as a colored banner at the top of the dashboard instead of being silently swallowed into logs.

### File Structure Changes

| File | Lines (Session 11) | Key Changes |
|---|---|---|
| `webui.py` | ~915 | `normalize_email()`, updated `get_user_email()`, `get_user_prefs()`, `set_user_pref()`, `get_creds()`, `save_prefs_route`, callback redirect, `@app.after_request` Cache-Control handler, `notify_single()` replaces hand-rolled dispatch, `alert_message` feedback on all action routes |
| `templates/index.html` | ~780 | Restored Material Symbols CDN, CSS classes, font-variation-settings JS; replaced briefcase→description; restored theme toggle ligatures; `testNotification()` JS handles `d.message` + `d.error` for JSON responses |
| `templates/_dashboard.html` | ~335 | "Notifications disabled" card for `none` channel in Alerts tab; `alert_message` banner at top of dashboard |

## 7e. Session 14 — Telegram Relay, ntfy.sh & UI Polish (Jun 14)

**Date:** June 14, 2026

### Cloudflare Telegram Relay

PythonAnywhere free tier blocks `api.telegram.org`. Fixed via a permanent Cloudflare Worker relay:
- Worker source: `telegram_worker.js` — accepts `POST /relay` with `{chat_id, text, parse_mode}`, proxies to Telegram Bot API
- URL: `https://telegram-relay.sachin-gotjobalert.workers.dev/relay`
- `notifier.py` updated: `_TELEGRAM_RELAY_URL` points to worker instead of direct API

### ntfy.sh Replaces Pushover

Pushover requires a one-time $4.99 purchase per device. Replaced with ntfy.sh (free, open source, no account needed):
- `_send_ntfy()` added to `notifier.py` — posts to `https://ntfy.sh/{topic}`
- `notify_single()` handles `ntfy` case
- `change_channel.html`: ntfy card with step-by-step setup instructions
- `send_pushover()` kept in `notifier.py` for backward compatibility

### WhatsApp Feature-Flagged Off

WhatsApp CallMeBot is dead for new users (bot full). Added `WHATSAPP_ENABLED` flag:
- `config.py`: reads `WHATSAPP_ENABLED` from env, defaults to `False`
- UI: WhatsApp cards hidden when flag is off
- WhatsApp Cloud API / Twilio WhatsApp removed from UI (no server-side env vars either)

### Timezone Support

Dates now display in user-configurable timezone (default IST):
- `localize_datetime()` using `zoneinfo.ZoneInfo`
- `/save-timezone` route + selector in Settings tab
- Defaults to `Asia/Kolkata`

### Notification Log Persistence

Previously `notif_log` was in-memory only — lost on every PythonAnywhere restart:
- Added `load_notif_log()` and `save_notif_log()` functions
- `NOTIF_LOG_PATH` constant (`user_notif_log.json`)
- Loaded on startup, saved after each notification
- Keeps last 100 entries per user

### Alert Banner Auto-Dismiss

**Root cause:** Every button uses `outerHTML=h` to update the dashboard. Browsers do **not** execute `<script>` tags parsed from `outerHTML`/`innerHTML`. The inline script in `_dashboard.html` was silently discarded, so the banner never auto-dismissed.

**Fix:** Replaced inline `<script>` with a polling loop in `index.html`:
- `setInterval(handleBanner, 500)` checks for `#alert-banner` every 500ms
- On detection: 3s timer → fade out (opacity + translateY) → remove → prepend "Dashboard" entry to `#notif-log-list`
- Works with any DOM update mechanism (initial load, `outerHTML`, `innerHTML`, HTMX)
- `#notif-log-list` container always rendered even when empty; empty state (`#notif-log-empty`) hidden via JS on first entry

### File Structure Changes

| File | Key Changes |
|---|---|
| `webui.py` | `load_notif_log()`, `save_notif_log()`, `NOTIF_LOG_PATH`, `log_notif()` now saves to JSON; `/save-timezone` route; removed dead channel routes/save endpoints |
| `templates/_dashboard.html` | Removed inline `<script>`; added `data-msg`/`data-icon`/`data-status` attributes to `#alert-banner`; `#notif-log-list` always rendered; `#notif-log-empty` separate div |
| `templates/index.html` | Added `initAlertDismiss()` polling loop; added `switchTab('alerts')` imported from global scope |
| `templates/change_channel.html` | Rebuilt with Telegram/ntfy/Slack/Discord cards; step-by-step setup instructions; pre-filled inputs from prefs |
| `src/notifier.py` | `_TELEGRAM_RELAY_URL` points to Cloudflare Worker; `_send_ntfy()` added; WhatsApp channels guarded by `WHATSAPP_ENABLED`; `ntfy` case in `notify_single()` |
| `src/config.py` | `WHATSAPP_ENABLED` flag (reads from env, defaults to `False`) |
| `telegram_worker.js` | New file — Cloudflare Worker Telegram relay |

### Bugs Fixed

| Issue | Fix |
|---|---|
| `api.telegram.org` blocked on PA free tier | Cloudflare Worker relay |
| Pushover costs $4.99 | Replaced with ntfy.sh (free) |
| Alert banner never auto-dismissed (inline script silent in outerHTML) | Polling in index.html |
| Notification log lost on restart | JSON persistence |
| Notif-log container missing when empty | Always-rendered #notif-log-list |

## 8. Architecture (Final)

### System Diagram

> **Visual version:** See `assets/architecture.svg` — 7-color scheme, pill labels, drop shadows.
> Also: `assets/how-it-works.svg` (user flow), `assets/hero-banner.svg` (README banner), `assets/badges.svg` (custom dark badges).

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
                    │   NVIDIA AI        │     │   Regex Parser      │
                    │  (primary parse)   │────▶│  (fallback)         │
                    └────────┬───────────┘     └──────────┬──────────┘
                             │                            │
                             ▼                            ▼
                    ┌────────────────────┐     ┌─────────────────────┐
                    │ Google Sheets      │     │   Notifier          │
                    │ (per-user, auto)   │     │ Telegram/Slack/WA   │
                    └────────────────────┘     └─────────────────────┘
```

### Data Flow (one poll cycle — Session 13 update)

```
Gmail API ──fetch 20 matching emails──► Poller
    │
    ▼
quick_is_job_email() ──regex filter──► skip if non-job (no AI wasted)
    │
    ▼
Parser ──try AI first──► NVIDIA ──JSON──► Parser
    │                                │
    │         if AI fails/skipped    │
    └─────regex fallback─────────────┘
    │
    ▼
Validator ──is company_name valid?──► skip if not
    │
    ▼
In-place check ──company+role in sheet?──► UPDATE row if new status > old
    │                                            (progress never regression)
    └── if no match ──► APPEND new row A-M
    │
    ▼
Notifier ──send alert──► Telegram / Discord / Slack / Pushover
    │
    ▼
Mark Read ──remove UNREAD label──► Gmail
```

### Components Summary

| Component | File | Lines | Role |
|---|---|---|---|---|
| Flask app | `webui.py` | ~900 | Routes, OAuth, scheduler, per-user polling, sheet formatting, in-place updates, pipeline status priority, email normalization, Cache-Control |
| Poller | `src/poller.py` | 85 | Gmail fetch, header extraction, body decode |
| Parser | `src/parser.py` | 238 | Company/role extraction, type classification (8 stages), AI integration, quick_is_job_email filter, COMPANY_ALIASES (60+), Indian market tuning |
| AI layer | `src/ai.py` | 134 | NVIDIA/Gemini/Groq API calls (two-pass: quick filter → AI) |
| Models | `src/models.py` | 86 | Pydantic JobApplication (13 fields), 8 email types with emojis |
| Notifier | `src/notifier.py` | 99 | Telegram/Slack/WhatsApp/Pushover/Discord |
| Sheets | `src/sheets_writer.py` | 47 | Google Sheets CRUD |
| Dedup | `src/duplicate_checker.py` | 27 | Message-ID cache |
| Scheduler | `src/scheduler.py` | 43 | Standalone CLI daemon |
| HTML UI | `templates/index.html` | ~780 | Dashboard + prefs + logs + pipeline progress bar + Material Symbols |
| Dashboard partial | `templates/_dashboard.html` | ~20 | "Notifications disabled" card for `none` channel |

---

## 9. File-by-File Breakdown

### Entry Points

| File | Lines | Role |
|---|---|---|
| `webui.py` | ~900 | Flask app — routes, OAuth, scheduler, per-user polling, sheet formatting, email normalization, Cache-Control, in-place updates, pipeline status priority |
| `wsgi.py` | 11 | PythonAnywhere WSGI bridge |

### Source Modules (`src/`)

| File | Lines | Role |
|---|---|---|
| `config.py` | 52 | Env var loading, logging setup, constants, validation |
| `main.py` | 61 | `OfferTracker` class — orchestrates one poll cycle |
| `poller.py` | 85 | Gmail API fetch, header extraction, body decode, mark-as-read |
| `parser.py` | 183 | Email parsing — company/role extraction, type classification, date parsing |
| `ai.py` | 129 | AI provider abstraction — Gemini, Groq, NVIDIA API calls |
| `models.py` | 82 | Pydantic `JobApplication` model — validation, sheet rows (13 cols), alert text |
| `notifier.py` | 89 | Multi-channel notification dispatch |
| `sheets_writer.py` | 47 | Google Sheets CRUD — auto-create, append, dedup |
| `duplicate_checker.py` | 27 | Message-ID dedup cache |
| `scheduler.py` | 43 | Standalone scheduler daemon (CLI mode) |
| `setup_oauth.py` | — | One-time OAuth setup script |

### Web Layer

| File | Lines | Role |
|---|---|---|
| `templates/index.html` | ~780 | Single-page HTML/JS app — dashboard, prefs, logs, Material Symbols, pipeline progress bar |
| `templates/_dashboard.html` | ~20 | Dashboard partial — status cards, alerts, "Notifications disabled" card for `none` channel |

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
| `README.md` | ~9K | Quickstart, custom SVG badges, hero banner, architecture, config, deployment |
| `CASE_STUDY.md` | 46K | Narrative case study for hiring managers |
| `PROJECT_REFERENCE.md` | 25K | Standalone technical reference |
| `PROJECT_COMPLETE.md` | — | This file — single A-Z reference |
| `docs/n8n-workflow.md` | 5.5K | n8n workflow breakdown, code, why rejected |
| `docs/DEVICE_ARCHITECTURE.md` | 3K | Device hardware, OS, env spec |
| `docs/linkedin-post-strategy.md` | 4K | LinkedIn viral post strategy (2026 algorithm) |
| `GITHUB.md` | 1K | Public Git info for contributors |

### Visual Assets

| File | Size | Purpose |
|---|---|---|
| `assets/hero-banner.svg` | 3K | Dark gradient banner — title, tagline, stat badges |
| `assets/badges.svg` | 4K | Custom dark-themed SVG badges (license, python, tests, hosting, AI, cost) |
| `assets/architecture.svg` | 8K | Full system architecture diagram — 7-color scheme, pill labels, shadows |
| `assets/how-it-works.svg` | 4K | Visual flow: User → OAuth → Gmail → Parser → Sheets + Alerts |

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
| GET | `/format-sheet` | Beautify Google Sheet (header style, banding, borders, auto-resize) |

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

**Email type classification — keyword detection (8 pipeline stages):**

| Type | Priority | Keywords |
|---|---|---|
| `rejection` | 1 | `regret to inform`, `unfortunately`, `not moving forward`, `rejected` |
| `other` | 2 | Everything else |
| `application_received` | 3 | `application received`, `thank you for applying`, `we received` |
| `assessment` | 4 | `coding test`, `assessment`, `hackerrank`, `hackerearth`, `online test` |
| `phone_screen` | 5 | `phone screen`, `video screen`, `introductory call`, `quick chat` |
| `interview_invitation` | 6 | `interview`, `invitation to`, `schedule an interview`, `shortlisted` |
| `technical_interview` | 7 | `technical interview`, `coding round`, `system design`, `pair programming` |
| `offer_letter` | 8 | `offer letter`, `offer of`, `internship offer`, `you are hired` |

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
    ├── quick_is_job_email()  ← Two-pass filter before AI
    │   └── if false: skip AI call, fall through to regex
    ├── if job-related: try parse_email_with_ai()
    │   └── if AI returns valid dict:
    │       ├── company = AI result or regex fallback
    │       ├── role = AI result or regex fallback
    │       ├── email_type = AI result
    │       ├── summary = AI result
    │       ├── date = AI date or regex date or internal_date
    │       └── parser = "AI"
    └── else (AI not configured or failed or non-job email):
        ├── company = extract_company()  ← uses COMPANY_ALIASES for domain→name
        ├── role = extract_role()
        ├── email_type = classify_email_type()  ← 8 pipeline stages
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

### Discord (next best — webhook-based, no setup friction)

**User setup:**
1. Select Discord in preferences
2. Open Discord → Server Settings → Integrations → Create Webhook
3. Name it "Offer Tracker", pick a channel, copy webhook URL
4. Paste URL in preferences → Save

**Technical:**
- Uses Discord webhook URL per user (no bot token needed)
- URL format: `https://discord.com/api/webhooks/...`
- Messages sent as JSON `{"content": "..."}` via POST
- Dashboard shows webhook status, test notification button, change/reset

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
- **Known issue:** "No channels" picker when creating webhook — needs workspace refresh at api.slack.com

### WhatsApp (CallMeBot — DEPRECATED / DEAD)

**⚠️ CallMeBot no longer works — numbers are banned within hours of activation. Latest number +34 644 59 90 43 not on WhatsApp.**

**Original setup (no longer functional):**
1. Select WhatsApp in preferences, enter phone number
2. Tap activation link → opens WhatsApp → send "I allow CallMeBot" to gateway number
3. CallMeBot replies with API key → paste in app

**Technical:**
- Uses `api.callmebot.com/whatsapp.php` with phone + apikey + text
- Known issue: API key delivery is unreliable (gateway numbers sometimes don't respond)
- Gateway numbers: `+34 644 64 60 89`, `+34 623 78 64 49`, `+34 644 03 87 31`, `+34 644 59 90 43` — all dead

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
| `AI_PROVIDER` | `nvidia` | `nvidia` (primary), `gemini`, `groq`, `none` |
| `AI_MODEL` | `meta/llama-3.1-70b-instruct` | Model name for provider |
| `GEMINI_API_KEY` | — | Required if `AI_PROVIDER=gemini` (was deprecated — 429 errors) |
| `GROQ_API_KEY` | — | Required if `AI_PROVIDER=groq` |
| `NVIDIA_API_KEY` | — | Required if `AI_PROVIDER=nvidia` (currently active) |

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

### Recently Fixed

| Issue | Fix | Session |
|---|---|---|
| Briefcase icon didn't render on user's device | Replaced `briefcase` ligature with `description` (document icon) — renders reliably across all devices | 11 |
| Browser caching OAuth callback URL caused "Session expired" on viewport retoggle | Added `@app.after_request` handler setting `Cache-Control: no-store` on all responses; changed error render to `redirect("/")` | 11 |
| Test Notification button silently did nothing for discord/whatsapp_cloud/twilio/pushover | Replaced hand-rolled channel dispatch with `notify_single()` — handles all 8 channels | 11 |
| Alerts tab Test buttons gave "Error sending test" toast | Route now returns JSON for `fetch()` calls, HTML for HTMX calls | 11 |
| No visible feedback on Check Now / Send Test Email / Test Notification | Added `alert_message` context variable + colored banner in dashboard template | 11 |
| Telegram blocked on PythonAnywhere free tier | Deployed Cloudflare Worker relay — `telegram_worker.js` proxies to `api.telegram.org` | 14 |
| Alert banner never auto-dismissed | Inline `<script>` in `outerHTML` partial response doesn't execute; replaced with `setInterval` polling in `index.html` | 14 |
| Notification log lost on app restart | Added `load_notif_log()` / `save_notif_log()` — persists to `user_notif_log.json` | 14 |
| Notif-log container missing when empty | Always render `#notif-log-list` div; empty state is a separate `#notif-log-empty` div that JS hides on first entry | 14 |
| Pushover costs $4.99/purchase | Replaced with ntfy.sh (free, no account needed); `send_pushover()` kept for backward compat | 14 |

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

| Feature | Priority | Status | Description |
|---|---|---|---|
| Dashboard charts | Medium | ❌ Not started | Application trends, response rates, company breakdown |
| CSV/Excel export | Low | ✅ Done | `/export-xlsx` endpoint + Download XLSX button |
| AI categorization | Low | ✅ Done | Auto-tag by industry, role level, location (via NVIDIA AI summary) |
| Parser accuracy | Medium | ✅ Done | Indian job market: 60+ companies, off-campus/walk-in, fresher/GET roles |
| Multi-language | Low | ❌ Not started | Parse Hindi, Spanish emails via AI |
| In-place sheet updates | High | ✅ Done | Company+role matching, priority-based status pipeline (8 stages) |
| Two-pass AI pipeline | Medium | ✅ Done | `quick_is_job_email()` filter before NVIDIA call |
| Alias matching | Medium | ✅ Done | `COMPANY_ALIASES` (60+ ATS domain→canonical name mappings) |
| Discord notifications | Medium | ✅ Done | Webhook-based, ~1 min setup |
| Full status pipeline | Medium | ✅ Done | 8 stages: received→assessment→phone_screen→interview→tech→offer |

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
| **10** | Jun 11-12 | ~Evening | AI migration Gemini→NVIDIA, sheet format beautification, OAuth scope fix, 13-col schema |
| **11** | Jun 13 | ~Morning → Afternoon | Frontend polish — Material Symbols restored, briefcase→description icon, theme toggle ligature fix, nav fill JS restored, "none" channel card. Backend — email normalization, Cache-Control headers, callback redirect fix, `notify_single()` replaces hardcoded channel dispatch (fixes Test Notification for discord/whatsapp_cloud/twilio/pushover), visible error banner on all action buttons |
| **12** | Jun 12 | ~Morning | Visual overhaul — custom SVG badges, hero banner, architecture diagram (7-color), how-it-works flow, designer skill created |
| **13** | Jun 12 | ~Evening | Discord notifications, in-place sheet updates, two-pass AI pipeline, alias matching (60+), full status pipeline (8 stages), WhatsApp deprecated, Indian market tuning |
| **14** | Jun 14 | ~Afternoon | Cloudflare Telegram relay (PA blocks api.telegram.org), ntfy.sh channel (replaces Pushover), WhatsApp feature-flagged off, timezone selector, notif_log JSON persistence, alert banner auto-dismiss (3s fade + alerts log), polling replaces MutationObserver for banner detection |

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
| H | Email Type | Classifier (8 stages: Received/Assessment/Phone Screen/Interview/Tech Interview/Offer/Rejected/Other) |
| I | Summary | AI generated (2-3 sentence description) |
| J | Location | AI extracted (e.g., "Bangalore, India") |
| K | Salary | AI extracted (e.g., "$120k/yr", "₹12 LPA") |
| L | Next Step | AI classified (interview/offer/follow_up/waiting/rejected/none) |
| M | Parser | Provider name ("NVIDIA", "Gemini", "Groq", "Regex") |

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
| **NVIDIA over Gemini** | Gemini hit 429 rate limits (project-level quota); NVIDIA (`meta/llama-3.1-70b-instruct`) works without rate limiting |
| **AI primary + regex fallback** | AI is more accurate (company/role/location/salary/next_step) but regex works when API is down |
| **Parser stores provider name** | Column M stores "NVIDIA"/"Gemini"/"Groq"/"Regex" — enables auditing which parser processed each entry |
| **cron-job.org over in-app scheduler** | PythonAnywhere free tier sleeps; external ping wakes it |
| **Single HTML file (no JS framework)** | Zero build step; deployable as-is; works without npm |
| **Base64-encoded token filenames** | Safe for filesystem (no @ or / in filenames); reversible for debugging |

| **Discord over WhatsApp** | Webhook-based (no phone number, no verification, no rate limits); WhatsApp CallMeBot numbers get banned within hours |
| **In-place updates over always-append** | Same application emails no longer create duplicate rows; priority system prevents status regression |
| **Two-pass AI pipeline** | Quick regex filter before NVIDIA call saves API credits on non-job emails (spam, newsletters) |
| **COMPANY_ALIASES for domain normalization** | `extract_company_from_address()` now maps ATS/company domains to canonical names instead of raw title-case |
| **8-stage pipeline instead of 5** | Separate phone_screen, assessment, and technical_interview stages give more granular status tracking |
| **Pipeline progress bar in dashboard** | Users can visually see where each application stands without opening the sheet |
| **Email normalization (dots + case)** | Gmail ignores dots and case in usernames, so `normalize_email()` lowercases and strips dots before `@gmail.com` to prevent duplicate user entries and token file mismatches |
| **Cache-Control: no-store on all responses** | Prevents browser from caching the OAuth callback URL; replaying a cached callback was causing spurious "Session expired" errors |
| **Theme toggle always available** | Light/dark toggle uses `dark_mode`/`light_mode` Material Symbols ligatures that render on all devices; avoids ligature-dependent icon bugs |

---

*End of PROJECT_COMPLETE.md — single-file A-Z reference covering history, architecture, every file, endpoints, parser internals, OAuth flow, config, deployment, testing, known issues, and appendices. Generated 2026-06-14 (Updated: Session 14 — Telegram relay, ntfy.sh, notif_log persistence, alert banner auto-dismiss).*
