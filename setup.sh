#!/bin/bash

echo "========================================"
echo "AGStock Setup Script (Mac/Linux)"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.12+ from https://www.python.org/"
    exit 1
fi

echo "[1/5] Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

echo ""
echo "[2/5] Creating directories..."
mkdir -p reports
mkdir -p data

echo ""
echo "[3/5] Initializing Paper Trading database..."
python3 -c "from src.paper_trader import PaperTrader; pt = PaperTrader(); print('Database initialized')"

echo ""
echo "[4/5] Creating environment template..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# AGStock Environment Variables

# Slack Notification (Optional)
SLACK_WEBHOOK_URL=

# Email Notification (Optional)
EMAIL_ENABLED=false
EMAIL_FROM=
EMAIL_PASSWORD=
EMAIL_TO=
EOF
    echo "Created .env file. Please edit it with your settings."
else
    echo ".env file already exists. Skipping."
fi

echo ""
echo "[5/5] Running quick test..."
python3 -c "import streamlit; import lightgbm; import yfinance; print('All imports successful!')"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your notification settings (optional)"
echo "2. Run: streamlit run app.py"
echo ""
