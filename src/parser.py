from __future__ import annotations
import re
from datetime import datetime
from typing import Any

from src.models import JobApplication
from src.config import AI_PROVIDER, logger
from src.email_utils import extract_header, get_body_text, get_message_id
from src.ai import parse_email_with_ai


DATE_PATTERNS = [
    (re.compile(r"(\d{4}-\d{2}-\d{2})"), "%Y-%m-%d"),
    (re.compile(r"(\d{2}/\d{2}/\d{4})"), "%m/%d/%Y"),
    (re.compile(r"(\w+ \d{1,2},?\s*\d{4})"), "%B %d, %Y"),
]

INDIAN_COMPANIES = (
    r"TCS|Infosys|Wipro|HCL|Tech\s*Mahindra|LTI|Mindtree|Mphasis|Hexaware|Cognizant|CTS"
    r"|Capgemini|L&T\s*Infotech|LTIMindtree|Persistent|Coforge|LTI|Zoho|MakeMyTrip"
    r"|Freshworks|BrowserStack|Postman|Chargebee|Razorpay|Ola|Oyo|Swiggy|Zomato|Paytm"
    r"|PhonePe|Flipkart|Myntra|Nykaa|Urban\s*Company|Groww|Upstox|Zerodha|Unacademy"
    r"|BYJU'S|Vedantu|Physics\s*Wallah|UpGrad|Eruditus|Druva|Druva|Yellow\.ai|Observe\.ai"
    r"|Uniphore|Mad Street Den|Qure\.ai|Niki\.ai|Haptik|Bruno|Crozdesk"
    r"|Tata\s*Motors|Mahindra|Bajaj|Reliance|Aditya\s*Birla|ICICI|HDFC|Axis|Kotak|Yes\s*Bank"
    r"|SBI|Infosys|Wipro|LTI|Mphasis|HCL\s*Tech|Tech\s*Mahindra|Capgemini|Cognizant|Dell|Deloitte"
)

COMPANY_ALIASES = {
    "tcsrecruit": "TCS", "tcs": "TCS",
    "infosys": "Infosys", "wipro": "Wipro", "hcl": "HCL", "hcltech": "HCL",
    "techmahindra": "Tech Mahindra", "ltimindtree": "LTIMindtree",
    "cognizant": "Cognizant", "capgemini": "Capgemini",
    "accenture": "Accenture", "deloitte": "Deloitte",
    "pwc": "PwC", "ey": "EY", "kpmg": "KPMG",
    "mckinsey": "McKinsey", "bain": "Bain", "bcg": "BCG",
    "google": "Google", "microsoft": "Microsoft",
    "amazon": "Amazon", "meta": "Meta",
    "apple": "Apple", "netflix": "Netflix",
    "uber": "Uber", "airbnb": "Airbnb",
    "linkedin": "LinkedIn", "salesforce": "Salesforce",
    "adobe": "Adobe", "intel": "Intel", "ibm": "IBM",
    "oracle": "Oracle", "nvidia": "NVIDIA", "amd": "AMD",
    "cisco": "Cisco", "vmware": "VMware",
    "splunk": "Splunk", "twilio": "Twilio",
    "stripe": "Stripe", "shopify": "Shopify",
    "spotify": "Spotify", "tesla": "Tesla", "dell": "Dell",
    "zoho": "Zoho", "freshworks": "Freshworks",
    "razorpay": "Razorpay", "paytm": "Paytm",
    "flipkart": "Flipkart", "swiggy": "Swiggy",
    "zomato": "Zomato", "byjus": "BYJU'S",
    "unacademy": "Unacademy", "upgrad": "UpGrad",
    "zerodha": "Zerodha", "groww": "Groww",
    "phonepe": "PhonePe", "myntra": "Myntra", "nykaa": "Nykaa",
    "sbi": "SBI", "icici": "ICICI", "hdfc": "HDFC",
    "axis": "Axis Bank", "kotak": "Kotak", "barclays": "Barclays",
    "goldmansachs": "Goldman Sachs", "jpmorgan": "JPMorgan",
    "morganstanley": "Morgan Stanley", "citi": "Citi",
    "bofa": "Bank of America", "jpmc": "JPMorgan Chase",
    "reliance": "Reliance", "tata": "Tata", "mahindra": "Mahindra",
    "bajaj": "Bajaj", "adityabirla": "Aditya Birla",
    "coforge": "Coforge", "persistent": "Persistent",
    "lntinfotech": "L&T Infotech", "hexaware": "Hexaware",
    "mphasis": "Mphasis", "mindtree": "Mindtree",
}

STOP_WORDS = {"at", "in", "the", "a", "an", "for", "with", "and", "or", "to", "of", "is", "on", "by", "as", "it"}


