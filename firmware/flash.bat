@echo off
setlocal
title Project Sidecar — ESP32 Auto-Flasher
echo ==========================================================
echo   Project Sidecar — ESP32 Auto-Flasher for Windows
echo ==========================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0flash.ps1"
echo.
pause
