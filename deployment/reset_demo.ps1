# SIH26237 — Windows PowerShell Demo Environment Reset
# Usage: powershell -ExecutionPolicy Bypass -File .\deployment\reset_demo.ps1

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "SIH26237 DEMO RESET (PowerShell / Windows)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Execute Python reset script
python "$ProjectRoot\scripts\deployment\reset_demo.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Environment reset and baseline fixtures restored." -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Reset script failed with exit code $LASTEXITCODE" -ForegroundColor Red
}
