# AGStock Morning Routine - Task Scheduler Setup
# Run this script as Administrator to register the morning routine

$TaskName = "AGStock_Morning_Routine"
$TaskDescription = "Runs AGStock Sovereign Morning Constitution at 7:00 AM daily"
$ScriptPath = "C:\gemini-thinkpad\AGStock\run_morning_routine.bat"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task '$TaskName' already exists. Removing..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create Action
$Action = New-ScheduledTaskAction -Execute $ScriptPath

# Create Trigger (Daily at 7:00 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At 7:00AM

# Create Settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register Task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description $TaskDescription

Write-Host ""
Write-Host "============================================"
Write-Host "  AGStock Morning Routine Scheduled!"
Write-Host "============================================"
Write-Host "Task Name: $TaskName"
Write-Host "Schedule: Daily at 7:00 AM"
Write-Host "Script: $ScriptPath"
Write-Host ""
Write-Host "To view: Open Task Scheduler -> Task Scheduler Library"
Write-Host "To test: Right-click the task -> Run"
Write-Host ""
