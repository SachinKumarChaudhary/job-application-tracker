"""Telegram API relay server — receives requests and forwards to Telegram.
Tries IP directly (bypasses DNS) and hostname as fallback.
"""
import os, sys, logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [relay] %(message)s")
log = logging.getLogger("relay")

ALLOWED_TOKENS = set()
TELEGRAM_IPS = ["149.154.166.110", "149.154.167.220", "149.154.175.100"]

@app.route("/relay/bot<token>/sendMessage", methods=["POST"])
def relay(token):
    if ALLOWED_TOKENS and token not in ALLOWED_TOKENS:
        return jsonify({"ok": False, "error": "unauthorized token"}), 403
    data = request.get_json(silent=True) or {}
    import requests

    # Try each method
    targets = [[f"https://{ip}/bot{token}/sendMessage", {"Host": "api.telegram.org"}]
               for ip in TELEGRAM_IPS]
    targets += [[f"http://{ip}/bot{token}/sendMessage", {"Host": "api.telegram.org"}]
                for ip in TELEGRAM_IPS]
    targets += [[f"https://api.telegram.org/bot{token}/sendMessage", {}],
                [f"http://api.telegram.org/bot{token}/sendMessage", {}]]

    for url, headers in targets:
        try:
            r = requests.post(url, json=data, timeout=10, headers=headers)
            log.info(f"relayed -> {r.status_code} ({url[:50]}...)")
            return jsonify(r.json()), r.status_code
        except Exception as e:
            log.debug(f"fail: {url[:50]}... -> {e}")
    return jsonify({"ok": False, "error": "all targets failed"}), 502

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ALLOWED_TOKENS.add(sys.argv[1])
        print(f"Allowed bot token: {sys.argv[1][:6]}...{sys.argv[1][-4:]}")
    port = int(os.environ.get("PORT", 5001))
    print(f"Relay listening on :{port}")
    app.run(host="0.0.0.0", port=port)
