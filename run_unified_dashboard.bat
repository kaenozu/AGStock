@echo off
REM 統合ダッシュボード 起動スクリプト

echo ========================================
echo   AGStock 統合ダッシュボード
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

streamlit run unified_dashboard.py --server.port 8500

pause
