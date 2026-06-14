# n8n Workflow — Job Application Auto-Tracker

## Overview

This workflow was designed as a no-code alternative to the custom Flask app. It runs the same pipeline — Gmail → Parse AI + regex → Google Sheets → Notifications — but visually in n8n.

**Status:** Archived. The Flask app replaced this because Android Termux kills Node.js threads (tracing-stop ptrace bug). See [Session History](#session-history) below.

---

## Workflow Diagram

```
Gmail Trigger ──► Decode MIME ──► Gemini API ──► Parse & Validate ──► Is Valid?
   (poll every 15m)   (extract fields)   (AI parse)   (clean JSON)       │
                                                                         │
                                                     ┌─── Yes ──► Append to Sheet ──► Send Telegram
                                                     │              (Google Sheets)     (notification)
                                                     └─── No ───► End (skip)
```

## Node Breakdown

| Node | Type | What It Does |
|---|---|---|
| **Gmail Trigger** | `gmailTrigger` | Polls Gmail every 15 min with query: `subject:"application received" OR subject:"thank you for applying" OR ...` |
| **Decode MIME Body** | `code` (JavaScript) | Extracts headers (Subject, From, Message-ID), decodes base64 body, returns `{subject, sender, messageId, date, body}` |
| **Gemini API** | `httpRequest` | Calls `gemini-2.0-flash:generateContent` with the email text, requests JSON output |
| **Parse & Validate** | `code` (JavaScript) | Strips markdown from Gemini response, parses JSON, validates fields, returns clean `{company_name, job_role, ...}` |
| **Is Valid?** | `if` | Checks `company_name != "Unknown"` — skips unparseable emails |
| **Append to Sheet** | `googleSheets` | Appends row to Google Sheet with all parsed fields |
| **Send Telegram** | `telegram` | Sends Markdown notification with emoji based on email type |
| **End** | `noOp` | Terminal node |

---

## Key Code: Decode MIME Body (JavaScript)

```javascript
const headers = {};
for (const h of $json.payload.headers) {
  headers[h.name] = h.value;
}

function extractText(payload) {
  const parts = payload.parts || [payload];
  for (const part of parts) {
    if (part.mimeType === "text/plain" && part.body?.data) {
      return Buffer.from(part.body.data, "base64url").toString("utf-8");
    }
    if (part.parts) {
      const result = extractText(part);
      if (result) return result;
    }
  }
  if (payload.body?.data) {
    return Buffer.from(payload.body.data, "base64url").toString("utf-8");
  }
  return "";
}

const body = extractText($json.payload);
const ts = $json.internalDate
  ? new Date(parseInt($json.internalDate)).toISOString().split("T")[0]
  : new Date().toISOString().split("T")[0];

return [{
  json: {
    subject: headers["Subject"] || "",
    sender: headers["From"] || "",
    messageId: headers["Message-ID"] || "",
    date: ts,
    body: body
  }
}];
```

## Key Code: Parse & Validate (JavaScript)

```javascript
const candidates = $json.candidates || [];
const raw = candidates[0]?.content?.parts?.[0]?.text
  || $json.text
  || $json.response
  || "{}";

let cleaned = raw.replace(/```json?\n?/g, "").replace(/\n?```/g, "").trim();
const match = cleaned.match(/\{[\s\S]*\}/);
let parsed = {};
if (match) {
  try { parsed = JSON.parse(match[0]); } catch (e) { parsed = {}; }
}

const validTypes = ["offer_letter", "interview_invitation", "application_received", "rejection", "other"];

return [{
  json: {
    company_name: (parsed.company_name || "").trim() || "Unknown",
    job_role: (parsed.job_role || "").trim() || "Unknown",
    application_date: parsed.date || $json.date || null,
    email_subject: $json.subject || "",
    sender_email: $json.sender || "",
    message_id: $json.messageId || "",
    email_type: validTypes.includes(parsed.email_type) ? parsed.email_type : "other",
    summary: (parsed.summary || "").trim() || ""
  }
}];
```

---

## Ported to Flask

The logic from both JavaScript code nodes was ported directly to Python in the Flask app:

| n8n Node | Flask Equivalent |
|---|---|
| Gmail Trigger | `src/poller.py` — `fetch_unread_messages()` |
| Decode MIME Body | `src/poller.py` — `get_body_text()` |
| Gemini API | `src/ai.py` — `_call_gemini()` |
| Parse & Validate + Is Valid? | `src/parser.py` — `parse_email()`, `_clean_json()` |
| Append to Sheet | `src/sheets_writer.py` — `append_row()` |
| Send Telegram | `src/notifier.py` — `_send_telegram()` |

---

## Why n8n Was Rejected

| Issue | Detail |
|---|---|
| **Android tracing-stop bug** | Termux proot stops Node.js threads immediately after fork. Process shows `State: t (tracing stop)`. Requires `kill -CONT` loop to keep alive. |
| **Unreliable 24/7** | Even with CONT daemon, n8n occasionally freezes during SQLite migrations or Express init. |
| **Resource-heavy** | n8n uses ~200MB RAM + Node.js runtime. Flask app uses ~30MB. |
| **No multi-user** | n8n workflows run as a single user. Flask supports per-user Gmail OAuth. |

The `n8n-workflow.json` is preserved in the repo as a reference — the architecture is sound, and it could run on a real server (VPS, Railway, etc.) without issues.

---

## How to Run (if you have a real server)

```bash
# Install n8n
npm install -g n8n

# Start
n8n start

# Import workflow
# Open http://localhost:5678 → Workflows → Import → Select n8n-workflow.json
```

Set up Google Sheets + Telegram credentials in n8n's credential manager.
