#!/usr/bin/env python3
"""
AegisTrace Source Code Integrity Manifest Generator.
===================================================
Generates deterministic SHA-256 digests and file metadata for the canonical
AegisTrace source tree to support independent reproduction and clean-room audit.

Output:
    artifacts/reproduction/source_manifest.json
"""

import sys
import os
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INCLUDED_DIRECTORIES = ["core", "apps", "scripts", "tests", "docs"]
INCLUDED_EXTENSIONS = [".py", ".json", ".md", ".ts", ".tsx", ".css", ".html", ".yaml", ".yml", ".toml"]
EXCLUDED_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".system_generated",
    ".git",
    "coverage",
]


def should_include(path: Path) -> bool:
    """Check if file should be tracked in the canonical manifest."""
    path_str = str(path)
    for excl in EXCLUDED_PATTERNS:
        if excl in path_str:
            return False
    return path.suffix.lower() in INCLUDED_EXTENSIONS


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 digest of a file with normalized byte reading."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_manifest() -> dict:
    """Scan canonical directories and build the source manifest."""
    files_catalog = {}
    all_digests = []

    for dir_name in INCLUDED_DIRECTORIES:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            continue

        for root, _, files in os.walk(dir_path):
            for file in sorted(files):
                file_path = Path(root) / file
                if not should_include(file_path):
                    continue

                rel_path = file_path.relative_to(PROJECT_ROOT).as_posix()
                sha256 = compute_file_sha256(file_path)
                size_bytes = file_path.stat().st_size

                files_catalog[rel_path] = {
                    "sha256": sha256,
                    "size_bytes": size_bytes,
                }
                all_digests.append(f"{rel_path}:{sha256}")

    # Root repository manifest digest
    all_digests.sort()
    tree_hasher = hashlib.sha256()
    for entry in all_digests:
        tree_hasher.update(entry.encode("utf-8"))
    manifest_digest = tree_hasher.hexdigest()

    manifest = {
        "manifest_version": "1.0.0",
        "generated_at_iso": datetime.now(timezone.utc).isoformat(),
        "project_id": "SIH26237",
        "platform": "AegisTrace",
        "total_tracked_files": len(files_catalog),
        "source_tree_merkle_digest": manifest_digest,
        "files": files_catalog,
    }

    out_dir = PROJECT_ROOT / "artifacts" / "reproduction"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "source_manifest.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print(f"[+] Source manifest successfully generated:")
    print(f"    Total Tracked Files: {manifest['total_tracked_files']}")
    print(f"    Source Tree Digest:   {manifest['source_tree_merkle_digest']}")
    print(f"    Manifest Path:        {out_file}")

    return manifest


if __name__ == "__main__":
    generate_manifest()
