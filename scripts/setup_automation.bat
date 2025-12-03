@echo off
REM AGStock 自動実行設定スクリプト
REM 個人投資家向け - 完全自動運用のセットアップ

echo ================================================
echo AGStock 自動実行セットアップ
echo ================================================
echo.

REM 現在のディレクトリを取得
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=python

echo 現在のディレクトリ: %SCRIPT_DIR%
echo.

REM Pythonパスの確認
echo Pythonのバージョンを確認中...
%PYTHON_PATH% --version
if errorlevel 1 (
    echo.
    echo エラー: Python が見つかりません
    echo Anaconda Promptなどから実行してください
    pause
    exit /b 1
)

echo.
echo ================================================
echo タスクスケジューラに以下のタスクを登録します:
echo ================================================
echo.
echo 1. AGStock Daily Scan
echo    - 実行時刻: 毎日 15:30 (市場終了後)
echo    - 処理内容: 市場スキャン、シグナル検出、自動取引
echo.
echo 2. AGStock Morning Brief  
echo    - 実行時刻: 毎日 08:00 (市場開始前)
echo    - 処理内容: 朝の市況レポート送信
echo.
echo ================================================
echo.

REM 確認
set /p CONFIRM="セットアップを続行しますか？ (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo セットアップをキャンセルしました
    pause
    exit /b 0
)

echo.
echo タスクを登録中...
echo.

REM タスク1: 日次スキャン（15:30）
schtasks /create /tn "AGStock Daily Scan" /tr "cmd /c cd /d %SCRIPT_DIR% && %PYTHON_PATH% fully_automated_trader.py >> logs\auto_trader.log 2>&1" /sc daily /st 15:30 /f

if errorlevel 1 (
    echo エラー: Daily Scanのタスク登録に失敗しました
) else (
    echo ✓ Daily Scanのタスクを登録しました
)

echo.

REM タスク2: 朝の市況レポート（08:00）
schtasks /create /tn "AGStock Morning Brief" /tr "cmd /c cd /d %SCRIPT_DIR% && %PYTHON_PATH% morning_brief.py >> logs\morning_brief.log 2>&1" /sc daily /st 08:00 /f

if errorlevel 1 (
    echo エラー: Morning Briefのタスク登録に失敗しました
) else (
    echo ✓ Morning Briefのタスクを登録しました
)

echo.
echo ================================================
echo セットアップ完了！
echo ================================================
echo.
echo 登録されたタスクを確認するには:
echo   タスクスケジューラを開く（taskschd.msc）
echo.
echo タスクを削除するには:
echo   schtasks /delete /tn "AGStock Daily Scan" /f
echo   schtasks /delete /tn "AGStock Morning Brief" /f
echo.
echo ログファイル:
echo   logs\auto_trader.log
echo   logs\morning_brief.log
echo.
echo ================================================
echo.
echo 🎉 これで毎日自動で取引が実行されます！
echo    - 15:30: 市場スキャン・自動取引
echo    - 08:00: 朝の市況レポート
echo.
echo ⚠️ 重要な注意事項:
echo    1. PCの電源を入れたままにしてください
echo    2. config.jsonで通知設定を確認してください
echo    3. 最初の数日は結果を確認することをお勧めします
echo.
pause
