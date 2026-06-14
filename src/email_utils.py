from __future__ import annotations
import base64
from typing import Any


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
