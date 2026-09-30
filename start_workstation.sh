#!/usr/bin/env bash
set -e

# =========================================================================
#  AegisTrace (SIH26237) — Forensic Workstation One-Click Launcher (POSIX)
#  Internal Code Name: Black Amber
# =========================================================================

echo ""
echo "========================================================================="
echo "  AEGISTRACE (SIH26237) — ONE-CLICK FORENSIC WORKSTATION LAUNCHER"
echo "  NIST FIPS 203/204 Post-Quantum Zero-Trust Document Traceability"
echo "========================================================================="
echo ""

# 1. Verify Python Availability
PY_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[ERROR] Python is not found in your system PATH."
    echo "Please install Python 3.9+ from https://www.python.org/downloads/"
    exit 1
fi

# 2. Verify Node.js Availability
if ! command -v node >/dev/null 2>&1; then
    echo "[ERROR] Node.js is not found in your system PATH."
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# 3. Switch to Project Root Directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"

# 4. Execute Workstation Launcher
exec "$PY_CMD" scripts/deployment/start_workstation.py
