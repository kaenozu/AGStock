# AGStock Auto Trading Task Registration Script
# This script registers a scheduled task to run auto trading daily at 9:30 AM

$TaskName = "AGStock_AutoTrading"
$TaskDescription = "Daily automated trading execution"
$ScriptPath = "c:\gemini-thinkpad\AGStock\run_auto_trade.bat"
$WorkingDirectory = "c:\gemini-thinkpad\AGStock"

# Create task action
$Action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $WorkingDirectory

# Create trigger (daily at 9:30 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At 09:30

# Task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Remove existing task if present
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Removing existing task: $TaskName"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Register the task
Write-Host "Registering task: $TaskName"
Register-ScheduledTask -TaskName $TaskName -Description $TaskDescription -Action $Action -Trigger $Trigger -Settings $Settings

Write-Host ""
Write-Host "========================================"
Write-Host "Task registration completed successfully!"
Write-Host "========================================"
Write-Host ""
Write-Host "Task Details:"
Write-Host "  Name: $TaskName"
Write-Host "  Schedule: Daily at 9:30 AM"
Write-Host "  Script: $ScriptPath"
Write-Host ""
Write-Host "To verify:"
Write-Host "  1. Open Task Scheduler"
Write-Host "  2. Click 'Task Scheduler Library'"
Write-Host "  3. Find '$TaskName' in the list"
Write-Host ""
Write-Host "To test now:"
Write-Host "  Right-click the task -> Run"
Write-Host ""
