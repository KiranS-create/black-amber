"""
core/deployment/builder.py

Deterministic Reproducible Build Engine for AegisTrace.
Packages the AegisTrace repository into bit-for-bit reproducible release bundles (.zip and .tar.gz).
Guarantees byte-level determinism across distinct build environments and timestamps by enforcing:
  1. Fixed timestamp normalization via SOURCE_DATE_EPOCH (default: 2024-01-01T00:00:00Z).
  2. Deterministic file ordering (lexicographical sort of relative POSIX paths).
  3. Normalized POSIX permissions (0o644 for files, 0o755 for directories/scripts).
  4. Normalized line endings (\n / LF) for text and source files.
  5. Stripping of volatile user/group metadata, platform paths, and filesystem attributes.
"""

import os
import io
import stat
import time
import zipfile
import tarfile
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

DEFAULT_SOURCE_DATE_EPOCH = 1704067200  # 2024-01-01 00:00:00 UTC
ZIP_FIXED_DATETIME = (2024, 1, 1, 0, 0, 0)

TEXT_EXTENSIONS = {
    ".py", ".txt", ".json", ".yml", ".yaml", ".sh", ".bat", ".ps1", ".md", ".toml", ".ini", ".cfg", ".sql"
}

IGNORED_DIRECTORIES = {
    ".git", "__pycache__", ".pytest_cache", "node_modules", "dist", ".system_generated", "scratch", ".idea", ".vscode"
}

IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".log", ".tmp", ".swp"
}

INCLUDED_ROOT_DIRECTORIES = [
    "core",
    "apps/api",
    "security",
    "deployment",
    "scripts",
    "artifacts/sbom",
    "artifacts/deployment",
    "docs",
    "research/supply_chain",
    "tests/deployment",
]

INCLUDED_ROOT_FILES = [
    "requirements.txt",
    "conftest.py",
    "README.md",
]


