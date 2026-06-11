import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"

GMAIL_QUERY = os.getenv("GMAIL_QUERY", 'subject:"application received" OR subject:"thank you for applying" OR subject:"application confirmation" OR subject:"offer letter" OR subject:"we received your application"')
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "15"))
SHEET_NAME = os.getenv("SHEET_NAME", "Job Application Tracker")

# ── Shared notification gateways ──
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")  # optional fallback for users without their own
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "GotJobAlert_bot")

# ── AI / LLM Provider (for email parsing, categorization, summarization) ──
AI_PROVIDER = os.getenv("AI_PROVIDER", "none")  # gemini | groq | nvidia | none
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN", "")
PUSHOVER_USER = os.getenv("PUSHOVER_USER", "")

CRON_SECRET = os.getenv("CRON_SECRET", "")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("offer_tracker")

def validate():
    missing = []
    if not CREDENTIALS_PATH.exists():
        missing.append(f"credentials.json not found at {CREDENTIALS_PATH}")
    if not TOKEN_PATH.exists():
        logger.warning("token.json not found — run setup.py first for first-time OAuth")
    if missing:
        for msg in missing:
            logger.error(msg)
        return False
    return True
