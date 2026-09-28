"""
core/deployment/manifest.py

Deterministic Artifact Integrity Manifest and Verification Engine for AegisTrace.
Computes SHA-256 integrity digests across all security-sensitive repository artifacts:
  - Core Python source files
  - API & security backend implementations
  - Deployment configuration files and dependency lock files
  - Deployment scripts and startup utilities
  - Generated SBOMs and verification artifacts

The verifier strictly detects:
  1. Hash mismatch / modified files
  2. Missing files
  3. Unexpected / injected extra files
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path


SECURITY_SENSITIVE_DIRECTORIES = [
    "core",
    "apps/api",
    "security",
    "deployment",
    "scripts/deployment",
    "artifacts/sbom",
]

ALLOWED_EXTENSIONS = {
    ".py",
    ".txt",
    ".json",
    ".yml",
    ".yaml",
    ".sh",
    ".bat",
    ".ps1",
    ".md",
}

EXCLUDED_PATTERNS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    "release_manifest.json",
    "release_manifest.sig.json",
    ".pyc",
}


def compute_file_sha256(filepath: Path) -> str:
    """Compute deterministic SHA-256 of file content."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class ArtifactManifestManager:
    """
    Generates and verifies cryptographic integrity manifests.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent
        self.manifest_path = self.repo_root / "artifacts" / "deployment" / "release_manifest.json"

    def _should_include_file(self, rel_path: Path) -> bool:
        """Check if file matches security-sensitive criteria."""
        path_str = rel_path.as_posix()
        for excl in EXCLUDED_PATTERNS:
            if excl in path_str:
                return False

        if rel_path.suffix not in ALLOWED_EXTENSIONS:
            if not (rel_path.name.startswith("Dockerfile") or rel_path.name.endswith(".lock")):
                return False

        return True

    def scan_sensitive_files(self) -> List[Path]:
        """Discover all security-sensitive files in the repository."""
        discovered: List[Path] = []
        for d in SECURITY_SENSITIVE_DIRECTORIES:
            dir_path = self.repo_root / d
            if not dir_path.exists():
                continue
            for root, dirs, files in os.walk(dir_path):
                # Filter out pycache dirs in-place
                dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache")]
                for f in files:
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(self.repo_root)
                    if self._should_include_file(rel_p):
                        discovered.append(rel_p)
        return sorted(discovered, key=lambda p: p.as_posix())

    def generate_manifest(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Produce a deterministic artifact integrity manifest.
        """
        target = output_path or self.manifest_path
        target.parent.mkdir(parents=True, exist_ok=True)

        files = self.scan_sensitive_files()
        entries: List[Dict[str, Any]] = []
        hasher_of_manifest = hashlib.sha256()

        for rel_p in files:
            full_p = self.repo_root / rel_p
            sha256 = compute_file_sha256(full_p)
            size = full_p.stat().st_size
            path_str = rel_p.as_posix()

            category = "source"
            if path_str.startswith("deployment/"):
                category = "deployment"
            elif path_str.startswith("scripts/"):
                category = "script"
            elif path_str.startswith("artifacts/sbom/"):
                category = "sbom"

            entry = {
                "path": path_str,
                "sha256": sha256,
                "size_bytes": size,
                "category": category,
            }
            entries.append(entry)
            hasher_of_manifest.update(f"{path_str}:{sha256}:{size}\n".encode("utf-8"))

        manifest = {
            "format_version": "1.0.0",
            "release_id": "v1.0.0",
            "hash_algorithm": "SHA-256",
            "file_count": len(entries),
            "manifest_root_digest": hasher_of_manifest.hexdigest(),
            "files": entries,
        }

        with open(target, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        return manifest

    def verify_manifest(
        self,
        manifest_path: Optional[Path] = None,
        check_unexpected: bool = True,
    ) -> Dict[str, Any]:
        """
        Verify on-disk repository files against integrity manifest.
        Detects modified, missing, and unexpected extra files.
        """
        target = manifest_path or self.manifest_path
        if not target.exists():
            return {
                "status": "INVALID",
                "error": f"Manifest file not found: {target}",
                "matched_count": 0,
                "missing": [],
                "modified": [],
                "unexpected": [],
            }

        with open(target, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        expected_files: Dict[str, Dict[str, Any]] = {
            e["path"]: e for e in manifest_data.get("files", [])
        }

        matched_count = 0
        missing: List[str] = []
        modified: List[Dict[str, Any]] = []

        for path_str, expected in expected_files.items():
            full_p = self.repo_root / path_str
            if not full_p.exists():
                missing.append(path_str)
                continue

            current_sha = compute_file_sha256(full_p)
            current_size = full_p.stat().st_size

            if current_sha != expected["sha256"] or current_size != expected["size_bytes"]:
                modified.append({
                    "path": path_str,
                    "expected_sha256": expected["sha256"],
                    "current_sha256": current_sha,
                    "expected_size": expected["size_bytes"],
                    "current_size": current_size,
                })
            else:
                matched_count += 1

        unexpected: List[str] = []
        if check_unexpected:
            current_scanned = self.scan_sensitive_files()
            current_set = {p.as_posix() for p in current_scanned}
            expected_set = set(expected_files.keys())
            unexpected = sorted(list(current_set - expected_set))

        is_valid = len(missing) == 0 and len(modified) == 0 and len(unexpected) == 0

        return {
            "status": "VALID" if is_valid else "INVALID",
            "release_id": manifest_data.get("release_id"),
            "manifest_root_digest": manifest_data.get("manifest_root_digest"),
            "total_expected": len(expected_files),
            "matched_count": matched_count,
            "missing_count": len(missing),
            "modified_count": len(modified),
            "unexpected_count": len(unexpected),
            "missing": missing,
            "modified": modified,
            "unexpected": unexpected,
        }
