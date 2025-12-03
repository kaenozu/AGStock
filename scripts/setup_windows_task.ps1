$Action = New-ScheduledTaskAction -Execute "c:\gemini-thinkpad\AGStock\run_auto_invest.bat"
$Trigger = New-ScheduledTaskTrigger -Daily -At 15:30
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -TaskName "AGStock_AutoInvest" -Description "Daily Auto Invest for AGStock (15:30 JST)" -Force
Write-Host "✅ Task 'AGStock_AutoInvest' has been registered to run daily at 15:30."
Write-Host "To check the task, open Task Scheduler and look for 'AGStock_AutoInvest'."
