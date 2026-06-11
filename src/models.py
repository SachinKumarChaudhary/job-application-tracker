from datetime import datetime
from pydantic import BaseModel, field_validator


EMAIL_TYPE_EMOJI = {
    "offer_letter": "🎉",
    "interview_invitation": "🎯",
    "application_received": "📋",
    "rejection": "❌",
    "other": "📬",
}

EMAIL_TYPE_LABEL = {
    "offer_letter": "Offer Letter",
    "interview_invitation": "Interview",
    "application_received": "Received",
    "rejection": "Rejected",
    "other": "Other",
}


class JobApplication(BaseModel):
    company_name: str
    job_role: str
    application_date: datetime
    email_subject: str
    sender_email: str
    message_id: str
    email_type: str = "other"
    summary: str = ""
    parser: str = "Regex"

    @field_validator("company_name", "job_role")
    @classmethod
    def not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty")
        return stripped

    def to_sheet_row(self) -> list[str]:
        return [
            self.company_name,
            self.job_role,
            self.application_date.strftime("%Y-%m-%d"),
            self.email_subject,
            self.sender_email,
            self.message_id,
            "Yes",
            EMAIL_TYPE_LABEL.get(self.email_type, self.email_type),
            self.summary,
            self.parser,
        ]

    def to_alert_text(self) -> str:
        emoji = EMAIL_TYPE_EMOJI.get(self.email_type, "📬")
        label = EMAIL_TYPE_LABEL.get(self.email_type, "Update")
        lines = [
            f"{emoji} *{label}!*",
            f"Company: {self.company_name}",
            f"Role: {self.job_role}",
            f"Date: {self.application_date.strftime('%Y-%m-%d')}",
        ]
        if self.summary:
            lines.append(f"\n{self.summary}")
        lines.append(f"\nLogged to Google Sheets.")
        return "\n".join(lines)
