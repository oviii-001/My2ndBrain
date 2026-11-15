@echo off
title My2ndBrain — Jarvis PC Simulator
cd /d "%~dp0"
echo ==========================================================
echo   My2ndBrain — Jarvis Ambient Voice Simulator
echo ==========================================================
echo 1. Push-to-Talk Mode (Press Enter to speak)
echo 2. Hands-Free Wake Word Mode ("Hey Jarvis")
echo.
set /p mode="Select mode [1 or 2, default: 1]: "
if "%mode%"=="2" (
    python pc-simulator/simulator.py
) else (
    python pc-simulator/simulator.py --manual
)
pause
