# AGStock 運用自動化セットアップスクリプト
# このスクリプトは Windows タスクスケジューラに主要なタスクを登録します。

$BaseDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonExe = "python.exe" # venvを使用する場合はパスを書き換えてください

# 1. 毎朝の市場スキャン (平日 08:45)
$ScanTask = "AGStock_MorningScan"
$ScanAction = New-ScheduledTaskAction -Execute $PythonExe -Argument "$BaseDir\daily_scan.py" -WorkingDirectory $BaseDir
$ScanTrigger = New-ScheduledTaskTrigger -Daily -At 08:45
# 平日のみに制限（PowerShellで後から修正）

# 2. 自動トレード (平日 09:15)
$TradeTask = "AGStock_AutoTrade"
$TradeAction = New-ScheduledTaskAction -Execute $PythonExe -Argument "$BaseDir\fully_automated_trader.py" -WorkingDirectory $BaseDir
$TradeTrigger = New-ScheduledTaskTrigger -Daily -At 09:15

# 3. モデル再学習 (毎週土曜 10:00)
$RetrainTask = "AGStock_WeeklyRetrain"
$RetrainAction = New-ScheduledTaskAction -Execute $PythonExe -Argument "$BaseDir\scripts\retrain_system.py" -WorkingDirectory $BaseDir
$RetrainTrigger = New-ScheduledTaskTrigger -Weekly -At 10:00 -DaysOfWeek Saturday

# 共通設定
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

function Register-Task($Name, $Action, $Trigger) {
    $Existing = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if ($Existing) { Unregister-ScheduledTask -TaskName $Name -Confirm:$false }
    Register-ScheduledTask -TaskName $Name -Action $Action -Trigger $Trigger -Settings $Settings
    Write-Host "✅ Registered: $Name"
}

Write-Host "🚀 AGStock 自動運用タスクを登録しています..."
Register-Task $ScanTask $ScanAction $ScanTrigger
Register-Task $TradeTask $TradeAction $TradeTrigger
Register-Task $RetrainTask $RetrainAction $RetrainTrigger

Write-Host "`n✨ 全てのタスクが正常に登録されました。"
Write-Host "タスクスケジューラを開いて確認してください。"
