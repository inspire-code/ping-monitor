@echo off
cd /d "%~dp0"
:loop
start /wait python ping_monitor.py
echo Script crashed or closed. Restarting in 5 seconds...
timeout /t 5
goto loop
