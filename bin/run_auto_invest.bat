@echo off
cd /d "%~dp0.."
if not exist logs mkdir logs
echo ======================================================== >> logs\scheduler.log
echo Starting Auto Invest at %date% %time% >> logs\scheduler.log
python auto_invest.py >> logs\scheduler.log 2>&1
echo Finished Auto Invest at %date% %time% >> logs\scheduler.log
echo ======================================================== >> logs\scheduler.log
