@echo off
echo ========================================
echo AGStock Setup Script (Windows)
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.12+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/5] Creating directories...
if not exist "reports" mkdir reports
if not exist "data" mkdir data

echo.
echo [3/5] Initializing Paper Trading database...
python -c "from src.paper_trader import PaperTrader; pt = PaperTrader(); print('Database initialized')"

echo.
echo [4/5] Creating environment template...
if not exist ".env" (
    (
        echo # AGStock Environment Variables
        echo.
        echo # Slack Notification ^(Optional^)
        echo SLACK_WEBHOOK_URL=
        echo.
        echo # Email Notification ^(Optional^)
        echo EMAIL_ENABLED=false
        echo EMAIL_FROM=
        echo EMAIL_PASSWORD=
        echo EMAIL_TO=
    ) > .env
    echo Created .env file. Please edit it with your settings.
) else (
    echo .env file already exists. Skipping.
)

echo.
echo [5/5] Running quick test...
python -c "import streamlit; import lightgbm; import yfinance; print('All imports successful!')"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your notification settings ^(optional^)
echo 2. Run: streamlit run app.py
echo.
pause
