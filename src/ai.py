from __future__ import annotations

import json
import re
from typing import Any

import requests

from src.config import (
    AI_PROVIDER, AI_MODEL, GEMINI_API_KEY, GROQ_API_KEY, NVIDIA_API_KEY,
    logger,
)

AI_PARSE_PROMPT = """You are an email parser for a job application tracker.
Extract the following fields from the email and return ONLY valid JSON (no markdown, no backticks):

{{
  "company_name": "string (the company name, capitalized properly)",
  "job_role": "string (the job title/role; e.g. 'Software Engineer', 'Graduate Trainee', 'Fresher')",
  "date": "string (application date in YYYY-MM-DD format, or null if unknown)",
  "email_type": "string (one of: offer_letter, technical_interview, interview_invitation, phone_screen, assessment, application_received, rejection, other)",
  "location": "string (office location, city, or 'Remote' if mentioned; e.g. 'Bengaluru', 'Hyderabad', 'Remote'; empty string if unknown)",
  "salary": "string (salary or stipend mentioned; e.g. '₹50,000/mo', '₹12 LPA', '$120k/yr', '6 LPA + benefits'; empty if unknown)",
  "summary": "string (2-3 sentence summary including key details like team, tech stack, deadlines, walk-in dates, off-campus drive details)",
  "next_step": "string (one of: 'interview', 'offer', 'follow_up', 'waiting', 'rejected', 'none')"
}}

For Indian job emails: 'off-campus drive' → application_received, 'walk-in drive' → interview_invitation,
'assessment/test' → assessment, 'hiring alert/opening' → application_received.
Pipeline stages (low to high): received → assessment → phone_screen → interview → technical_interview → offer.
For phone screening invitations use phone_screen. For technical/onsite/coding rounds use technical_interview.

Email Subject: {subject}
From: {sender}
Body: {body}"""


def _clean_json(text: str) -> Any:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    brace = text.find("{")
    if brace >= 0:
        text = text[brace:]
        end = text.rfind("}")
        if end >= 0:
            text = text[:end+1]
    return json.loads(text)


def _call_gemini(prompt: str) -> dict[str, Any] | None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{AI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    try:
        resp = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = _clean_json(text)
        if not isinstance(result, dict):
            logger.warning(f"Gemini returned non-dict: {type(result).__name__} = {result!r}")
            return None
        return result
    except Exception as e:
        logger.warning(f"Gemini AI call failed: {e}")
        return None


def _call_groq(prompt: str) -> dict[str, Any] | None:
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": AI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return _clean_json(text)
    except Exception as e:
        logger.warning(f"Groq AI call failed: {e}")
        return None


def _call_nvidia(prompt: str) -> dict[str, Any] | None:
    try:
        resp = requests.post(
            f"https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": AI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return _clean_json(text)
    except Exception as e:
        logger.warning(f"NVIDIA AI call failed: {e}")
        return None


def parse_email_with_ai(subject: str, sender: str, body: str) -> dict[str, Any] | None:
    if AI_PROVIDER == "none" or AI_PROVIDER == "":
        return None

    safe_subject = subject[:500].replace("{", "{{").replace("}", "}}")
    safe_sender = sender[:200].replace("{", "{{").replace("}", "}}")
    safe_body = body[:2000].replace("{", "{{").replace("}", "}}")
    prompt = AI_PARSE_PROMPT.format(subject=safe_subject, sender=safe_sender, body=safe_body)

    if AI_PROVIDER == "gemini":
        return _call_gemini(prompt)
    elif AI_PROVIDER == "groq":
        return _call_groq(prompt)
    elif AI_PROVIDER == "nvidia":
        return _call_nvidia(prompt)
    else:
        logger.warning(f"Unknown AI provider: {AI_PROVIDER}")
        return None
