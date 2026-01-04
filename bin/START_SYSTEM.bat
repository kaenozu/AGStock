@echo off
title AGStock Full Auto System
echo ========================================================
echo   AGStock フルオートシステム起動
echo ========================================================
echo.
echo  システムを起動しています...
echo  このウィンドウは最小化して置いておいてください。
echo.

cd /d %~dp0

REM 仮想環境のアクティベート
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python run_system.py

pause
