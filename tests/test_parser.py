"""
Sample test emails for parser testing.
"""
from datetime import datetime
from unittest.mock import patch
from src.parser import (
    parse_email, extract_company_from_address, parse_date,
    quick_is_job_email, classify_email_type, COMPANY_ALIASES,
)


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


@patch("src.parser.parse_email_with_ai", return_value=None)
def test_parse_simple_email(mock_ai):
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


@patch("src.parser.parse_email_with_ai", return_value=None)
def test_parse_thank_you_email(mock_ai):
    msg = make_mock_msg(
        subject="Thank you for applying to Stripe!",
        sender="jobs@stripe.com",
        body="Thank you for your interest in the Backend Engineer Intern role at Stripe.",
    )
    app = parse_email(msg)
    assert app is not None
    assert "Stripe" in app.company_name
    assert "Backend Engineer Intern" in app.job_role or "Backend Engineer" in app.job_role or "Engineer Intern" in app.job_role


@patch("src.parser.parse_email_with_ai", return_value=None)
def test_parse_company_from_subject(mock_ai):
    msg = make_mock_msg(
        subject="We received your application for Data Scientist at Microsoft",
        sender="no-reply@microsoft.com",
        body="Thank you for applying.",
    )
    app = parse_email(msg)
    assert app is not None
    assert "Microsoft" in app.company_name


@patch("src.parser.parse_email_with_ai", return_value=None)
def test_parse_unknown_company_falls_back_to_domain(mock_ai):
    msg = make_mock_msg(
        subject="Application received",
        sender="hr@some-startup.io",
        body="Thanks for applying!",
    )
    app = parse_email(msg)
    assert app is not None
    assert "Some" in app.company_name or "Startup" in app.company_name


@patch("src.parser.parse_email_with_ai", return_value=None)
def test_duplicate_message_id(mock_ai):
    msg = make_mock_msg(
        subject="Software Engineer at Netflix",
        sender="jobs@netflix.com",
        body="We received your application for the Software Engineer position at Netflix.",
    )
    app = parse_email(msg)
    assert app is not None
    assert app.message_id == "<test123@mail>"


@patch("src.parser.parse_email_with_ai", return_value=None)
def test_date_in_body(mock_ai):
    msg = make_mock_msg(
        subject="Application Received",
        sender="hr@meta.com",
        body="Dear Candidate,\n\nApplication Date: 2025-06-08\nPosition: Software Engineer at Meta\n\nThank you.",
    )
    app = parse_email(msg)
    assert app is not None
    assert app.application_date.strftime("%Y-%m-%d") == "2025-06-08"


def test_quick_is_job_email():
    assert quick_is_job_email("Application Received: Google", "Thanks") is True
    assert quick_is_job_email("Offer Letter from Amazon", "We are pleased") is True
    assert quick_is_job_email("Interview Invitation", "Schedule") is True
    assert quick_is_job_email("Your order confirmation", "Order #123") is False
    assert quick_is_job_email("Weekly newsletter", "Tips and tricks") is False
    assert quick_is_job_email("", "hello world") is False


def test_company_aliases():
    assert extract_company_from_address("no-reply@tcs.com") == "TCS"
    assert extract_company_from_address("hr@infosys.com") == "Infosys"
    assert extract_company_from_address("jobs@byjus.com") == "BYJU'S"
    assert extract_company_from_address("careers@zoho.com") == "Zoho"
    assert extract_company_from_address("hello@unknown-startup.io") == "Unknownstartup"


def test_classify_email_type_pipeline():
    assert classify_email_type("regret to inform you", "") == "rejection"
    assert classify_email_type("congratulations, you are hired!", "") == "offer_letter"
    assert classify_email_type("Technical Interview Round 2", "") == "technical_interview"
    assert classify_email_type("phone screen invitation", "") == "phone_screen"
    assert classify_email_type("coding assessment", "") == "assessment"
    assert classify_email_type("interview schedule", "") == "interview_invitation"
    assert classify_email_type("application received", "") == "application_received"
    assert classify_email_type("random spam email", "") == "other"
