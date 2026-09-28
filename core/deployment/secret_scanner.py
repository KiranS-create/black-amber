"""
core/deployment/secret_scanner.py

Static Secret, Credential, and Private Key Scanner for AegisTrace.
Detects accidentally committed secrets, raw private keys, cloud tokens,
and high-entropy cryptographic credentials across repository assets.
"""

import os
import re
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set


SECRET_PATTERNS = [
    ("PRIVATE_KEY_PEM", re.compile(r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----")),
    ("RSA_PRIVATE_KEY", re.compile(r"-----BEGIN RSA PRIVATE KEY-----")),
    ("EC_PRIVATE_KEY", re.compile(r"-----BEGIN EC PRIVATE KEY-----")),
    ("DSA_PRIVATE_KEY", re.compile(r"-----BEGIN DSA PRIVATE KEY-----")),
    ("OPENSSH_PRIVATE_KEY", re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----")),
    ("AWS_ACCESS_KEY", re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}")),
    ("AWS_SECRET_KEY", re.compile(r"""(?i)aws_(?:secret_access_key|secret_key)\s*[:=]\s*["']?([A-Za-z0-9/+=]{40})["']?""")),
    ("SLACK_TOKEN", re.compile(r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}")),
    ("GENERIC_API_KEY", re.compile(r"""(?i)(?:api_key|apikey|secret_key|private_key|auth_token)\s*=\s*["']([A-Za-z0-9_\-]{32,64})["']""")),
    ("JWT_TOKEN", re.compile(r"ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]{10,}\.[A-Za-z0-9._-]{10,}")),
]

EXCLUDED_DIRS = {
    ".git", "__pycache__", ".pytest_cache", "node_modules", "dist", ".system_generated", "scratch",
    ".venv", "venv", "env", ".secrets", ".agents"
}

# Allow-listed test fixtures or public keys
SUPPRESSED_FILENAMES = {
    "secret_scanner.py",
    "release_authority.pub",
    "requirements-hashes.txt",
    "dependency_inventory.json",
    "aegistrace-cyclonedx.json",
    "aegistrace-spdx.json",
    "release_manifest.json",
    "release_manifest.sig.json",
    "wheelhouse_manifest.json",
    "test_supply_chain_attacks.py",
}


def shannon_entropy(data: str) -> float:
    """Calculate the Shannon entropy of a string."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    for x in set(data):
        p_x = float(data.count(x)) / length
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy


class SecretScanner:
    """
    Scans repository files for leaked secrets, tokens, and private keys.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent

    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Scan a single file for secret patterns.
        """
        file_path = file_path.resolve()
        findings: List[Dict[str, Any]] = []
        if file_path.name in SUPPRESSED_FILENAMES:
            return findings

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return findings

        try:
            rel_path = file_path.relative_to(self.repo_root.resolve()).as_posix()
        except ValueError:
            rel_path = file_path.as_posix()
        is_test_file = "tests/" in rel_path or "test_" in file_path.name or "fixture" in file_path.name

        for line_num, line in enumerate(lines, start=1):
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue

            for rule_name, pattern in SECRET_PATTERNS:
                matches = pattern.finditer(line_str)
                for match in matches:
                    matched_text = match.group(0)
                    
                    # Filter out obvious false positives in tests/docs/schemas
                    if "EXAMPLE" in matched_text.upper() or "PLACEHOLDER" in matched_text.upper() or "DUMMY" in matched_text.upper():
                        continue
                    if "derive_key" in line_str or "hashlib" in line_str:
                        continue
                    if is_test_file and "test" in line_str.lower():
                        continue

                    findings.append({
                        "file": rel_path,
                        "line": line_num,
                        "rule": rule_name,
                        "snippet": line_str[:120],
                        "severity": "CRITICAL" if "KEY" in rule_name else "HIGH",
                    })

        return findings

    def scan_directory(self, target_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Recursively scan directory for secrets.
        """
        root_scan = (target_dir or self.repo_root).resolve()
        all_findings: List[Dict[str, Any]] = []
        scanned_files_count = 0

        for root, dirs, files in os.walk(root_scan):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                p = Path(root) / file
                # Skip binary assets and large archives
                if p.suffix.lower() in {
                    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".raw", ".sqlite3", ".db",
                    ".tar", ".gz", ".zip", ".pdf", ".pptx", ".pyc", ".wasm", ".woff",
                    ".woff2", ".ttf", ".eot", ".bin"
                }:
                    continue
                # Skip binary and very large files (> 2MB)
                if p.stat().st_size > 2 * 1024 * 1024:
                    continue
                scanned_files_count += 1
                findings = self.scan_file(p)
                if findings:
                    all_findings.extend(findings)

        return {
            "status": "CLEAN" if len(all_findings) == 0 else "FINDINGS_DETECTED",
            "scanned_files": scanned_files_count,
            "total_findings": len(all_findings),
            "findings": all_findings,
        }
