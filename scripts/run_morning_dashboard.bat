@echo off
cd ..
REM 朝活ダッシュボード起動スクリプト
REM 使い方: ダブルクリックで起動

echo ========================================
echo   朝活ダッシュボード起動中...
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

streamlit run morning_dashboard.py --server.port 8503

pause
