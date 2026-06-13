from datetime import datetime
from src.models import JobApplication


def test_minimal_job_application():
    app = JobApplication(
        company_name="Google",
        job_role="Software Engineer Intern",
        application_date=datetime(2025, 6, 8),
        email_subject="Your application has been received",
        sender_email="no-reply@google.com",
        message_id="<abc123@mail.gmail.com>",
    )
    assert app.company_name == "Google"
    assert app.job_role == "Software Engineer Intern"
    assert "@" in app.sender_email


def test_to_sheet_row():
    app = JobApplication(
        company_name="Google",
        job_role="SWE Intern",
        application_date=datetime(2025, 6, 8),
        email_subject="Received",
        sender_email="hr@google.com",
        message_id="<id@mail>",
    )
    row = app.to_sheet_row()
    assert len(row) == 13
    assert row[0] == "Google"
    assert row[2] == "2025-06-08"
    assert row[6] == "Yes"
    assert row[7] == "Other"
    assert row[8] == ""


def test_to_alert_text():
    app = JobApplication(
        company_name="Google",
        job_role="SWE Intern",
        application_date=datetime(2025, 6, 8),
        email_subject="Received",
        sender_email="hr@google.com",
        message_id="<id@mail>",
    )
    text = app.to_alert_text()
    assert "Google" in text
    assert "SWE Intern" in text
    assert "2025-06-08" in text
    assert "📬" in text
    assert "Other" in text
