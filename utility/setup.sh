#!/usr/bin/env bash
set -e

echo "=== Offer Tracker Setup ==="

echo ""
echo "Step 1: Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo ""
echo "Step 2: Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "Step 3: Setting up .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  -> .env created. Edit it with your notification tokens later."
else
    echo "  -> .env already exists, skipping."
fi

echo ""
echo "Step 4: Creating credentials folder..."
mkdir -p credentials

echo ""
echo "=== NEXT STEPS ==="
echo ""
echo "1. Go to https://console.cloud.google.com/apis/credentials"
echo "   -> Create OAuth 2.0 Client ID (Desktop app)"
echo "   -> Download JSON -> save as: credentials/credentials.json"
echo ""
echo "2. Run the OAuth setup:"
echo "   source .venv/bin/activate"
echo "   python -m src.setup_oauth"
echo ""
echo "3. Edit .env to add Pushover/Slack/Telegram/WhatsApp tokens"
echo ""
echo "4. Test it:"
echo "   source .venv/bin/activate"
echo "   python -c \"from src.main import OfferTracker; OfferTracker().run_once()\""
echo ""
echo "5. Run continuously:"
echo "   python -m src.scheduler"
