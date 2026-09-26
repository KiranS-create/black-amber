#!/usr/bin/env python3
"""
SIH26237 — Rapid 30-Second Headless Demo Validator
==================================================

Quickly executes the 3 core live demo scenarios in non-blocking mode:
1. Ground-Truth Leak -> ATTRIBUTED (Bob)
2. Tampered Leak -> INSUFFICIENT_EVIDENCE / CONFLICT
3. Untracked Control -> NO_SIGNAL

Ensures the entire live demo pipeline is functional before presenter starts.
"""

import sys
import time
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.demo.run_live_demo import run_interactive_demo

if __name__ == "__main__":
    t0 = time.perf_counter()
    print("[*] Starting Rapid Headless Demo Validation...")
    run_interactive_demo(auto_mode=True, step_delay=0.1)
    elapsed = time.perf_counter() - t0
    print(f"\n[+] Rapid Demo Validation Completed in {elapsed:.2f} seconds.")
