"""
Sample test emails for parser testing.
"""
from datetime import datetime
from src.parser import parse_email, extract_company_from_address, parse_date


def make_mock_msg(subject, sender, body, date_str=None):
    import time
    mock_time = "1717800000000"
    return {
        "id": "test123",
        "internalDate": mock_time,
        "payload": {
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": sender},
                {"name": "Message-ID", "value": "<test123@mail>"},
            ],
            "mimeType": "text/plain",
            "body": {
                "data": __import__("base64").urlsafe_b64encode(body.encode()).decode()
            },
        },
    }


def test_extract_company_from_domain():
    assert extract_company_from_address("no-reply@google.com") == "Google"
    assert extract_company_from_address("hr@microsoft.com") == "Microsoft"
    assert extract_company_from_address("jobs@stripe.com") == "Stripe"


def test_parse_date_iso():
    result = parse_date("2025-06-08")
    assert result is not None
    assert result.strftime("%Y-%m-%d") == "2025-06-08"


def test_parse_simple_email():
    msg = make_mock_msg(
        subject="Application Received: Software Engineer at Google",
        sender="no-reply@google.com",
        body="Dear Candidate,\n\nWe have received your application for the Software Engineer position at Google.\n\nThank you.",
    )
    app = parse_email(msg)
    assert app is not None
    assert "Google" in app.company_name
    assert "Software Engineer" in app.job_role
    assert app.sender_email == "no-reply@google.com"
    assert hasattr(app, "email_type")
    assert hasattr(app, "summary")


def test_parse_thank_you_email():
    msg = make_mock_msg(
        subject="Thank you for applying to Stripe!",
        sender="jobs@stripe.com",
        body="Thank you for your interest in the Backend Engineer Intern role at Stripe.",
    )
    app = parse_email(msg)
    assert app is not None
    assert "Stripe" in app.company_name
    assert "Backend Engineer Intern" in app.job_role or "Backend Engineer" in app.job_role or "Engineer Intern" in app.job_role


def test_parse_company_from_subject():
    msg = make_mock_msg(
        subject="We received your application for Data Scientist at Microsoft",
        sender="no-reply@microsoft.com",
        body="Thank you for applying.",
    )
    app = parse_email(msg)
    assert app is not None
    assert "Microsoft" in app.company_name


def test_parse_unknown_company_falls_back_to_domain():
    msg = make_mock_msg(
        subject="Application received",
        sender="hr@some-startup.io",
        body="Thanks for applying!",
    )
    app = parse_email(msg)
    assert app is not None
    assert app.company_name == "Some-Startup" or "Some" in app.company_name


def test_duplicate_message_id():
    msg = make_mock_msg(
        subject="Software Engineer at Netflix",
        sender="jobs@netflix.com",
        body="We received your application for the Software Engineer position at Netflix.",
    )
    app = parse_email(msg)
    assert app is not None
    assert app.message_id == "<test123@mail>"


def test_date_in_body():
    msg = make_mock_msg(
        subject="Application Received",
        sender="hr@meta.com",
        body="Dear Candidate,\n\nApplication Date: 2025-06-08\nPosition: Software Engineer at Meta\n\nThank you.",
    )
    app = parse_email(msg)
    assert app is not None
    assert app.application_date.strftime("%Y-%m-%d") == "2025-06-08"
