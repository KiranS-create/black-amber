@echo off
setlocal enabledelayedexpansion

REM =========================================================================
REM  AegisTrace (SIH26237) — Forensic Workstation One-Click Launcher (Windows)
REM  Internal Code Name: Black Amber
REM =========================================================================

echo.
echo =========================================================================
echo   AEGISTRACE (SIH26237) — ONE-CLICK FORENSIC WORKSTATION LAUNCHER
echo   NIST FIPS 203/204 Post-Quantum Zero-Trust Document Traceability
echo =========================================================================
echo.

REM 1. Verify Python Availability
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not found in your system PATH.
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM 2. Verify Node.js Availability
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not found in your system PATH.
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

REM 3. Switch to Project Root Directory
cd /d "%~dp0"

REM 4. Execute Workstation Launcher
python scripts\deployment\start_workstation.py

pause