def extract_company_from_address(sender: str) -> str:
    match = re.search(r"@([\w-]+)\.", sender)
    if not match:
        return "Unknown"
    domain = match.group(1).lower().strip("-")
    domain = domain.replace("-", "")
    return COMPANY_ALIASES.get(domain, domain.title())


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

    known = rf"(?:at|with|for)\s+(Google|Microsoft|Amazon|Meta|Apple|Netflix|Stripe|Spotify|Uber|Airbnb|Twitter|LinkedIn|Salesforce|Adobe|Intel|IBM|Oracle|Tesla|SpaceX|Shopify|Reddit|Pinterest|Snapchat|Dropbox|Notion|Figma|Palantir|Datadog|Snowflake|Cloudflare|Nvidia|AMD|Intel|Goldman\s*Sachs|JPMorgan|Morgan\s*Stanley|Citi|Bank\s*of\s*America|Deloitte|McKinsey|BCG|Accenture|PwC|EY|KPMG|Cisco|Vmware|Splunk|Twilio|Square|Robinhood|Coinbase|OpenAI|Anthropic|DeepMind|{INDIAN_COMPANIES})\b"

    patterns = [
        known,
        r"(?:Hiring|hiring|walk[- ]?in|off[- ]?campus|recruitment|placement)\s+(?:drive\s+(?:by|for|at)\s+)?([A-Z][A-Za-z0-9\s&.]+?)(?:\s+(?:is|for|drive|internship|program|programme|\n|\.|,|$))",
        r"([A-Z][A-Za-z0-9\s&.]+?)\s+(?:Off\s*Campus|Walk[- ]?In|Hiring|Recruitment)\s+Drive",
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
        r"((?:Product|UX|UI|Graphic|Marketing|Technical|Business|Management)"
        r"(?:\s+(?:Manager|Designer|Writer|Analyst|Consultant|Associate|Trainee))"
        r"(?:\s?\w*Intern)?)"
    )
    indian_roles = (
        r"(Graduate\s*(Engineer\s*)?Trainee|GET|Fresher|Trainee\s*(Engineer|Developer)"
        r"|Associate\s*(Software|Developer|Engineer|Consultant)?"
        r"|Software\s*Engineer\s*Trainee|Systems\s*Engineer\s*Trainee"
        r"|Junior\s*(Software|Developer|Engineer|Associate)"
        r"|Engineer\s*Trainee|Management\s*Trainee)"
    )
    patterns = [keyword, known, known2]
    patterns.insert(0, indian_roles)

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

    if re.search(r"regret\s+to\s+inform|unfortunately|not\s+moving\s+forward|rejected|after\s+careful\s+review|has\s+been\s+filled|will\s+not\s+be\s+(?:moving|proceeding)|thank\s+you\s+for\s+(?:your\s+)?interest|not\s+selected|unsuccessful", text_lower):
        return "rejection"
    if re.search(r"offer\s+letter|offer\s+of|letter\s+of\s+offer|internship\s+offer|offer\s+of\s+employment|offer\s+released|congratulations.*offer|we\s+are\s+pleased\s+to\s+offer|you\s+are\s+hired", text_lower):
        return "offer_letter"
    if re.search(r"(?:technical|onsite|round\s*\d|panel|in[- ]?person|virtual\s+onsite)\s+interview|coding\s+(?:round|interview|session)|system\s+design|whiteboard|pair\s+programming", text_lower):
        return "technical_interview"
    if re.search(r"interview|invitation\s+to|schedule\s+(?:an|a)\s+interview|shortlisted|shortlist|we\s+would\s+like\s+to\s+meet|next\s+(?:round|step|stage)", text_lower):
        return "interview_invitation"
    if re.search(r"phone\s+(?:screen|call|interview|discussion)|video\s+screen|preliminary\s+call|quick\s+chat|introductory\s+call", text_lower):
        return "phone_screen"
    if re.search(r"walk[- ]?in\s+(?:drive|interview)", text_lower):
        return "interview_invitation"
    if re.search(r"coding\s+test|assessment|hackerrank|hackerearth|test\s+invitation|online\s+test|aptitude|technical\s+test", text_lower):
        return "assessment"
    if re.search(r"application\s+received|thank\s+you\s+for\s+applying|we\s+received\s+your\s+application|application\s+confirmation|application\s+has\s+been\s+received|off[- ]?campus\s+drive|hiring\s+alert|opening|opportunity|we\s+are\s+hiring|job\s+alert", text_lower):
        return "application_received"

    return "other"


def quick_is_job_email(subject: str, body: str) -> bool:
    text = f"{subject}\n{body}".lower()
    keywords = (
        r"offer\s*letter|interview|application|hiring|recruit"
        r"|job\s*alert|opportunity|position|role\s+at|appl(y|ied)"
        r"|shortlist|assessment|coding\s*test|hackerrank|hackerearth"
        r"|walk[- ]?in|off[- ]?campus|placement|internship"
        r"|congratulations|we\s+(?:are|'re)\s+hiring|job\s+opening"
        r"|vacanc|talent|join\s+(?:our|the|us)|career"
        r"|thank\s+you\s+for\s+(?:your\s+)?(?:interest|applying)"
        r"|graduate\s+(?:engineer\s+)?trainee|fresher|engineer\s+trainee"
    )
    return bool(re.search(keywords, text))


def parse_email(msg: dict[str, Any]) -> JobApplication | None:
    subject = extract_header(msg, "Subject") or ""
    sender = extract_header(msg, "From") or ""
    body = get_body_text(msg) or ""
    message_id = get_message_id(msg)
    internal_date = datetime.fromtimestamp(int(msg.get("internalDate", 0)) / 1000)

    if not subject:
        logger.warning("Email has no subject, skipping")
        return None

    if quick_is_job_email(subject, body):
        ai_result = parse_email_with_ai(subject, sender, body)
    else:
        ai_result = None

    if isinstance(ai_result, dict) and ai_result:
        company_name = ai_result.get("company_name", "").strip() or extract_company(subject, body, sender)
        job_role = ai_result.get("job_role", "").strip() or extract_role(subject, body)
        email_type = ai_result.get("email_type", "other")
        location = ai_result.get("location", "")
        salary = ai_result.get("salary", "")
        summary = ai_result.get("summary", "")
        next_step = ai_result.get("next_step", "")

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
        parser_name = {"gemini": "Gemini", "groq": "Groq", "nvidia": "NVIDIA"}.get(AI_PROVIDER, "AI")
    else:
        company_name = extract_company(subject, body, sender)
        job_role = extract_role(subject, body)
        email_type = classify_email_type(subject, body)
        location = ""
        salary = ""
        summary = ""
        next_step = ""
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
        location=location,
        salary=salary,
        summary=summary,
        next_step=next_step,
        parser=parser_name,
    )
