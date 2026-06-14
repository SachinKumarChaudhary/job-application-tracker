#!/bin/bash
# One-command setup: restart relay, tunnel, and update PA
# Usage: bash /tmp/relay_setup.sh

set -e

BOT_TOKEN="8926784432:AAFNNMlSQyvE3ME9XeohYosuGC9Na_WVn20"
PA_TOKEN=$(cat /sdcard/Gotjobalert/.pa_token)
PA_USER="SachinKumarChaudhary"
PA_BASE="https://www.pythonanywhere.com/api/v0/user/$PA_USER"
NOTIFIER_PATH="/mnt/sdcard/Gotjobalert/src/notifier.py"

echo "=== 1. Kill stale processes ==="
kill $(pgrep -f "telegram_relay") 2>/dev/null || true
kill $(pgrep -f "serveo.net") 2>/dev/null || true
sleep 1

echo "=== 2. Start relay ==="
nohup python3 /tmp/telegram_relay.py "$BOT_TOKEN" > /tmp/relay.log 2>&1 &
sleep 2
echo "Relay PID: $(pgrep -f telegram_relay)"

echo "=== 3. Start tunnel ==="
nohup ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=10 \
    -o ExitOnForwardFailure=yes \
    -R 80:localhost:5001 serveo.net > /tmp/tunnel.log 2>&1 &
TUNNEL_PID=$!
echo "Tunnel PID: $TUNNEL_PID"
sleep 6

# Extract URL
TUNNEL_URL=$(grep -oP 'https://[a-f0-9-]+\.serveousercontent\.com' /tmp/tunnel.log | head -1)
if [ -z "$TUNNEL_URL" ]; then
    cat /tmp/tunnel.log
    echo "TUNNEL URL NOT FOUND"
    exit 1
fi
echo "Tunnel URL: $TUNNEL_URL/relay"

echo "=== 4. Update notifier.py with new URL ==="
RELAY_SAFE=$(echo "$TUNNEL_URL/relay" | sed 's|/|\\/|g')
sed -i "s/orsion\.com\/relay/orsion.com\/relay/g" "$NOTIFIER_PATH" 2>/dev/null || true
sed -i "s|serveousercontent\.com/relay|$RELAY_SAFE|g" "$NOTIFIER_PATH"

echo "=== 5. Upload to PA ==="
curl -s -o /dev/null -w "Upload: %{http_code}\n" -X POST \
    "$PA_BASE/files/path/home/$PA_USER/Gotjobalert/src/notifier.py" \
    -H "Authorization: Token $PA_TOKEN" \
    -F "content=@$NOTIFIER_PATH"

echo "=== 6. Reload PA app ==="
curl -s -o /dev/null -w "Reload: %{http_code}\n" -X POST \
    "$PA_BASE/webapps/${PA_USER}.pythonanywhere.com/reload/" \
    -H "Authorization: Token $PA_TOKEN"

echo "=== DONE ==="
echo "Open your PA app and test Telegram notification."
echo ""
echo "To keep tunnel alive, run this every 6-12 hours:"
echo "  bash /tmp/relay_setup.sh"
