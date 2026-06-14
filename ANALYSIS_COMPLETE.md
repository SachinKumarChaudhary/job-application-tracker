# Codebase Analysis — Gotjobalert

> Generated: 2026-06-14
> Project: `/sdcard/Gotjobalert`

---

## 1. Project Stats

| Metric | Value |
|--------|-------|
| Total lines (source) | 3,863 |
| Python files | 13 (active: 7, dead: 5 to delete, poller.py: partial) |
| HTML templates | 3 (index: 599, dashboard: 248, change_channel: 200) |
| Test files | 2 (14 tests, all passing) |
| Other | wsgi.py, .env.example, requirements.txt, n8n artifacts (archival) |
| Live | https://SachinKumarChaudhary.pythonanywhere.com/ |
| GitHub | https://github.com/SachinKumarChaudhary/job-application-tracker |

## 2. Active Files (What Actually Runs)

### webui.py (1,249 lines) — Main Flask App
- **Routes:** 18 (index, auth, callback, logout, save-prefs, trigger, verify-telegram, change-channel, dedup-sheet, format-sheet, send-test-email, status, logs, cron/<secret>, automation-status, test-notification, save-whatsapp-apikey, save-timezone, download-contacts, export-xlsx, upload-credentials, fix-sheet)
- **OAuth:** Multi-user per-user token files (`credentials/token_<base64(email)>.json`)
- **Scheduler:** Daemon thread `scheduler_loop()` polls all users every 15 min
- **Sheets:** In-place updates with priority-based progression (rejection→offer)
- **State:** Volatile in-memory dicts (`last_run`, `last_count`, `last_error`, `log_buffer`) — notif_log persisted to JSON
- **Key pattern:** `_get_dashboard_context()` → shared context builder wrapped in try/except everywhere

### src/config.py (62 lines) — Configuration
- Loads `.env` via `python-dotenv`
- Exports: logging, paths, API keys, feature flags
- **Issue:** Exports `TOKEN_PATH` (line 11) — single-user misleading export

### src/parser.py (283 lines) — Email Parser
- **Two-pass pipeline:** `quick_is_job_email()` regex filter → AI (Gemini/Groq/NVIDIA) → regex fallback
- **8-stage classifier:** rejection, offer_letter, technical_interview, interview_invitation, phone_screen, assessment, application_received, other
- **COMPANY_ALIASES:** 65+ domain→canonical name mappings
- **INDIAN_COMPANIES:** 70+ Indian company names
- Imports from `src/poller.py`: `extract_header`, `get_body_text`, `get_message_id` (only 3 helpers needed)

### src/notifier.py (243 lines) — 7 Notification Channels
- Telegram (3-URL fallback chain: CF Worker → HTTPS → HTTP)
- Slack webhook
- Discord webhook
- WhatsApp CallMeBot
- WhatsApp Cloud API (Meta)
- Twilio WhatsApp
- Pushover
- ntfy.sh
- **Issue:** `http://api.telegram.org` (no TLS) in fallback chain — line 53

### src/ai.py (134 lines) — AI Provider Dispatcher
- `_call_gemini()` — Gemini API via HTTP POST
- `_call_groq()` — Groq API (OpenAI-compatible)
- `_call_nvidia()` — NVIDIA API (OpenAI-compatible)
- `_clean_json()` — Strip markdown fences, extract JSON object
- `parse_email_with_ai()` — Truncates inputs to 500/200/2000 chars, formats prompt

### src/models.py (88 lines) — Pydantic Models
- `JobApplication` — 13 fields, validators, `to_sheet_row()`, `to_alert_text()`
- `EMAIL_TYPE_EMOJI`, `EMAIL_TYPE_LABEL`, `NEXT_STEP_EMOJI` — display maps

### src/poller.py (85 lines) — **Half Dead**
- **Used:** `extract_header()`, `get_body_text()`, `get_message_id()` — 3 shared helpers
- **Dead:** `get_gmail_service()` (single-user), `fetch_unread_messages()` (no `is:unread`), `mark_as_read()` (duplicated in webui.py)

## 3. Dead Files (To Delete)

| File | Lines | Why Dead |
|------|-------|----------|
| `src/main.py` | 61 | Single-user OfferTracker — replaced by webui.py multi-user |
| `src/scheduler.py` | 43 | Standalone signal-handler scheduler — replaced by webui.py daemon thread |
| `src/sheets_writer.py` | 47 | gspread-based single-user writer — replaced by webui.py raw Sheets API calls |
| `src/duplicate_checker.py` | 27 | Single-user dedup — replaced by webui.py per-user known_ids set |
| `src/setup_oauth.py` | 37 | Headless OAuth setup — replaced by webui.py browser OAuth flow |

