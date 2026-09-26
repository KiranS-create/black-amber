Write-Host "=== SIH26237 Environment Check (PowerShell / Windows) ===" -ForegroundColor Cyan

# OS Info
$os = Get-CimInstance Win32_OperatingSystem
Write-Host "OS: $($os.Caption) ($($os.Version))"

# Git
try {
    $gitVer = git --version
    Write-Host "Git: $gitVer" -ForegroundColor Green
} catch {
    Write-Host "Git: Not found" -ForegroundColor Red
}

# Python
try {
    $pyVer = python --version
    Write-Host "Python: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "Python: Not found" -ForegroundColor Red
}

# Pip
try {
    $pipVer = python -m pip --version
    Write-Host "Pip: $pipVer" -ForegroundColor Green
} catch {
    Write-Host "Pip: Not found" -ForegroundColor Red
}

# Node.js
try {
    $nodeVer = node --version
    Write-Host "Node.js: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "Node.js: Not found" -ForegroundColor Red
}

# npm
try {
    $npmVer = npm --version
    Write-Host "npm: $npmVer" -ForegroundColor Green
} catch {
    Write-Host "npm: Not found" -ForegroundColor Red
}

# CMake
try {
    $cmakeVer = cmake --version | Select-Object -First 1
    Write-Host "CMake: $cmakeVer" -ForegroundColor Green
} catch {
    Write-Host "CMake: Not found" -ForegroundColor Yellow
}

# OpenSSL
try {
    $sslVer = openssl version
    Write-Host "OpenSSL: $sslVer" -ForegroundColor Green
} catch {
    Write-Host "OpenSSL: Not found in PATH (Python cryptography will provide underlying crypto)" -ForegroundColor Yellow
}

# Docker
try {
    $dockerVer = docker --version
    Write-Host "Docker: $dockerVer" -ForegroundColor Green
} catch {
    Write-Host "Docker: Not found / Optional for v0.1" -ForegroundColor Yellow
}

Write-Host "==========================================================" -ForegroundColor Cyan
