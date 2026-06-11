from __future__ import annotations

from typing import Any

from src.config import logger, validate
from src.poller import get_gmail_service, fetch_unread_messages, extract_header, mark_as_read
from src.parser import parse_email
from src.duplicate_checker import DuplicateChecker
from src.sheets_writer import SheetsHelper
from src.notifier import notify_all


class OfferTracker:
    def __init__(self):
        self._sheets = SheetsHelper()
        self._dedup = DuplicateChecker(self._sheets)
        self._gmail = None

    def _ensure_gmail(self) -> Any:
        if self._gmail is None:
            self._gmail = get_gmail_service()
        return self._gmail

    def run_once(self) -> int:
        logger.info("Starting poll cycle")

        if not validate():
            logger.warning("Configuration incomplete, skipping cycle")
            return 0

        self._dedup.refresh()
        service = self._ensure_gmail()
        raw_messages = fetch_unread_messages(service)

        new_count = 0
        for msg in raw_messages:
            try:
                message_id = extract_header(msg, "Message-ID") or ""
                if self._dedup.is_duplicate(message_id):
                    logger.debug(f"Skipping duplicate: {message_id}")
                    mark_as_read(service, msg["id"])
                    continue

                app = parse_email(msg)
                if app is None:
                    logger.debug("Could not parse email, marking as read")
                    mark_as_read(service, msg["id"])
                    continue

                self._sheets.append_row(app.to_sheet_row())
                self._dedup.add(app.message_id)
                notify_all(app.to_alert_text())
                mark_as_read(service, msg["id"])
                new_count += 1
                logger.info(f"Processed: {app.company_name} - {app.job_role}")

            except Exception as e:
                logger.error(f"Failed to process message {msg.get('id', '?')}: {e}")

        logger.info(f"Cycle complete — {new_count} new applications logged")
        return new_count
