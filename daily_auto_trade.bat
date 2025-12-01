@echo off
echo AGStock デイリー自動運用
echo ========================

cd /d C:\gemini-thinkpad\AGStock

echo.
echo [%date% %time%] デイリールーチン開始...
echo.

python -c "from master_trading_system import MasterTradingSystem; import json; system = MasterTradingSystem(); results = system.daily_routine(); print(json.dumps(results, indent=2, ensure_ascii=False))"

echo.
echo [%date% %time%] デイリールーチン完了
echo.

pause
