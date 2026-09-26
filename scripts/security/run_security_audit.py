#!/usr/bin/env python3
"""
SIH26237 - Automated Security Audit & Red-Team Test Runner.
Executes all security tests and generates a formatted finding summary.
"""

import sys
import subprocess
import time
from pathlib import Path

def main():
    print("=" * 70)
    print("  SIH26237 — APPLICATION SECURITY / RED TEAM AUDIT RUNNER")
    print("=" * 70)
    print("Executing tests across: tests/security/**\n")

    start_time = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/security", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start_time

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    print("-" * 70)
    print(f"Audit completed in {elapsed:.2f} seconds.")
    print("-" * 70)

    if result.returncode == 0:
        print("[PASS] All 49 security, red-team, and remediation regression tests passed cleanly.")
        print("  Findings documented in: artifacts/security/SECURITY_AUDIT.md")
        print("  Remediation plan in:    artifacts/security/REMEDIATION_PLAN.md")
        print("=" * 70)
        sys.exit(0)
    else:
        print("[FAIL] Security test failures detected.")
        sys.exit(1)

if __name__ == "__main__":
    main()
