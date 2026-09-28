#!/usr/bin/env python3
"""
scripts/deployment/generate_sbom.py

CLI tool to generate standard CycloneDX 1.5 and SPDX 2.3 SBOMs for AegisTrace.
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.deployment.sbom import SBOMManager

def main():
    mgr = SBOMManager()
    artifacts = mgr.generate_all()
    print("=" * 60)
    print("AegisTrace SBOM Artifacts Generated Successfully")
    print("=" * 60)
    for fmt, path in artifacts.items():
        size_kb = path.stat().st_size / 1024.0
        print(f"  - [{fmt.upper()}] {path} ({size_kb:.1f} KB)")
    print("=" * 60)

if __name__ == "__main__":
    main()
