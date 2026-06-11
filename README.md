# Offer Tracker — Job Application Auto-Tracker

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/tests-11%20passing-brightgreen" alt="11 tests passing">
  <img src="https://img.shields.io/badge/hosting-PythonAnywhere%20(free)-purple" alt="PythonAnywhere Free">
  <img src="https://img.shields.io/badge/AI-Gemini%20%7C%20Groq%20%7C%20NVIDIA-orange" alt="AI Providers">
  <img src="https://img.shields.io/badge/cost-%240-brightgreen" alt="$0 budget">
</p>

> Automatically track job applications from Gmail — extracts company, role, and type via AI + regex, logs to Google Sheets, and sends real-time alerts to Telegram/Slack/WhatsApp. **Zero infrastructure cost.**

**For anyone applying to 50+ jobs:** stop manually logging applications. Connect your Gmail once, get a live spreadsheet and instant alerts.

---

## Quickstart

```bash
git clone https://github.com/yourusername/offer-tracker
cd offer-tracker
pip install -r requirements.txt
cp .env.example .env   # configure at least TELEGRAM_BOT_TOKEN
python webui.py        # runs at http://localhost:8080
```

**Live demo:** [https://SachinKumarChaudhary.pythonanywhere.com/](https://SachinKumarChaudhary.pythonanywhere.com/)

---

## Features

- **Multi-user Gmail OAuth** — each user connects their own Gmail, tokens are isolated
- **AI email parsing** — Gemini (free), Groq, or NVIDIA extracts company, role, date, type, summary
- **Regex fallback** — 50+ company patterns, 15+ role patterns, email type classifier (offer/rejection/interview/received)
- **Google Sheets logging** — auto-creates spreadsheet per user with typed columns
- **Multi-channel notifications** — Telegram DM, Slack webhook, WhatsApp (CallMeBot), Pushover
- **24/7 automation** — cron-job.org pings the app every 15 min, polls all users in one request
- **11 passing tests** — parser + model coverage
- **$0 hosting** — PythonAnywhere free tier handles the entire stack

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  cron-job   │────▶│  Flask App   │────▶│  Gmail API  │
│  (free)     │     │  (webui.py)  │     │  (3 users)  │
└─────────────┘     └──────┬───────┘     └──────┬──────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐     ┌─────────────┐
                    │  Gemini AI   │     │  Regex      │
                    │  (primary)   │────▶│  (fallback) │
                    └──────┬───────┘     └──────┬──────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐     ┌─────────────┐
                    │ Google Sheets│     │  Notifier   │
                    │  (free DB)   │     │  (TG/SL/WA) │
                    └──────────────┘     └─────────────┘
```

### Components

| Component | File | Role |
|---|---|---|
| **Flask app** | `webui.py` | OAuth, routes, scheduler loop, per-user token isolation |
| **Poller** | `src/poller.py` | Gmail API fetch, header extraction, body parsing |
| **Parser** | `src/parser.py` | Company/role extraction, email type classification |
| **AI layer** | `src/ai.py` | Gemini/Groq/NVIDIA API calls with JSON response parsing |
| **Models** | `src/models.py` | Pydantic `JobApplication` with sheet/alert formatting |
| **Notifier** | `src/notifier.py` | Telegram, Slack webhook, WhatsApp CallMeBot, Pushover |
| **Sheets** | `src/sheets_writer.py` | Google Sheets auto-create, append, dedup via Message-ID |
| **Dedup** | `src/duplicate_checker.py` | Message-ID cache to prevent duplicate processing |

---

## Configuration

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `TELEGRAM_BOT_USERNAME` | Yes | Bot username (users DM this to connect) |
| `CRON_SECRET` | Yes | Secret key in cron URL path |
| `GMAIL_QUERY` | No | Gmail search query (default: application/offer subjects) |
| `AI_PROVIDER` | No | `gemini`, `groq`, `nvidia`, or `none` (regex only) |
| `GEMINI_API_KEY` | Conditional | Required if `AI_PROVIDER=gemini` |
| `GROQ_API_KEY` | Conditional | Required if `AI_PROVIDER=groq` |
| `NVIDIA_API_KEY` | Conditional | Required if `AI_PROVIDER=nvidia` |
| `POLL_INTERVAL_MINUTES` | No | Poll interval (default: 15) |

---

## How It Works

1. **User signs in** with Google → OAuth grants Gmail + Sheets scope
2. **User chooses notification channel** — Telegram, Slack, or WhatsApp
3. **User sends a test email** to themselves with an application subject
4. **Scheduler polls Gmail** every 15 min — matches `subject:"application received" OR subject:"offer letter"...`
5. **Parser extracts** company, role, date, type:
   - AI path: Gemini/Groq/NVIDIA returns structured JSON
   - Regex path: 50+ company patterns, 15+ role patterns, keyword classifier
6. **Logs to Google Sheets** — auto-created spreadsheet with columns: Company, Role, Date, Type, Summary
7. **Sends notification** — Telegram DM / Slack message / WhatsApp text
8. **Marks as read** — email is removed from UNREAD to avoid re-processing

---

## Deployment

### PythonAnywhere (free)

```bash
# Upload code, set up venv
mkvirtualenv offertracker --python=python3.10
pip install -r requirements.txt

# Configure WSGI
# Edit /var/www/wsgi.py to point to /home/user/offer-tracker/wsgi.py

# Set env vars in PythonAnywhere dashboard
```

### cron-job.org (free 24/7)

Create a cron job that hits:
```
https://your-app.pythonanywhere.com/cron/your_secret
```
Every 15 minutes → polls all connected users.

---

## Testing

```bash
pytest -v
# 11 passed
```

---

## What I'd Do Differently

- **Use `is:unread` in Gmail query** — prevents re-processing already-seen emails
- **Add webhook verification** — Slack bot token needs `channels:read` scope
- **Replace WhatsApp CallMeBot** with Twilio or Telegram-only (CallMeBot is unreliable)
- **Add dashboard charts** — application trend, response rate, company breakdown
- **Handle token revocation** — detect when user revokes OAuth and prompt re-auth

---

## License

MIT
