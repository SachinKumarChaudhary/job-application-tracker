from __future__ import annotations

from typing import Any
from google.oauth2.credentials import Credentials
import gspread

from src.config import SHEET_NAME, TOKEN_PATH, logger


SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/gmail.modify"]

HEADERS = [
    "Company Name", "Job Role", "Application Date",
    "Email Subject", "Sender Email", "Message ID", "Alert Sent",
    "Email Type", "Summary",
]


class SheetsHelper:
    def __init__(self):
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        gc = gspread.authorize(creds)
        self._sheet = gc.open(SHEET_NAME).sheet1
        self._ensure_headers()

    def _ensure_headers(self) -> None:
        existing = self._sheet.row_values(1)
        if existing != HEADERS:
            logger.info("Setting sheet headers")
            self._sheet.insert_row(HEADERS, 1)

    def read_all_rows(self) -> list[list[str]]:
        return self._sheet.get_all_values()

    def append_row(self, row: list[str]) -> int:
        self._sheet.append_row(row)
        row_count = len(self._sheet.get_all_values())
        logger.info(f"Appended row {row_count}: {row[0]} - {row[1]}")
        return row_count

    def row_has_message_id(self, message_id: str) -> bool:
        try:
            col_f = self._sheet.col_values(6)
            return message_id in col_f
        except Exception:
            return False
