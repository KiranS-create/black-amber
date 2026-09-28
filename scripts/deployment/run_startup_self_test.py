"""
scripts/deployment/startup_self_test.py

CLI tool to execute AegisTrace startup self-tests and enclave integrity verification.

Usage:
    python scripts/deployment/startup_self_test.py
    python scripts/deployment/startup_self_test.py --strict
"""

import sys
import argparse
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.deployment.startup_self_test import StartupSelfTestRunner, StartupSelfTestFailure


def main():
    parser = argparse.ArgumentParser(description="AegisTrace Startup Self-Test & Enclave Integrity Audit")
    parser.add_argument("--strict", action="store_true", help="Enforce strict production fail-closed verification")

    args = parser.parse_args()
    runner = StartupSelfTestRunner(repo_root=repo_root)

    print("=== AegisTrace Enclave Startup Self-Test ===")
    print(f"[*] Strict fail-closed mode: {args.strict}")

    try:
        report = runner.run_all(fail_closed=args.strict)
    except StartupSelfTestFailure as e:
        print(f"\n[FATAL] Startup self-test failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Overall status: {report['overall_status']}")
    for name, c in report["checks"].items():
        status = c.get("status")
        sym = "[OK]" if status == "PASS" else ("[WARN]" if status == "WARN" else "[FAIL]")
        print(f"    {sym} {name}: {status}")

    if report["overall_status"] == "PASS":
        print("\n[SUCCESS] All enclave startup self-tests PASSED.")
    else:
        print("\n[WARNING] Some self-tests did not pass. Check details above.", file=sys.stderr)
        if args.strict:
            sys.exit(1)


if __name__ == "__main__":
    main()
