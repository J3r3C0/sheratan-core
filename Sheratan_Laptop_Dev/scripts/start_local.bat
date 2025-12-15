@echo off
setlocal
cd /d %~dp0\..
powershell -ExecutionPolicy Bypass -File ".\scripts\start_local.ps1"
endlocal
