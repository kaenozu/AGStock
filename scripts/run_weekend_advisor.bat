@echo off
cd ..
REM 週末戦略会議 起動スクリプト

echo ========================================
echo   週末戦略会議 - AI戦略アドバイザー
echo ========================================
echo.

REM 仮想環境がある場合はアクティベート
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Streamlit起動
echo ブラウザが自動的に開きます...
echo 終了するには Ctrl+C を押してください
echo.

streamlit run weekend_advisor.py --server.port 8504

pause
