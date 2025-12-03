@echo off
cd ..
REM フルオート取引システム - 毎朝自動実行用
REM Full Auto Trading System - Daily Auto Run

echo ========================================
echo   AGStock フルオート取引システム
echo ========================================
echo.

REM ログディレクトリ作成
if not exist logs mkdir logs
if not exist reports mkdir reports

REM Python実行
echo [%date% %time%] 実行開始...
python auto_trader.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   実行成功！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   エラーが発生しました
    echo ========================================
    pause
)

REM 10秒後に自動で閉じる
timeout /t 10
