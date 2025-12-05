# AGStock 自動起動タスク登録スクリプト
# ※ 管理者権限で実行してください

$TaskName = "AGStock_AutoTrader"
$WorkDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = Join-Path $WorkDir "start_daemon.bat"

Write-Host "Setting up Task Scheduler for: $TaskName"
Write-Host "Working Directory: $WorkDir"
Write-Host "Script Path: $ScriptPath"

# アクション作成
$Action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $WorkDir

# トリガー作成（ログオン時）
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# 設定作成（電源接続時のみ実行しない、など）
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0

# タスク登録
try {
    Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName $TaskName -Description "AGStock Automated Trading Daemon" -Force
    Write-Host "✅ タスク登録成功！次回ログオン時に自動起動します。" -ForegroundColor Green
    Write-Host "すぐに開始するには、以下のコマンドを実行してください："
    Write-Host "Start-ScheduledTask -TaskName `"$TaskName`""
} catch {
    Write-Host "❌ エラー: タスク登録に失敗しました。" -ForegroundColor Red
    Write-Host "管理者権限でPowerShellを実行しているか確認してください。"
    Write-Host $_.Exception.Message
}
