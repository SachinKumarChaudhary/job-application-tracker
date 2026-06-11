from __future__ import annotations

from src.config import logger


class DuplicateChecker:
    def __init__(self, sheets_helper):
        self._sheets = sheets_helper
        self._known_ids: set[str] = set()

    def refresh(self) -> None:
        try:
            rows = self._sheets.read_all_rows()
            ids = set()
            for row in rows[1:]:
                if len(row) >= 6 and row[5].strip():
                    ids.add(row[5].strip())
            self._known_ids = ids
            logger.debug(f"Loaded {len(ids)} known Message-IDs from sheet")
        except Exception as e:
            logger.warning(f"Could not refresh duplicate cache: {e}")

    def is_duplicate(self, message_id: str) -> bool:
        return message_id in self._known_ids

    def add(self, message_id: str) -> None:
        self._known_ids.add(message_id)
