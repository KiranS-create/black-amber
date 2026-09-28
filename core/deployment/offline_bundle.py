"""
core/deployment/offline_bundle.py

Offline Wheelhouse Mirror and Air-Gapped Installation Manager for AegisTrace.
Manages deterministic dependency mirroring, cryptographic hash verification,
and air-gapped installation protocols without external network access.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple


class OfflineBundleManager:
    """
    Manages offline wheelhouse bundles and verifies air-gapped package integrity.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent
        self.hashes_file = self.repo_root / "deployment" / "requirements-hashes.txt"
        self.lock_file = self.repo_root / "deployment" / "requirements-lock.txt"

    def parse_requirements_hashes(self, hash_file: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
        """
        Parses deployment/requirements-hashes.txt.
        Returns a mapping:
          package_name_normalized: {
              "raw_name": package_name,
              "version": version_str,
              "hashes": [hash1, hash2, ...]
          }
        """
        target = hash_file or self.hashes_file
        if not target.exists():
            raise FileNotFoundError(f"Requirements hashes file not found: {target}")

        packages: Dict[str, Dict[str, Any]] = {}
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()

        # Split on entries: packages start at beginning of line with name==version
        lines = content.splitlines()
        current_pkg = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "==" in line and not line.startswith("--hash="):
                # Clean line (remove trailing backslash)
                pkg_line = line.rstrip("\\").strip()
                if "==" in pkg_line:
                    pkg_name, ver = pkg_line.split("==", 1)
                    norm_name = pkg_name.lower().replace("-", "_")
                    current_pkg = norm_name
                    packages[current_pkg] = {
                        "raw_name": pkg_name,
                        "version": ver.strip(),
                        "hashes": set(),
                    }
            elif line.startswith("--hash=sha256:"):
                if current_pkg and current_pkg in packages:
                    hash_val = line.split("--hash=sha256:", 1)[1].rstrip("\\").strip()
                    packages[current_pkg]["hashes"].add(hash_val.lower())

        # Convert sets to sorted lists for determinism
        for pkg_info in packages.values():
            pkg_info["hashes"] = sorted(list(pkg_info["hashes"]))

        return packages

    def verify_wheelhouse(self, wheelhouse_dir: Path) -> Dict[str, Any]:
        """
        Validates that an offline wheelhouse contains cryptographically verified
        wheels matching requirements-hashes.txt.
        """
        required_pkgs = self.parse_requirements_hashes()

        if not wheelhouse_dir.exists() or not wheelhouse_dir.is_dir():
            return {
                "status": "MISSING_DIR",
                "wheelhouse_dir": str(wheelhouse_dir),
                "total_required": len(required_pkgs),
                "present_count": 0,
                "missing": sorted(list(required_pkgs.keys())),
                "corrupted": [],
                "untracked": [],
                "wheels": [],
            }

        scanned_wheels = []
        found_pkg_names: Set[str] = set()
        corrupted = []

        all_valid_hashes = set()
        for p in required_pkgs.values():
            all_valid_hashes.update(p["hashes"])

        for root, _, files in os.walk(wheelhouse_dir):
            for filename in files:
                if not (filename.endswith(".whl") or filename.endswith(".tar.gz") or filename.endswith(".zip")):
                    continue

                full_p = Path(root) / filename
                h = hashlib.sha256()
                with open(full_p, "rb") as wf:
                    while chunk := wf.read(65536):
                        h.update(chunk)
                computed_hash = h.hexdigest().lower()

                # Infer package name from filename (e.g. fastapi-0.115.6-py3-none-any.whl)
                pkg_name_inferred = re.split(r"[-_](?=[0-9])", filename)[0].lower().replace("-", "_")

                is_known_hash = computed_hash in all_valid_hashes
                is_known_pkg = pkg_name_inferred in required_pkgs

                wheel_meta = {
                    "filename": filename,
                    "inferred_package": pkg_name_inferred,
                    "sha256": computed_hash,
                    "size_bytes": full_p.stat().st_size,
                    "valid_hash": is_known_hash,
                }
                scanned_wheels.append(wheel_meta)

                if is_known_pkg:
                    expected_hashes = required_pkgs[pkg_name_inferred]["hashes"]
                    if computed_hash in expected_hashes:
                        found_pkg_names.add(pkg_name_inferred)
                    else:
                        corrupted.append({
                            "filename": filename,
                            "package": pkg_name_inferred,
                            "sha256": computed_hash,
                            "expected_hashes": expected_hashes,
                        })

        missing = sorted(list(set(required_pkgs.keys()) - found_pkg_names))
        is_complete = len(missing) == 0 and len(corrupted) == 0

        status = "COMPLETE" if is_complete else ("CORRUPTED" if corrupted else "INCOMPLETE")

        return {
            "status": status,
            "wheelhouse_dir": str(wheelhouse_dir),
            "total_required": len(required_pkgs),
            "present_count": len(found_pkg_names),
            "missing_count": len(missing),
            "corrupted_count": len(corrupted),
            "missing": missing,
            "corrupted": corrupted,
            "wheels": scanned_wheels,
        }

    def generate_wheelhouse_manifest(
        self, wheelhouse_dir: Path, output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Creates a JSON manifest of all wheels in wheelhouse directory with SHA-256 hashes.
        """
        verification = self.verify_wheelhouse(wheelhouse_dir)
        target = output_file or (wheelhouse_dir / "wheelhouse_manifest.json")
        target.parent.mkdir(parents=True, exist_ok=True)

        manifest = {
            "format_version": "1.0.0",
            "wheelhouse_dir": str(wheelhouse_dir),
            "total_wheels": len(verification["wheels"]),
            "status": verification["status"],
            "install_command": self.get_offline_install_command(),
            "wheels": verification["wheels"],
        }

        with open(target, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        return manifest

    def get_offline_install_command(self, wheelhouse_rel_path: str = "./wheelhouse") -> str:
        """
        Generates standard zero-trust air-gapped pip command.
        """
        return (
            f"pip install --no-index --find-links {wheelhouse_rel_path} "
            f"--require-hashes -r deployment/requirements-hashes.txt"
        )
