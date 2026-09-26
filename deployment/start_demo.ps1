# SIH26237 — Windows PowerShell One-Command Demo Launcher
# Usage: powershell -ExecutionPolicy Bypass -File .\deployment\start_demo.ps1

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "SIH26237 ONE-COMMAND DEMO START (PowerShell / Windows)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Launch Python orchestrator
python "$ProjectRoot\scripts\deployment\start_demo.py"
