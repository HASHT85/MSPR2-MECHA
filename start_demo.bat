@echo off
cd /d "%~dp0"
if /I "%~1"=="--local" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_demo.ps1" -Local
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_demo.ps1" %*
)
pause
