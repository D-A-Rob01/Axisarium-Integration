@echo off
setlocal
cd /d "%~dp0"

net session >nul 2>&1
if not "%errorlevel%"=="0" (
  echo Aletheion scheduler hardening needs one elevated Task Scheduler registration.
  echo Requesting administrator permission...
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -Verb RunAs -FilePath '%~dp0install-aletheion-task-elevated.cmd'"
  echo.
  echo If Windows showed a permission prompt, approve it and use the elevated window that opens.
  pause
  exit /b
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0register-aletheion-task.ps1" -StartTime "06:00"
echo.
echo Installer finished with exit code %errorlevel%.
pause
