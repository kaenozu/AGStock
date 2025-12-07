@echo off
cd ..
title AGStock Simple Dashboard
echo ========================================================
echo   AGStock シンプルダッシュボード起動
echo ========================================================
echo.

cd /d %~dp0

REM 仮想環境のアクティベート
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo ブラウザが自動的に開きます...
echo.

streamlit run simple_dashboard.py --server.port 8502

pause
