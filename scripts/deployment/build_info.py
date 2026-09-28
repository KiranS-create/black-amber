import datetime
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.config import config

def collect_build_info() -> dict:
    # 1. Git Metadata
    git_commit = "UNKNOWN"
    git_branch = "UNKNOWN"
    try:
        commit_proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False
        )
        if commit_proc.returncode == 0:
            git_commit = commit_proc.stdout.strip()

        branch_proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False
        )
        if branch_proc.returncode == 0:
            git_branch = branch_proc.stdout.strip()
    except Exception:
        pass

    # 2. Node.js & npm Metadata
    node_version = "UNKNOWN"
    npm_version = "UNKNOWN"
    try:
        node_proc = subprocess.run(["node", "--version"], capture_output=True, text=True, check=False)
        if node_proc.returncode == 0:
            node_version = node_proc.stdout.strip()
        npm_proc = subprocess.run(["npm", "--version"], capture_output=True, text=True, check=False)
        if npm_proc.returncode == 0:
            npm_version = npm_proc.stdout.strip()
    except Exception:
        pass

    # 3. Python Package Snapshot
    key_packages = [
        "fastapi", "uvicorn", "pydantic", "cryptography", "pycryptodome",
        "kyber-py", "dilithium-py",
        "reportlab", "pypdf", "pytest", "numpy", "opencv-python", "scipy", "Pillow"
    ]
    pkg_snapshot = {}
    for pkg in key_packages:
        try:
            import importlib.metadata
            pkg_snapshot[pkg] = importlib.metadata.version(pkg)
        except Exception:
            pkg_snapshot[pkg] = "INSTALLED_OR_VENDOR"

    info = {
        "application_name": "SIH26237 — Cryptographic Attribution Platform",
        "version": config.version,
        "git_commit": git_commit,
        "git_branch": git_branch,
        "build_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "python_compiler": platform.python_compiler(),
            "node_version": node_version,
            "npm_version": npm_version
        },
        "dependency_snapshot": pkg_snapshot,
        "offline_ready": True
    }

    # Save to artifacts/deployment
    out_dir = PROJECT_ROOT / "artifacts" / "deployment"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "build_info.json"
    with open(out_file, "w") as f:
        json.dump(info, f, indent=2)

    print(f"[+] Build information saved to: {out_file}")
    return info

if __name__ == "__main__":
    info = collect_build_info()
    print(json.dumps(info, indent=2))
