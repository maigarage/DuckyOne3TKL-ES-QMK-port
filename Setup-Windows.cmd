@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup-Windows.ps1"
if errorlevel 1 echo Setup failed. Review the error above; no firmware was flashed.
pause
