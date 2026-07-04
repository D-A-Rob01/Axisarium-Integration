@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0register-aletheion-task.ps1" -StartTime "06:00"
echo.
echo Installer finished with exit code %errorlevel%.
pause
