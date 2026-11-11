@echo off
cd /d "%~dp0"
echo Arret des conteneurs Docker MECHA (si actifs)...
docker compose down >nul 2>&1
echo Arret des processus Python locaux FastAPI / Streamlit (si actifs)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'api\.main:app|app[\\/]src[\\/]dashboard\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo [OK] Demo MECHA arretee proprement.
pause
