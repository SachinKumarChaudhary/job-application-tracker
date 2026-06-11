from __future__ import annotations

import requests

from src.config import (
    TELEGRAM_BOT_TOKEN, PUSHOVER_TOKEN, PUSHOVER_USER, logger,
)


def send_pushover(message: str) -> None:
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        logger.debug("Pushover not configured, skipping")
        return
    try:
        resp = requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message,
        }, timeout=10)
        resp.raise_for_status()
        logger.info("Pushover notification sent")
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


def _send_whatsapp_callmebot(phone: str, apikey: str, message: str) -> None:
    try:
        resp = requests.post(
            "https://api.callmebot.com/whatsapp.php",
            data={"phone": phone, "text": message, "apikey": apikey},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"WhatsApp notification sent to {phone}")
    except Exception as e:
        logger.warning(f"WhatsApp notification failed: {e}")


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
