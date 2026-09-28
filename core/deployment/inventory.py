"""
core/deployment/inventory.py

Complete dependency inventory and graph resolution for AegisTrace.
Inspects runtime, direct, transitive, build, test, and cryptographic dependencies,
extracting exact versions, license metadata, integrity classifications,
and dependency relationships.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from pathlib import Path

try:
    import importlib.metadata as metadata_pkg
except ImportError:
    import importlib_metadata as metadata_pkg  # type: ignore


class DependencyType(str, Enum):
    DIRECT = "DIRECT"
    TRANSITIVE = "TRANSITIVE"
    TEST_ONLY = "TEST_ONLY"
    BUILD_TOOLING = "BUILD_TOOLING"
    OPTIONAL = "OPTIONAL"


CRYPTO_SENSITIVE_PACKAGES: Set[str] = {
    "cryptography",
    "pycryptodome",
    "kyber-py",
    "dilithium-py",
    "cffi",
    "pycparser",
}

RUNTIME_CRITICAL_PACKAGES: Set[str] = {
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic-core",
    "pydantic_core",
    "cryptography",
    "pycryptodome",
    "kyber-py",
    "dilithium-py",
    "numpy",
    "scipy",
    "pillow",
    "pypdf",
    "reportlab",
    "python-multipart",
    "httpx",
    "requests",
}

TEST_PACKAGES: Set[str] = {
    "pytest",
    "pluggy",
    "iniconfig",
    "exceptiongroup",
    "tomli",
    "faker",
}


def normalize_pkg_name(name: str) -> str:
    """Canonicalize Python package name per PEP 503."""
    return re.sub(r"[-_.]+", "-", name).lower().strip()


class DependencyInventoryResolver:
    """
    Resolves the complete, machine-readable dependency graph for AegisTrace.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent
        self.req_file = self.repo_root / "deployment" / "requirements.txt"
        self.lock_file = self.repo_root / "deployment" / "requirements-lock.txt"
        self.hashes_file = self.repo_root / "deployment" / "requirements-hashes.txt"

    def parse_requirements_file(self, path: Path) -> Dict[str, str]:
        """Parse requirement file into package_name -> pinned_version map."""
        if not path.exists():
            return {}
        result: Dict[str, str] = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Strip extras e.g. uvicorn[standard]==0.39.0
                clean_line = re.sub(r"\[.*?\]", "", line)
                if "==" in clean_line:
                    pkg, ver = clean_line.split("==", 1)
                    # Strip any hash arguments
                    ver = ver.split("--hash")[0].strip()
                    result[normalize_pkg_name(pkg)] = ver.strip()
                elif ">=" in clean_line or "~=" in clean_line:
                    pkg = re.split(r"[><=~]", clean_line)[0].strip()
                    result[normalize_pkg_name(pkg)] = clean_line.strip()
        return result

    def get_installed_distributions(self) -> Dict[str, Any]:
        """Retrieve installed metadata from active environment."""
        installed: Dict[str, Any] = {}
        try:
            for dist in metadata_pkg.distributions():
                name = normalize_pkg_name(dist.metadata.get("Name", ""))
                if not name:
                    continue
                installed[name] = dist
        except Exception:
            pass
        return installed

    def resolve_inventory(self) -> Dict[str, Any]:
        """
        Produce a complete, machine-readable dependency inventory and graph.
        """
        direct_pins = self.parse_requirements_file(self.req_file)
        locked_pins = self.parse_requirements_file(self.lock_file)
        installed_dists = self.get_installed_distributions()

        # Combine all known relevant package names
        all_pkg_names = set(direct_pins.keys()) | set(locked_pins.keys())

        # Also pull installed dependencies of direct pins
        for name in list(all_pkg_names):
            if name in installed_dists:
                dist = installed_dists[name]
                requires = dist.requires or []
                for req in requires:
                    # Clean requirement string
                    m = re.match(r"^([a-zA-Z0-9_\-\.]+)", req.strip())
                    if m:
                        dep_name = normalize_pkg_name(m.group(1))
                        all_pkg_names.add(dep_name)

        packages: List[Dict[str, Any]] = []
        crypto_packages: List[str] = []
        runtime_critical_packages: List[str] = []

        for pkg in sorted(all_pkg_names):
            is_direct = pkg in direct_pins
            is_test = pkg in TEST_PACKAGES
            is_crypto = pkg in CRYPTO_SENSITIVE_PACKAGES
            is_runtime_crit = pkg in RUNTIME_CRITICAL_PACKAGES

            if is_direct:
                dep_type = DependencyType.DIRECT
            elif is_test:
                dep_type = DependencyType.TEST_ONLY
            else:
                dep_type = DependencyType.TRANSITIVE

            # Installed metadata
            installed_version: Optional[str] = None
            license_str = "UNKNOWN"
            direct_deps: List[str] = []

            if pkg in installed_dists:
                dist = installed_dists[pkg]
                installed_version = dist.version
                license_meta = dist.metadata.get("License")
                if license_meta and license_meta != "UNKNOWN":
                    license_str = license_meta
                else:
                    # Check classifiers
                    classifiers = dist.metadata.get_all("Classifier") or []
                    for c in classifiers:
                        if c.startswith("License ::"):
                            license_str = c.split("::")[-1].strip()
                            break

                requires = dist.requires or []
                for req in requires:
                    # Skip extra conditions if not standard
                    m = re.match(r"^([a-zA-Z0-9_\-\.]+)", req.strip())
                    if m:
                        dep_n = normalize_pkg_name(m.group(1))
                        if dep_n != pkg:
                            direct_deps.append(dep_n)

            pinned_ver = direct_pins.get(pkg) or locked_pins.get(pkg) or installed_version

            if is_crypto:
                crypto_packages.append(pkg)
            if is_runtime_crit:
                runtime_critical_packages.append(pkg)

            pkg_entry = {
                "name": pkg,
                "pinned_version": pinned_ver,
                "installed_version": installed_version,
                "dependency_type": dep_type.value,
                "license": license_str,
                "is_runtime_critical": is_runtime_crit,
                "is_crypto_sensitive": is_crypto,
                "direct_dependencies": sorted(list(set(direct_deps))),
                "package_url": f"pkg:pypi/{pkg}@{pinned_ver or installed_version or 'unknown'}",
                "source": "pypi.org / local-wheelhouse",
                "version_mismatch": bool(
                    pinned_ver and installed_version and pinned_ver != installed_version
                ),
            }
            packages.append(pkg_entry)

        inventory = {
            "schema_version": "1.0.0",
            "application": "AegisTrace",
            "environment": {
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
            },
            "summary": {
                "total_packages": len(packages),
                "direct_dependencies": sum(1 for p in packages if p["dependency_type"] == DependencyType.DIRECT.value),
                "transitive_dependencies": sum(1 for p in packages if p["dependency_type"] == DependencyType.TRANSITIVE.value),
                "test_dependencies": sum(1 for p in packages if p["dependency_type"] == DependencyType.TEST_ONLY.value),
                "crypto_sensitive_packages": sorted(crypto_packages),
                "runtime_critical_packages": sorted(runtime_critical_packages),
            },
            "packages": packages,
        }
        return inventory

    def write_inventory(self, output_path: Optional[Path] = None) -> Path:
        """Write machine-readable inventory to disk."""
        target = output_path or (self.repo_root / "artifacts" / "deployment" / "dependency_inventory.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        inventory = self.resolve_inventory()
        with open(target, "w", encoding="utf-8") as f:
            json.dump(inventory, f, indent=2, sort_keys=True)
        return target
