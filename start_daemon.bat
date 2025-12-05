@echo off
cd /d %~dp0
echo Starting AGStock Daemon...
start /B python daemon.py > logs/daemon_stdout.log 2>&1
echo Daemon started in background.
