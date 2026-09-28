#!/usr/bin/env python3
"""
scripts/deployment/generate_dependency_inventory.py

CLI tool to generate the machine-readable dependency inventory for AegisTrace.
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.deployment.inventory import DependencyInventoryResolver

def main():
    resolver = DependencyInventoryResolver()
    output_path = resolver.write_inventory()
    inventory = resolver.resolve_inventory()
    summary = inventory["summary"]
    print("=" * 60)
    print("AegisTrace Dependency Inventory Generated Successfully")
    print("=" * 60)
    print(f"Target File: {output_path}")
    print(f"Total Packages: {summary['total_packages']}")
    print(f"Direct Dependencies: {summary['direct_dependencies']}")
    print(f"Transitive Dependencies: {summary['transitive_dependencies']}")
    print(f"Crypto-Sensitive Packages: {len(summary['crypto_sensitive_packages'])}")
    print(f"Runtime-Critical Packages: {len(summary['runtime_critical_packages'])}")
    print("=" * 60)

if __name__ == "__main__":
    main()
