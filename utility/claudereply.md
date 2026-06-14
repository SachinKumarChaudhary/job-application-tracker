Here's the full diagnosis. There are **three bugs across two layers**, and they all produce the same symptom: HTMX gets a 5xx response and silently drops it — no swap, no error, nothing visible.

---

## 🔴 Bug 1 — `NameError: msg` in `/test-notification` (Definitive)

```python
# msg is NEVER defined anywhere in this function
if not channel or channel == "none":
    return jsonify({"status": "error", "error": msg}), 400   # ← NameError

try:
    ok = notify_single(channel, prefs, msg, email)            # ← NameError here too
```

`msg` is used in **two places** but never assigned. Even though the user has Telegram configured (so the `if not channel` guard is skipped), `notify_single(..., msg, ...)` still fires and immediately throws `NameError: name 'msg' is not defined` → Flask returns 500 → **HTMX ignores 5xx by default and does nothing**.

**Fix:**
```python
@app.route("/test-notification", methods=["POST"])
def test_notification():
    email = get_user_email()
    if not email:
        return jsonify({"error": "Not authenticated"}), 401

    prefs = get_user_prefs(email)
    channel = prefs.get("notification_channel")

    # Define msg before using it
    msg = "🔔 Test notification from Job Tracker"

    if not channel or channel == "none":
        _alert = "No notification channel configured."
        if request.headers.get("HX-Request"):
            ctx = _get_dashboard_context(email)
            ctx["alert_message"] = _alert
            return render_template("_dashboard.html", **ctx)
        return jsonify({"status": "error", "error": _alert}), 200  # 200 so HTMX swaps

    try:
        ok = notify_single(channel, prefs, msg, email)
        _alert = f"Test {channel} notification sent!" if ok else f"{channel} notification failed — check config."
    except Exception as e:
        _alert = f"Test notification failed: {e}"
        ok = False

    if request.headers.get("HX-Request"):
        ctx = _get_dashboard_context(email)
        ctx["alert_message"] = _alert
        return render_template("_dashboard.html", **ctx)
    return jsonify({"status": "ok" if ok else "error", "message": _alert})
```

---

## 🔴 Bug 2 — `_get_dashboard_context()` called without `try/except` in all routes

All three routes call `_get_dashboard_context(email)` **bare** — no try/except around it. The function's inner try block only guards the Sheets API calls. Anything else it touches can propagate:

```python
def _get_dashboard_context(email):
    prefs = get_user_prefs(email)              # ← unguarded
    ...
    return dict(
        ...
        telegram_bot_username=TELEGRAM_BOT_USERNAME,  # ← NameError if env var missing on PythonAnywhere
        has_telegram_bot=bool(TELEGRAM_BOT_TOKEN),    # ← same
        scheduler_alive=_scheduler_alive["running"],  # ← KeyError if key absent
        interval=POLL_INTERVAL_MINUTES,               # ← NameError if missing
    )
```

On PythonAnywhere specifically, env vars must be set in the **Web tab → Environment variables** section — they're not inherited from `.env` files. If `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, or `POLL_INTERVAL_MINUTES` aren't declared there, they silently don't exist → 500 on every HTMX request.

**Fix — wrap at the route level:**
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

    try:                                              # ← wrap this
        ctx = _get_dashboard_context(email)
    except Exception as e:
        ctx = {"authed": True, "email": email, "sheet_error": str(e),
               "rows": [], "prefs": {}, "prefs_complete": False,
               "sheet_url": "", "headers": [], "last_run": None,
               "last_count": 0, "last_error": "", "interval": 30,
               "logs": [], "telegram_bot_username": "",
               "has_telegram_bot": False, "scheduler_alive": False}
    ctx["alert_message"] = _alert
    return render_template("_dashboard.html", **ctx)
```

Apply the same pattern to `/send-test-email`.

---

## 🟡 Bug 3 — HTMX gets 4xx responses → also silently ignored

The `if not channel or channel == "none"` path (before your fix) returned `400`. HTMX only swaps on **2xx responses by default**. Any 4xx/5xx is dropped with no visible feedback. Throughout the app, error returns should either be 200 with an error message in the partial, or you need to enable error handling explicitly:

```html
<!-- Add to your base template, once -->
<script>
  document.body.addEventListener("htmx:responseError", function(evt) {
    console.error("HTMX error:", evt.detail.xhr.status, evt.detail.xhr.responseText);
    // Optionally show a toast here
  });
</script>
```

This alone would have surfaced all three bugs immediately in the browser console.

---

## Immediate Debug Checklist (PythonAnywhere)

Do these in order — each one answers a layer:

| Step | Command / Location | What it tells you |
|------|-------------------|-------------------|
| 1 | PythonAnywhere **Web tab → Error log** | Exact exception + traceback |
| 2 | Browser DevTools → Network tab → click the buttons | Status code (500? 401? 200?) |
| 3 | Browser Console | HTMX `responseError` events |
| 4 | PythonAnywhere **Web tab → Environment variables** | Whether `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `POLL_INTERVAL_MINUTES` are set |
| 5 | `python3 -c "from webui import app"` in a PA console | Surfaces import-time errors like circular imports from `notify_single` change |

---

## Summary

| # | Bug | Affects | Severity |
|---|-----|---------|----------|
| 1 | `msg` NameError — never defined | `/test-notification` always | 🔴 Crash |
| 2 | `_get_dashboard_context()` unguarded + env vars missing on PA | `/trigger`, `/send-test-email` | 🔴 Crash |
| 3 | Error responses (4xx/5xx) silently swallowed by HTMX | All three | 🟡 Masked symptoms |

Fix 1 and 2 first — they're definitive code bugs. Then confirm env vars are set in PythonAnywhere's Web tab. The error logs will confirm exactly which exception is firing on the live server.