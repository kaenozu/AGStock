@echo off
REM ============================================
REM   AGStock Morning Routine Launcher
REM   Designed to be called by Windows Task Scheduler
REM ============================================

echo [%DATE% %TIME%] Starting AGStock Morning Routine...

REM Navigate to project directory
cd /d "%~dp0.."

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the morning routine
python morning_routine.py

echo [%DATE% %TIME%] Morning Routine Completed.
pause
