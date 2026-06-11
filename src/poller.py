from __future__ import annotations
import base64
from typing import Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from src.config import GMAIL_QUERY, TOKEN_PATH, logger


def get_gmail_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), ["https://www.googleapis.com/auth/gmail.modify"])
    return build("gmail", "v1", credentials=creds)


def fetch_unread_messages(service: Any) -> list[dict[str, Any]]:
    try:
        results = service.users().messages().list(
            userId="me",
            q=GMAIL_QUERY,
            maxResults=20,
        ).execute()

        messages = results.get("messages", [])
        if not messages:
            logger.debug("No matching emails found")
            return []

        full_messages = []
        for msg in messages:
            full = service.users().messages().get(
                userId="me", id=msg["id"], format="full"
            ).execute()
            full_messages.append(full)

        logger.info(f"Fetched {len(full_messages)} matching emails")
        return full_messages

    except Exception as e:
        logger.error(f"Failed to fetch emails: {e}")
        return []


def extract_header(msg: dict[str, Any], name: str) -> str:
    headers = msg.get("payload", {}).get("headers", [])
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def get_message_id(msg: dict[str, Any]) -> str:
    return extract_header(msg, "Message-ID") or extract_header(msg, "Message-Id") or ""


def get_body_text(msg: dict[str, Any]) -> str:
    payload = msg.get("payload", {})
    parts = payload.get("parts") or [payload]

    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        if "parts" in part:
            result = get_body_text(part)
            if result:
                return result

    data = payload.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return ""


def mark_as_read(service: Any, msg_id: str) -> None:
    try:
        service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
    except Exception as e:
        logger.warning(f"Failed to mark message {msg_id} as read: {e}")
