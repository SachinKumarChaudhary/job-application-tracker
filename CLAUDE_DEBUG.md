# Debug: Three Buttons Not Working on Offer Tracker

## Overview

Flask app deployed on PythonAnywhere: https://SachinKumarChaudhary.pythonanywhere.com/

Repo: https://github.com/SachinKumarChaudhary/job-application-tracker

## The Problem

Three HTMX-powered buttons on the dashboard do nothing when clicked (no visible response):

1. **Check Now** (`hx-get="/trigger"`)
2. **Send Test Email** (`hx-get="/send-test-email"`)
3. **Test Notification** (`hx-post="/test-notification"`)

The initial page loads fine. User is authenticated. Notification channel is Telegram.

## What We've Verified (local tests pass)

- Template `_dashboard.html` renders correctly with `alert_message` context
- `notify_single()` returns `False` for missing config correctly
- All Python imports work
- Routes return 401 for unauthenticated requests (correct)
- HTMX CDN script (`unpkg.com/htmx.org@2.0.4`) loads in the page
- Tailwind CSS loads from CDN

## What Could Cause All Three to Fail Silently

HTMX does NOT swap content on 4xx/5xx responses. All three routes return HTML (via `render_template("_dashboard.html", ...)`) for HTMX requests, or JSON for fetch() calls.

**The routes (current code from GitHub main branch):**

### `/trigger` (GET)
```python
@app.route("/trigger")
def trigger():
    email = get_user_email()
    if not email:
        return jsonify({"error": "Not authenticated"}), 401
    try:
        run_poll(email)
        _alert = f"Poll complete — {last_count.get(email, 0)} new entries"
    except Exception as e:
        _alert = f"Poll failed: {e}"
    ctx = _get_dashboard_context(email)
    ctx["alert_message"] = _alert
    return render_template("_dashboard.html", **ctx)
```

### `/send-test-email` (GET)
```python
@app.route("/send-test-email")
def send_test_email_route():
    email = get_user_email()
    if not email:
        return jsonify({"error": "Not authenticated"}), 401
    try:
        send_test_email(email)
        _alert = "Test email sent to your Gmail inbox!"
    except Exception as e:
        _alert = f"Test email failed: {e}"
    ctx = _get_dashboard_context(email)
    ctx["alert_message"] = _alert
    return render_template("_dashboard.html", **ctx)
```

### `/test-notification` (POST)
```python
@app.route("/test-notification", methods=["POST"])
def test_notification():
    email = get_user_email()
    if not email:
        return jsonify({"error": "Not authenticated"}), 401
    prefs = get_user_prefs(email)
    channel = prefs.get("notification_channel")
    if not channel or channel == "none":
        return jsonify({"status": "error", "error": msg}), 400
    try:
        ok = notify_single(channel, prefs, msg, email)
        _alert = f"Test {channel} notification sent!" if ok else f"...failed"
    except Exception as e:
        _alert = f"Test notification failed: {e}"
    if request.headers.get("HX-Request"):
        ctx = _get_dashboard_context(email)
        ctx["alert_message"] = _alert
        return render_template("_dashboard.html", **ctx)
    return jsonify({"status": "ok" if ok else "error", "message": _alert})
```

## Key Shared Function

```python
def _get_dashboard_context(email: str) -> dict:
    prefs = get_user_prefs(email)
    sheet_url = rows = sheet_error = ""
    try:
        sheet_url = ensure_sheet(email)
        svc = get_sheets_service(email)
        sid = _find_or_create_sheet(email)
        data = svc.spreadsheets().values().get(spreadsheetId=sid, range="A:M").execute()
        vals = data.get("values", [])
        if vals:
            rows = vals[1:][-20:]
    except Exception as e:
        sheet_error = str(e)
    return dict(
        authed=True, email=email, prefs=prefs,
        prefs_complete="notification_channel" in prefs,
        sheet_url=sheet_url, rows=rows,
        headers=SHEET_HEADERS[:5] + ["Stage", "Summary", "Location", "Salary", "Next Step", "Parser"],
        last_run=last_run.get(email), last_count=last_count.get(email, 0),
        last_error=last_error.get(email, ""), sheet_error=sheet_error,
        interval=POLL_INTERVAL_MINUTES,
        logs=log_buffer.get(email, [])[-30:],
        telegram_bot_username=TELEGRAM_BOT_USERNAME,
        has_telegram_bot=bool(TELEGRAM_BOT_TOKEN),
        scheduler_alive=_scheduler_alive["running"],
        alert_message="",
    )
```

## Helper: `get_user_email()` (called by all routes)

```python
def get_user_email() -> str | None:
    email = session.get("user_email")
    if not email:
        return None
    norm = normalize_email(email)
    if norm != email:
        prefs = load_prefs()
        if email in prefs and norm not in prefs:
            prefs[norm] = prefs.pop(email)
            save_prefs(prefs)
        old_token = get_token_path(email)
        new_token = get_token_path(norm)
        if old_token.exists() and not new_token.exists():
            old_token.rename(new_token)
        for d in (last_run, last_count, last_error, log_buffer):
            if email in d:
                d[norm] = d.pop(email)
        session["user_email"] = norm
    return norm
```

## Recent Changes (could be relevant)

1. Added `normalize_email()` — lowercases Gmail usernames, strips dots
2. `get_user_email()` now normalizes + migrates old prefs/tokens on first request
3. `get_creds()` renames old token files to normalized paths
4. Added `@app.after_request` with `Cache-Control: no-store` on all responses
5. Changed import from `from src.notifier import _send_slack_webhook, _send_whatsapp_callmebot, _send_telegram` to `from src.notifier import notify_single`
6. OAuth callback `redirect("/")` instead of error page

## What Claude Should Investigate

1. Could the `@app.after_request` `Cache-Control: no-store` header cause the browser to ignore `Set-Cookie` on HTMX response? (known edge case in some browsers)
2. Could the `normalize_email()` migration in `get_user_email()` cause a race condition or crash on the second request?
3. Could the `get_creds()` token file rename cause issues for subsequent requests?
4. Is there any case where `_get_dashboard_context()` throws outside its try/except?
5. Does `render_template("_dashboard.html", **ctx)` silently fail for some Jinja edge case?
6. Could the `from src.notifier import notify_single` (module-level) cause a circular import or delayed failure?

## Files on GitHub

All code is at: https://github.com/SachinKumarChaudhary/job-application-tracker

Key files:
- `webui.py` — main Flask app (all routes, most logic)
- `src/notifier.py` — notification dispatch
- `src/config.py` — configuration/env vars
- `templates/_dashboard.html` — dashboard partial template
- `templates/index.html` — main page (includes HTMX CDN)
