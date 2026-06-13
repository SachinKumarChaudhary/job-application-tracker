from __future__ import annotations

import requests

from src.config import (
    TELEGRAM_BOT_TOKEN, PUSHOVER_TOKEN, PUSHOVER_USER, logger,
    WHATSAPP_CLOUD_PHONE_NUMBER_ID, WHATSAPP_CLOUD_ACCESS_TOKEN,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM,
)


def send_pushover(message: str, user_key: str = "") -> None:
    token = PUSHOVER_TOKEN
    if not token:
        logger.debug("Pushover not configured (no app token), skipping")
        return
    if not user_key:
        user_key = PUSHOVER_USER
    if not user_key:
        logger.debug("Pushover not configured (no user key), skipping")
        return
    try:
        resp = requests.post("https://api.pushover.net/1/messages.json", data={
            "token": token,
            "user": user_key,
            "message": message,
        }, timeout=10)
        resp.raise_for_status()
        logger.info(f"Pushover notification sent to {user_key[:8]}...")
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


def _send_telegram(bot_token: str, chat_id: str, message: str) -> None:
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"Telegram DM sent to {chat_id}")
    except Exception as e:
        logger.warning(f"Telegram notification failed: {e}")


def _send_slack_webhook(webhook_url: str, message: str) -> None:
    try:
        resp = requests.post(webhook_url, json={"text": message}, timeout=10)
        resp.raise_for_status()
        logger.info("Slack notification sent via webhook")
    except Exception as e:
        logger.warning(f"Slack webhook notification failed: {e}")


def _send_discord(webhook_url: str, message: str) -> None:
    try:
        resp = requests.post(webhook_url, json={"content": message}, timeout=10)
        resp.raise_for_status()
        logger.info("Discord notification sent via webhook")
    except Exception as e:
        logger.warning(f"Discord webhook notification failed: {e}")


def _send_whatsapp_callmebot(phone: str, apikey: str, message: str) -> None:
    try:
        import urllib.parse
        params = urllib.parse.urlencode({"phone": phone, "text": message, "apikey": apikey})
        resp = requests.get(
            f"https://api.callmebot.com/whatsapp.php?{params}",
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"WhatsApp notification sent to {phone}")
    except Exception as e:
        logger.warning(f"WhatsApp notification failed: {e}")


def _send_whatsapp_cloud(to_phone: str, message: str) -> None:
    if not WHATSAPP_CLOUD_PHONE_NUMBER_ID or not WHATSAPP_CLOUD_ACCESS_TOKEN:
        logger.warning("WhatsApp Cloud: missing PHONE_NUMBER_ID or ACCESS_TOKEN in .env")
        return
    try:
        resp = requests.post(
            f"https://graph.facebook.com/v22.0/{WHATSAPP_CLOUD_PHONE_NUMBER_ID}/messages",
            headers={
                "Authorization": f"Bearer {WHATSAPP_CLOUD_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {"body": message},
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"WhatsApp Cloud API: message sent to {to_phone}")
    except Exception as e:
        logger.warning(f"WhatsApp Cloud API notification failed: {e}")
        try:
            logger.warning(f"Response: {resp.text}")
        except Exception:
            pass


def _send_twilio_whatsapp(to_phone: str, message: str) -> None:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.warning("Twilio: missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in .env")
        return
    try:
        resp = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data={
                "From": TWILIO_WHATSAPP_FROM,
                "To": f"whatsapp:{to_phone}",
                "Body": message,
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"Twilio WhatsApp: message sent to {to_phone}")
    except Exception as e:
        logger.warning(f"Twilio WhatsApp notification failed: {e}")
        try:
            logger.warning(f"Response: {resp.text}")
        except Exception:
            pass


def notify_all(message: str) -> None:
    logger.info("Sending notifications (all channels) — notify_single used per-user from web UI")
    send_pushover(message)


def notify_single(channel: str | None, prefs: dict, message: str, email: str = "") -> None:
    if not channel:
        logger.debug("No notification channel configured, skipping")
        return
    logger.info(f"Sending {channel} notification for {email}")
    if channel == "slack":
        webhook_url = prefs.get("slack_webhook_url", "")
        if webhook_url:
            _send_slack_webhook(webhook_url, message)
        else:
            logger.warning("Slack: missing webhook_url")
    elif channel == "telegram":
        chat_id = prefs.get("telegram_chat_id", "")
        if chat_id and TELEGRAM_BOT_TOKEN:
            _send_telegram(TELEGRAM_BOT_TOKEN, chat_id, message)
        else:
            logger.warning("Telegram: missing chat_id or TELEGRAM_BOT_TOKEN")
    elif channel == "whatsapp":
        phone = prefs.get("whatsapp_phone", "")
        apikey = prefs.get("whatsapp_apikey", "")
        if phone and apikey:
            _send_whatsapp_callmebot(phone, apikey, message)
        else:
            logger.warning("WhatsApp: missing phone or apikey")
    elif channel == "discord":
        webhook_url = prefs.get("discord_webhook_url", "")
        if webhook_url:
            _send_discord(webhook_url, message)
        else:
            logger.warning("Discord: missing webhook_url")
    elif channel == "pushover":
        user_key = prefs.get("pushover_user_key", "")
        if user_key:
            send_pushover(message, user_key)
        else:
            logger.warning("Pushover: missing user_key")
    elif channel == "whatsapp_cloud":
        phone = prefs.get("whatsapp_cloud_phone", "")
        if phone:
            _send_whatsapp_cloud(phone, message)
        else:
            logger.warning("WhatsApp Cloud: missing phone number")
    elif channel == "twilio_whatsapp":
        phone = prefs.get("twilio_whatsapp_phone", "")
        if phone:
            _send_twilio_whatsapp(phone, message)
        else:
            logger.warning("Twilio WhatsApp: missing phone number")
