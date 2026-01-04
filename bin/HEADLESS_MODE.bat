@echo off
echo ========================================
echo   AGStock 自動運転モード (Headless)
echo ========================================
echo.
echo バックグラウンドで市場を監視し、自動売買を行います。
echo 停止するには Ctrl+C を押してください。
echo.

python run_headless.py --interval 3600

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo エラーが発生しました。再起動しますか？
    pause
)
