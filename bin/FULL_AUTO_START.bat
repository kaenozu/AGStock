@echo off
chcp 65001 >nul
title AGStock フルオートシステム

echo ============================================================
echo   🤖 AGStock フルオート取引システム
echo ============================================================
echo.
echo   このスクリプトは以下を自動で実行します:
echo.
echo   ✅ 毎時0分・30分に市場スキャン
echo   ✅ AIによる売買シグナル生成
echo   ✅ 自動売買の実行（信頼度50%%以上のみ）
echo   ✅ LINE通知（設定済みの場合）
echo.
echo   搭載AI: LSTM, LightGBM, Transformer, Prophet, RL, FinBERT
echo.
echo ============================================================
echo.

REM ログディレクトリ作成
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "models" mkdir models

REM Python環境確認
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Pythonが見つかりません
    pause
    exit /b 1
)

echo 🚀 デーモン起動中...
echo.
echo ※ 停止するにはCtrl+Cを押してください
echo.

python daemon.py

pause
