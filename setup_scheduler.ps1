# AGStock 自動実行スケジューラー設定スクリプト
# 管理者権限で実行してください

$scriptPath = $PSScriptRoot
$pythonPath = (Get-Command python).Source
$traderScript = Join-Path $scriptPath "fully_automated_trader.py"

Write-Host "=== AGStock 自動実行スケジューラー設定 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Python: $pythonPath"
Write-Host "Script: $traderScript"
Write-Host ""

# 日本市場用タスク (平日 16:00)
$taskName1 = "AGStock_JP_Market"
$action1 = New-ScheduledTaskAction -Execute $pythonPath -Argument $traderScript -WorkingDirectory $scriptPath
$trigger1 = New-ScheduledTaskTrigger -Daily -At "16:00"
$trigger1.DaysOfWeek = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
$settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    Unregister-ScheduledTask -TaskName $taskName1 -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $taskName1 -Action $action1 -Trigger $trigger1 -Settings $settings1 -Description "AGStock 日本市場クローズ後の自動取引 (16:00)"
    Write-Host "✓ 日本市場タスク登録完了: 平日 16:00" -ForegroundColor Green
} catch {
    Write-Host "✗ 日本市場タスク登録失敗: $_" -ForegroundColor Red
}

# 米国市場用タスク (平日 07:00)
$taskName2 = "AGStock_US_Market"
$action2 = New-ScheduledTaskAction -Execute $pythonPath -Argument $traderScript -WorkingDirectory $scriptPath
$trigger2 = New-ScheduledTaskTrigger -Daily -At "07:00"
$trigger2.DaysOfWeek = "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"  # 米国時間の月-金 = 日本時間の火-土
$settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    Unregister-ScheduledTask -TaskName $taskName2 -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $taskName2 -Action $action2 -Trigger $trigger2 -Settings $settings2 -Description "AGStock 米国市場クローズ後の自動取引 (07:00)"
    Write-Host "✓ 米国市場タスク登録完了: 火-土 07:00" -ForegroundColor Green
} catch {
    Write-Host "✗ 米国市場タスク登録失敗: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 設定完了 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "確認方法: タスクスケジューラを開いて以下を確認してください"
Write-Host "  - $taskName1"
Write-Host "  - $taskName2"
Write-Host ""
Write-Host "手動テスト実行:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName1'" -ForegroundColor Yellow
Write-Host ""
