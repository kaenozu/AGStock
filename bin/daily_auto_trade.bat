@echo off
echo AGStock デイリー自動運用
echo ========================

cd /d "%~dp0.."

echo.
echo [%date% %time%] デイリールーチン開始...
echo.

python run_auto_trade.py

echo.
echo [%date% %time%] デイリールーチン完了
echo.

pause
