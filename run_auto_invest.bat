@echo off
cd /d "c:\gemini-thinkpad\AGStock"
if not exist logs mkdir logs
echo ======================================================== >> logs\scheduler.log
echo Starting Auto Invest at %date% %time% >> logs\scheduler.log
"C:\Users\neoen\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe" auto_invest.py >> logs\scheduler.log 2>&1
echo Finished Auto Invest at %date% %time% >> logs\scheduler.log
echo ======================================================== >> logs\scheduler.log
