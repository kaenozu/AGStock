@echo off
REM 自動売買実行用バッチファイル
REM Windowsタスクスケジューラーから実行されます

cd /d "%~dp0.."

echo ========================================
echo AGStock 自動売買システム
echo 実行時刻: %date% %time%
echo ========================================

REM Python仮想環境がある場合はアクティベート（オプション）
REM call venv\Scripts\activate.bat

REM 自動売買スクリプトを実行
python run_auto_trade.py

echo.
echo ========================================
echo 実行完了
echo ========================================

REM ログを確認したい場合は以下をコメント解除
REM pause
