from __future__ import annotations
import re
from datetime import datetime
from typing import Any

from src.models import JobApplication
from src.config import logger
from src.poller import extract_header, get_body_text, get_message_id
from src.ai import parse_email_with_ai


DATE_PATTERNS = [
    (re.compile(r"(\d{4}-\d{2}-\d{2})"), "%Y-%m-%d"),
    (re.compile(r"(\d{2}/\d{2}/\d{4})"), "%m/%d/%Y"),
    (re.compile(r"(\w+ \d{1,2},?\s*\d{4})"), "%B %d, %Y"),
]

STOP_WORDS = {"at", "in", "the", "a", "an", "for", "with", "and", "or", "to", "of", "is", "on", "by", "as", "it"}


def extract_company_from_address(sender: str) -> str:
    match = re.search(r"@([\w-]+)\.", sender)
    return match.group(1).title() if match else "Unknown"


def parse_date(text: str) -> datetime | None:
    for pattern, fmt in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            try:
                return datetime.strptime(match.group(1), fmt)
            except ValueError:
                continue
    return None


def extract_company(subject: str, body: str, sender: str) -> str:
    domain_company = extract_company_from_address(sender)

    patterns = [
        r"(?:at|with)\s+(Google|Microsoft|Amazon|Meta|Apple|Netflix|Stripe|Spotify|Uber|Airbnb|Twitter|LinkedIn|Salesforce|Adobe|Intel|IBM|Oracle|Tesla|SpaceX|Shopify|Reddit|Pinterest|Snapchat|Dropbox|Notion|Figma|Palantir|Datadog|Snowflake|Cloudflare|Nvidia|AMD|Intel|Goldman\s*Sachs|JPMorgan|Morgan\s*Stanley|Citi|Bank\s*of\s*America|Deloitte|McKinsey|BCG|Accenture|PwC|EY|KPMG|Cisco|Vmware|Splunk|Twilio|Square|Robinhood|Coinbase|OpenAI|Anthropic|DeepMind)\b",
        r"(?:at|for|with)\s+(?:the\s|a\s|an\s)?([A-Z][A-Za-z0-9\s&.]+?)(?:\s+(?:is|we|the|position|role|job|internship|program|programme|intern|\.|,|\n)|$)",
        r"Company[:\s]\s*(.+)",
    ]

    for source in [subject, body]:
        for pattern in patterns:
            match = re.search(pattern, source, re.I)
            if match:
                result = match.group(1).strip()
                result = re.sub(r'^(?:the|a|an)\s+', '', result, flags=re.I).strip()
                if len(result) > 50:
                    return domain_company
                return result

    return domain_company


STOP_WORDS_ROLE = {"at", "in", "the", "a", "an", "for", "with", "and", "or", "to", "of", "is"}


def extract_role(subject: str, body: str) -> str:
    keyword = (
        r"(Frontend|Backend|Full[- ]?Stack|DevOps|MLOps|Site[- ]?Reliability)"
        r"(?:\s+(?:Engineer|Developer|Intern)){0,2}"
    )
    known = (
        r"((?:Software|Data|ML|QA|iOS|Android|Security|Systems|Research|Solutions|Platform|Cloud)"
        r"(?:\s+(?:Engineer|Developer|Scientist|Architect))"
        r"(?:\s+Intern)?)"
    )
    known2 = (
        r"((?:Product|UX|UI|Graphic|Marketing|Technical|Business)"
        r"(?:\s+(?:Manager|Designer|Writer|Analyst|Consultant|Associate))"
        r"(?:\s+Intern)?)"
    )
    patterns = [keyword, known, known2]

    extra = [
        r"Offer\s+Letter\s*\|\s*([^|]+)",
        r"Application(?:\s+received)?[:\s-]+(.+?)(?:\s*–|\s*-|\n|$)",
        r"Programme?\s+in\s+(.+?)(?:\s*–|\s*-|\n|$)",
    ]
    patterns.extend(extra)

    for source in [subject, body]:
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, source, re.I)
            if match:
                if i < 3:
                    role = match.group(0).strip()
                else:
                    role = match.group(1).strip()
                role = role.strip("*| ").strip()
                if role.lower() in STOP_WORDS_ROLE:
                    continue
                if len(role) < 2:
                    continue
                return role

    fallback = [
        r"(?:position|role|job title|applying for)[:\s]+(.+?)(?:\.|,|\n|$)",
        r"(?:for the|for a|as an?|an?)\s+(.+?)(?:\s+(?:at|position|role|job|internship|with|\.|,|\n)|$)",
    ]
    for source in [subject, body]:
        for pattern in fallback:
            match = re.search(pattern, source, re.I)
            if match:
                role = match.group(1).strip()
                if role.lower() not in STOP_WORDS_ROLE and len(role) >= 2:
                    return role

    return "Unknown Position"


def classify_email_type(subject: str, body: str) -> str:
    text_lower = f"{subject}\n{body}".lower()

    if re.search(r"regret\s+to\s+inform|unfortunately|not\s+moving\s+forward|rejected|after\s+careful\s+review|has\s+been\s+filled|will\s+not\s+be\s+(?:moving|proceeding)", text_lower):
        return "rejection"
    if re.search(r"offer\s+letter|offer\s+of|letter\s+of\s+offer|internship\s+offer|offer\s+of\s+employment", text_lower):
        return "offer_letter"
    if re.search(r"interview|invitation\s+to|schedule\s+(?:an|a)\s+interview", text_lower):
        return "interview_invitation"
    if re.search(r"application\s+received|thank\s+you\s+for\s+applying|we\s+received\s+your\s+application|application\s+confirmation|application\s+has\s+been\s+received", text_lower):
        return "application_received"

    return "other"


def parse_email(msg: dict[str, Any]) -> JobApplication | None:
    subject = extract_header(msg, "Subject") or ""
    sender = extract_header(msg, "From") or ""
    body = get_body_text(msg) or ""
    message_id = get_message_id(msg)
    internal_date = datetime.fromtimestamp(int(msg.get("internalDate", 0)) / 1000)

    if not subject:
        logger.warning("Email has no subject, skipping")
        return None

    ai_result = parse_email_with_ai(subject, sender, body)

    if isinstance(ai_result, dict) and ai_result:
        company_name = ai_result.get("company_name", "").strip() or extract_company(subject, body, sender)
        job_role = ai_result.get("job_role", "").strip() or extract_role(subject, body)
        email_type = ai_result.get("email_type", "other")
        summary = ai_result.get("summary", "")

        ai_date = ai_result.get("date")
        if ai_date:
            try:
                parsed_date = datetime.strptime(ai_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                parsed_date = None
        else:
            parsed_date = None

        app_date = parsed_date or parse_date(subject + "\n" + body) or internal_date

        logger.info(f"AI parsed: {company_name} - {job_role} [{email_type}]")
        parser_name = "AI"
    else:
        company_name = extract_company(subject, body, sender)
        job_role = extract_role(subject, body)
        email_type = classify_email_type(subject, body)
        summary = ""
        parser_name = "Regex"

        parsed_date = parse_date(subject + "\n" + body)
        app_date = parsed_date if parsed_date else internal_date

    return JobApplication(
        company_name=company_name,
        job_role=job_role,
        application_date=app_date,
        email_subject=subject,
        sender_email=sender,
        message_id=message_id,
        email_type=email_type,
        summary=summary,
        parser=parser_name,
    )
