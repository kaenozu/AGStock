@echo off
echo ==========================================
echo    AGStock AI Trading System - Docker
echo ==========================================

echo Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo Please install Docker Desktop for Windows.
    pause
    exit /b
)

echo.
echo Building and Starting Containers...
docker-compose up -d --build

echo.
echo [SUCCESS] System is running in background.
echo Access at: http://localhost:8501
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
echo.
pause
