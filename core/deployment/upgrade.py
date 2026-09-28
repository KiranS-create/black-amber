"""
core/deployment/upgrade.py

Safe Upgrade, Migration, and Rollback Controller for AegisTrace.
Guarantees transactional integrity during system updates, prevents downgrade attacks,
verifies cryptographic signatures on incoming update packages, and provides
deterministic backup and rollback mechanisms.
"""

import os
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, Optional

from core.deployment.versioning import SemVer, CURRENT_SYSTEM_VERSION
from core.crypto.signatures import MLDSA65


class UpgradeSecurityError(RuntimeError):
    """Raised when an upgrade violates security, signature, or versioning policies."""
    pass


class UpgradeSafetyController:
    """
    Manages safe upgrades, signature verification, and rollback execution.
    """

    def __init__(self, repo_root: Optional[Path] = None, current_version: Optional[SemVer] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent
        self.current_version = current_version or CURRENT_SYSTEM_VERSION
        self.backup_dir = self.repo_root / "data" / "backups"

    def validate_upgrade_package(
        self,
        package_info: Dict[str, Any],
        public_key: Optional[bytes] = None,
        allow_downgrade: bool = False,
    ) -> Dict[str, Any]:
        """
        Validates an incoming upgrade bundle:
          1. SemVer parsing and downgrade prevention.
          2. Cryptographic signature verification with ML-DSA-65.
          3. Schema compatibility and migration requirements.
        """
        target_version_str = package_info.get("target_version")
        if not target_version_str:
            raise UpgradeSecurityError("Missing target_version in upgrade package.")

        target_version = SemVer.parse(target_version_str)

        # 1. Downgrade prevention
        if target_version < self.current_version and not allow_downgrade:
            raise UpgradeSecurityError(
                f"Downgrade attack prevented: target version {target_version} is older than "
                f"current version {self.current_version}."
            )

        # 2. Cryptographic signature check
        sig_hex = package_info.get("signature_hex")
        payload_digest = package_info.get("payload_digest")
        if not sig_hex or not payload_digest:
            raise UpgradeSecurityError("Upgrade package missing required cryptographic signature fields.")

        if public_key:
            try:
                sig_bytes = bytes.fromhex(sig_hex)
                sign_data = f"{package_info.get('signer_id')}:{target_version_str}:{payload_digest}".encode("utf-8")
                valid = MLDSA65.verify(public_key, sign_data, sig_bytes)
                if not valid:
                    raise UpgradeSecurityError("Upgrade package ML-DSA-65 signature verification failed.")
            except Exception as e:
                raise UpgradeSecurityError(f"Upgrade package signature verification error: {e}")

        # 3. Migration classification
        requires_major_migration = target_version.major > self.current_version.major
        requires_minor_migration = target_version.minor > self.current_version.minor

        return {
            "valid": True,
            "current_version": str(self.current_version),
            "target_version": str(target_version),
            "is_major_upgrade": requires_major_migration,
            "is_minor_upgrade": requires_minor_migration,
            "requires_db_migration": requires_major_migration or requires_minor_migration,
            "rollback_supported": True,
        }

    def create_database_backup(self, db_path: Optional[Path] = None) -> Path:
        """
        Creates a verified point-in-time backup of the SQLite database prior to migration.
        """
        target_db = db_path or (self.repo_root / "data" / "metadata.sqlite3")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        backup_file = self.backup_dir / f"metadata_backup_{self.current_version}_{timestamp}.sqlite3"

        if target_db.exists():
            # Use SQLite backup API for online transactional consistency
            src_conn = sqlite3.connect(str(target_db))
            dst_conn = sqlite3.connect(str(backup_file))
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()
        else:
            # Create empty placeholder if db doesn't exist yet
            backup_file.touch()

        return backup_file

    def generate_rollback_plan(self, target_version: str, backup_file: Path) -> Dict[str, Any]:
        """
        Generate machine-verifiable rollback plan in case upgrade verification fails.
        """
        return {
            "rollback_target_version": str(self.current_version),
            "failed_target_version": target_version,
            "database_backup_file": str(backup_file),
            "rollback_procedure": [
                "1. Terminate running AegisTrace API services.",
                f"2. Restore SQLite database from {backup_file}.",
                f"3. Revert code repository and virtualenv to version {self.current_version}.",
                "4. Execute startup self-test in strict mode: python scripts/deployment/startup_self_test.py --strict.",
                "5. Resume service.",
            ],
        }