## 4. Critiques

### Critical

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| 1 | **5 dead files** | `src/main.py`, `scheduler.py`, `sheets_writer.py`, `duplicate_checker.py`, `setup_oauth.py` | All single-user code, completely unreferenced by webui.py. Confusing dead weight. |
| 2 | **poller.py half dead** | `src/poller.py` | Only 3 helper functions used by parser.py. Rest is dead single-user code. |
| 3 | **Misleading TOKEN_PATH** | `src/config.py:11` | Exports a single-user token path. webui.py uses per-user base64-encoded paths. New devs will copy the wrong pattern. |
| 4 | **Non-TLS URL** | `src/notifier.py:53` | `http://api.telegram.org` in fallback chain. If HTTPS fails, HTTP won't succeed either. Security smell. |

### High

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| 5 | **Test coverage gap** | `webui.py` (0), `notifier.py` (0), `ai.py` (0) | 1,626 lines of core logic with zero tests. Only parser + models tested (12 tests). |
| 6 | **Duplicated pipeline** | `webui.py:363` vs `webui.py:462` | `send_test_email()` and `run_poll()` implement the same fetch→parse→dedup→sheets→notify→mark-read flow independently. Maintenance trap. |
| 7 | **Side effects in getter** | `webui.py:86-104` | `get_user_email()` renames token files, migrates prefs, mutates global dicts. Name suggests a simple accessor. |
| 8 | **Volatile state** | `webui.py:51-55` | `last_run`, `last_count`, `last_error`, `log_buffer` are plain dicts lost on restart. PA free tier sleeps between cron pings. |

### Medium

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| 9 | **Hardcoded sheet ID 0** | `webui.py:276-348` | `format_sheet()` uses `"sheetId": 0`. Breaks if sheet tab renamed or sheet reorganized. |
| 10 | **No dedup cache** | `webui.py:498-502` | `known_ids` rebuilt from full column F on every poll. Wasteful API calls. |
| 11 | **Inconsistent catching** | Multiple locations | Some handlers log message only, others chain `traceback.format_exc()`. Debugging inconsistency. |

### Low

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| 12 | **Fragile heuristic** | `webui.py:1127` | `_is_msg_id()` checks `startswith("<")` to detect Message-IDs. The entire `fix_sheet` route exists because of past column shifts — schema evolution debt. |
| 13 | **Old bug in dead code** | `poller.py:18` | `fetch_unread_messages()` queries Gmail without `is:unread` despite being named "unread". Unfixed because never called. |

## 5. Dependency Graph

```
webui.py ──→ src/config (env vars, logger)
         ──→ src/models (EMAIL_TYPE_LABEL)
         ──→ src/notifier (notify_single)
         ──→ src/parser (parse_email) [lazy import inside loop]

src/parser.py ──→ src/models (JobApplication)
            ──→ src/config (AI_PROVIDER, logger)
            ──→ src/poller (extract_header, get_body_text, get_message_id)
            ──→ src/ai (parse_email_with_ai)

src/notifier.py ──→ src/config (all env vars, logger)

src/ai.py ──→ src/config (AI_PROVIDER, API keys, logger)
```

## 6. Next Steps (Prioritized)

### Phase 1 — Dead Code Cleanup
1. Delete `src/main.py`, `src/scheduler.py`, `src/sheets_writer.py`, `src/duplicate_checker.py`, `src/setup_oauth.py`
2. Create `src/email_utils.py` with `extract_header()`, `get_body_text()`, `get_message_id()`
3. Update `src/parser.py` imports → `from src.email_utils import ...`
4. Delete `src/poller.py`
5. Remove `TOKEN_PATH` from `src/config.py`
6. Remove `http://api.telegram.org` from `src/notifier.py:53`

### Phase 2 — Fixes
7. Standardize all `except Exception:` to log tracebacks consistently
8. Fix `format_sheet()` to resolve sheet name instead of hardcoded ID 0

### Phase 3 — Documentation
9. Update `README.md` — remove dead files from components table, update line counts
10. Update `PROJECT_REFERENCE.md` — remove dead file references, update session history (Session 14-15)
11. Update `PROJECT_COMPLETE.md` — same

### Phase 4 — Deploy & Push
12. Upload changed files to PythonAnywhere via PA API
13. Reload web app
14. `git add -A && git commit -m "cleanup: remove 5 dead legacy files, fix error handling"`
15. `git push`

### Phase 5 — MemCore
16. Auto-triggers on commit — verify `.selflearn-context.md` is regenerated
