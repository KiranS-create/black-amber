@echo off
REM SIH26237 — Windows Command Prompt One-Command Demo Launcher
REM Usage: double-click start_demo.bat or run from cmd.exe

echo ==========================================================
echo SIH26237 ONE-COMMAND DEMO START (Command Prompt / Windows)
echo ==========================================================

cd /d "%~dp0\.."
python scripts\deployment\start_demo.py

pause