class ReproducibleBundleBuilder:
    """
    Builds bit-for-bit reproducible release archives.
    """

    def __init__(self, repo_root: Optional[Path] = None, epoch: Optional[int] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent
        self.epoch = epoch or int(os.environ.get("SOURCE_DATE_EPOCH", DEFAULT_SOURCE_DATE_EPOCH))

    def collect_bundle_files(self) -> List[Tuple[Path, str]]:
        """
        Collect and sort all eligible files lexicographically by relative POSIX path.
        Returns: list of (absolute_path, relative_posix_path)
        """
        collected: List[Tuple[Path, str]] = []

        # 1. Root files
        for f in INCLUDED_ROOT_FILES:
            full_p = self.repo_root / f
            if full_p.is_file():
                collected.append((full_p, f))

        # 2. Subdirectories
        for d in INCLUDED_ROOT_DIRECTORIES:
            dir_path = self.repo_root / d
            if not dir_path.exists():
                continue
            for root, dirs, files in os.walk(dir_path):
                # Filter out ignored dirs in place
                dirs[:] = [sub for sub in dirs if sub not in IGNORED_DIRECTORIES]
                for filename in files:
                    full_p = Path(root) / filename
                    if full_p.suffix in IGNORED_EXTENSIONS:
                        continue
                    if filename.endswith("~"):
                        continue
                    rel_p = full_p.relative_to(self.repo_root).as_posix()
                    collected.append((full_p, rel_p))

        # Sort strictly by POSIX relative path to ensure ordering determinism
        collected.sort(key=lambda item: item[1])
        return collected

    def _read_normalized_bytes(self, full_p: Path) -> bytes:
        """
        Read file contents. For text files, normalize CRLF to LF to ensure
        cross-platform byte reproducibility between Windows, macOS, and Linux.
        """
        raw_bytes = full_p.read_bytes()
        if full_p.suffix.lower() in TEXT_EXTENSIONS:
            # Replace CRLF (\r\n) and CR (\r) with LF (\n)
            normalized = raw_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            return normalized
        return raw_bytes

    def build_zip(self, output_path: Path) -> Dict[str, Any]:
        """
        Generate bit-for-bit deterministic ZIP archive.
        """
        files = self.collect_bundle_files()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for full_p, rel_p in files:
                content = self._read_normalized_bytes(full_p)
                zinfo = zipfile.ZipInfo(filename=rel_p, date_time=ZIP_FIXED_DATETIME)
                
                # Normalize permissions: 0o755 for scripts, 0o644 for regular files
                is_executable = rel_p.endswith((".sh", ".bat", ".ps1")) or full_p.suffix == ""
                file_mode = 0o755 if is_executable else 0o644
                zinfo.external_attr = (stat.S_IFREG | file_mode) << 16
                zinfo.compress_type = zipfile.ZIP_DEFLATED

                zf.writestr(zinfo, content)

        file_sha256 = self._compute_sha256(output_path)
        file_size = output_path.stat().st_size

        return {
            "format": "zip",
            "output_path": str(output_path),
            "file_count": len(files),
            "size_bytes": file_size,
            "sha256": file_sha256,
            "source_date_epoch": self.epoch,
        }

    def build_tar_gz(self, output_path: Path) -> Dict[str, Any]:
        """
        Generate bit-for-bit deterministic tar.gz archive.
        """
        files = self.collect_bundle_files()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use an in-memory buffer or temp file to control gzip header mtime
        tar_buf = io.BytesIO()
        with tarfile.open(fileobj=tar_buf, mode="w") as tf:
            for full_p, rel_p in files:
                content = self._read_normalized_bytes(full_p)
                ti = tarfile.TarInfo(name=rel_p)
                ti.size = len(content)
                ti.mtime = self.epoch
                ti.uid = 0
                ti.gid = 0
                ti.uname = ""
                ti.gname = ""

                is_executable = rel_p.endswith((".sh", ".bat", ".ps1"))
                ti.mode = 0o755 if is_executable else 0o644

                tf.addfile(ti, io.BytesIO(content))

        tar_bytes = tar_buf.getvalue()

        # Write gzip stream with deterministic header mtime
        import gzip
        with gzip.GzipFile(filename="", mode="wb", fileobj=open(output_path, "wb"), mtime=self.epoch) as gz:
            gz.write(tar_bytes)

        file_sha256 = self._compute_sha256(output_path)
        file_size = output_path.stat().st_size

        return {
            "format": "tar.gz",
            "output_path": str(output_path),
            "file_count": len(files),
            "size_bytes": file_size,
            "sha256": file_sha256,
            "source_date_epoch": self.epoch,
        }

    def verify_reproducibility(self, temp_workdir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Executes two independent, clean build passes and verifies bit-for-bit SHA-256 equivalence.
        """
        with tempfile.TemporaryDirectory() as td:
            work_dir = Path(td)
            pass1_path = work_dir / "build_pass_1.zip"
            pass2_path = work_dir / "build_pass_2.zip"

            res1 = self.build_zip(pass1_path)
            res2 = self.build_zip(pass2_path)

            sha1 = res1["sha256"]
            sha2 = res2["sha256"]
            identical = (sha1 == sha2) and (res1["size_bytes"] == res2["size_bytes"])

            # Also verify tar.gz reproducibility
            tpass1 = work_dir / "build_pass_1.tar.gz"
            tpass2 = work_dir / "build_pass_2.tar.gz"
            tres1 = self.build_tar_gz(tpass1)
            tres2 = self.build_tar_gz(tpass2)
            tar_identical = (tres1["sha256"] == tres2["sha256"]) and (tres1["size_bytes"] == tres2["size_bytes"])

            return {
                "reproducible": identical and tar_identical,
                "zip_reproducible": identical,
                "tar_reproducible": tar_identical,
                "zip_sha256": sha1,
                "tar_sha256": tres1["sha256"],
                "file_count": res1["file_count"],
                "source_date_epoch": self.epoch,
                "pass_1_zip": res1,
                "pass_2_zip": res2,
                "pass_1_tar": tres1,
                "pass_2_tar": tres2,
            }

    @staticmethod
    def _compute_sha256(filepath: Path) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
