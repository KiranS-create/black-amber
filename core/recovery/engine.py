"""
AegisTrace Central Disaster Recovery & Forensic State Recovery Engine.

Orchestrates:
1. End-to-end backup generation with content-addressed storage and ML-DSA-65 post-quantum signed manifests.
2. Optional authenticated AES-256-GCM encryption with tenant AAD binding.
3. Monotonic rollback protection and cross-tenant isolation enforcement.
4. Coordinated subsystem restoration (ledger, lineage, telemetry, evidence, keys).
5. Generation of comprehensive, machine-readable RecoveryVerificationReports.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
import time
from typing import Dict, List, Optional, Tuple, Set, Any
from pydantic import BaseModel

from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from core.lineage.models import DocumentRoot, CopyInstance, AccessSession, ForwardingEvent, ExportEvent
from core.lineage.storage import LineageStorage
from core.telemetry.event import ForensicEvent
from core.telemetry.provider import InMemoryTelemetryProvider
from core.attribution.evidence import EvidenceBundle
from core.crypto.lifecycle.models import KeyRecord, KeyState
from core.crypto.signatures import MLDSA65

from core.recovery.models import (
    SignedBackupManifest,
    BackupType,
    BackupObjectRecord,
    RecoveryState,
    FinalRecoveryOutcome,
    RecoveryVerificationReport,
    ComponentRecoveryStatus,
)
from core.recovery.format import (
    ContentAddressedStore,
    BackupPackageBuilder,
    canonical_json_bytes,
)
from core.recovery.crypto import BackupCryptoEngine
from core.recovery.chain import BackupChainManager, ChainValidationStatus
from core.recovery.ledger_recovery import LedgerRecoveryEngine, LedgerRecoveryResult
from core.recovery.lineage_recovery import LineageRecoveryEngine, LineageRecoveryResult
from core.recovery.telemetry_recovery import TelemetryRecoveryEngine, TelemetryRecoveryResult
from core.recovery.evidence_recovery import EvidencePackageRecoveryEngine, EvidenceRecoveryResult
from core.recovery.key_recovery import KeyRecoveryEngine, KeyOperationalStatus
from core.recovery.audit import RecoveryAuditLog


class BackupEngineError(Exception):
    """Base error raised during backup operations."""
    pass


class BackupIntegrityError(BackupEngineError):
    """Raised when backup payload or manifest integrity verification fails."""
    pass


class BackupTenantMismatchError(BackupEngineError):
    """Raised on unauthorized cross-tenant backup or restoration attempts."""
    pass


class DisasterRecoveryEngine:
    """
    Central recovery engine coordinating end-to-end backup and restoration workflows.
    """

    def __init__(
        self,
        store: Optional[ContentAddressedStore] = None,
        audit_log: Optional[RecoveryAuditLog] = None,
    ):
        self.store = store or ContentAddressedStore()
        self.audit_log = audit_log or RecoveryAuditLog()
        
        # Monotonic state guards (per tenant)
        self._tenant_highest_sequence: Dict[str, int] = {}
        self._tenant_highest_epoch: Dict[str, int] = {}
        self._tenant_trusted_ledger_tips: Dict[str, str] = {}

    def set_trusted_watermark(
        self,
        tenant_id: str,
        sequence: int,
        epoch: int = 1,
        ledger_tip_hash: Optional[str] = None
    ) -> None:
        """Sets the known trusted monotonic state watermark for a tenant."""
        self._tenant_highest_sequence[tenant_id] = sequence
        self._tenant_highest_epoch[tenant_id] = epoch
        if ledger_tip_hash:
            self._tenant_trusted_ledger_tips[tenant_id] = ledger_tip_hash

    # ==========================================================================
    # 1. Backup Creation Workflow
    # ==========================================================================

    def create_backup(
        self,
        tenant_id: str,
        backup_type: BackupType,
        datasets: Dict[str, List[Any]],
        signer_id: str,
        signing_private_key_bytes: bytes,
        signing_public_key_bytes: bytes,
        parent_manifest: Optional[SignedBackupManifest] = None,
        encryption_passphrase: Optional[str] = None,
        source_system_id: str = "aegis_node_primary",
        operator_role: str = "SECURITY_ADMIN",
    ) -> SignedBackupManifest:
        """
        Creates, content-addresses, and cryptographically signs a forensic backup.
        """
        builder = BackupPackageBuilder(self.store)
        backup_seq = 0 if backup_type == BackupType.FULL else (parent_manifest.backup_sequence + 1 if parent_manifest else 1)
        backup_id = f"bkp_{hashlib.sha256(os.urandom(16)).hexdigest()[:20]}"

        # Ingest datasets into content-addressed store
        for ds_name, items in datasets.items():
            if encryption_passphrase:
                # Encrypt dataset payload with authenticated AAD binding
                raw_bytes = canonical_json_bytes(items)
                envelope = BackupCryptoEngine.encrypt_payload(
                    plaintext=raw_bytes,
                    passphrase=encryption_passphrase,
                    tenant_id=tenant_id,
                    backup_id=backup_id,
                    backup_sequence=backup_seq,
                )
                builder.add_dataset(ds_name, [envelope], tenant_id=tenant_id)
            else:
                builder.add_dataset(ds_name, items, tenant_id=tenant_id)

        merkle_root = builder.compute_merkle_root()

        # Build manifest
        manifest = SignedBackupManifest(
            backup_id=backup_id,
            backup_type=backup_type,
            tenant_id=tenant_id,
            backup_sequence=backup_seq,
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            source_system_id=source_system_id,
            schema_version="1.0",
            application_version="2.0.0",
            parent_backup_id=parent_manifest.backup_id if parent_manifest else None,
            parent_backup_commitment=parent_manifest.cryptographic_digest if parent_manifest else None,
            datasets=list(builder.datasets),
            objects=builder.objects,
            merkle_root=merkle_root,
            cryptographic_digest="",  # Updated during signing
            is_encrypted=bool(encryption_passphrase),
            encryption_algorithm="AES-256-GCM" if encryption_passphrase else None,
            key_derivation_algorithm="HKDF-SHA256" if encryption_passphrase else None,
            signer_id=signer_id,
            signer_public_key_b64=base64_encode(signing_public_key_bytes),
            signature_b64="",  # Updated during signing
        )

        signed_manifest = BackupCryptoEngine.sign_manifest(manifest, signing_private_key_bytes)

        # Update monotonic tracker
        self._tenant_highest_sequence[tenant_id] = max(
            self._tenant_highest_sequence.get(tenant_id, -1),
            backup_seq
        )

        # Audit log
        self.audit_log.record_action(
            operator_id=signer_id,
            operator_role=operator_role,
            action=f"BACKUP_CREATED_{backup_type.value}",
            tenant_id=tenant_id,
            target_backup_id=backup_id,
            previous_state="NORMAL",
            new_state="BACKUP_READY",
            result="SUCCESS",
        )

        return signed_manifest

    # ==========================================================================
    # 2. Restoration & State Reconstitution Workflow
    # ==========================================================================

    def restore_backup(
        self,
        manifest: SignedBackupManifest,
        expected_tenant_id: str,
        encryption_passphrase: Optional[str] = None,
        authority_public_key_bytes: Optional[bytes] = None,
        allow_rollback: bool = False,
        allow_tail_truncation: bool = False,
        operator_id: str = "recovery_operator",
        operator_role: str = "RECOVERY_OPERATOR",
        dual_authorizer_id: Optional[str] = None,
    ) -> RecoveryVerificationReport:
        """
        Executes complete restoration from a signed backup manifest.
        Validates signatures, tenant isolation, monotonic sequence rollback,
        and reconstitutes subsystem state stores.
        """
        start_time = time.perf_counter()
        recovery_id = f"rec_{hashlib.sha256(os.urandom(16)).hexdigest()[:20]}"
        errors: List[str] = []
        warnings: List[str] = []
        component_statuses: Dict[str, ComponentRecoveryStatus] = {}

        # 1. Tenant Boundary Validation
        tenant_status = RecoveryState.VALID_RECOVERY
        if manifest.tenant_id != expected_tenant_id:
            tenant_status = RecoveryState.TENANT_MISMATCH
            errors.append(
                f"TENANT_ISOLATION_VIOLATION: Manifest tenant '{manifest.tenant_id}' != expected '{expected_tenant_id}'"
            )

        # 2. Cryptographic Manifest Signature Verification
        is_valid_sig, sig_err = BackupCryptoEngine.verify_manifest(manifest, authority_public_key_bytes)
        if not is_valid_sig:
            errors.append(f"MANIFEST_SIGNATURE_INVALID: {sig_err}")

        # 3. Monotonic Rollback Guard
        rollback_status = RecoveryState.VALID_RECOVERY
        highest_seq = self._tenant_highest_sequence.get(expected_tenant_id, -1)
        if highest_seq != -1 and manifest.backup_sequence < highest_seq:
            if not allow_rollback:
                rollback_status = RecoveryState.ROLLBACK_DETECTED
                errors.append(
                    f"ROLLBACK_DETECTED: Attempted restore of sequence {manifest.backup_sequence} < current highest {highest_seq}"
                )
            else:
                if not dual_authorizer_id:
                    rollback_status = RecoveryState.ROLLBACK_DETECTED
                    errors.append("ROLLBACK_OVERRIDE_FAILED: Intentional rollback requires dual-authorizer approval")
                else:
                    rollback_status = RecoveryState.PARTIAL_RECOVERY
                    warnings.append(
                        f"INTENTIONAL_ROLLBACK: Sequence {manifest.backup_sequence} restored with dual-authorization ({dual_authorizer_id})"
                    )

        # If security checks failed early, produce failure report immediately
        if errors:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            report = RecoveryVerificationReport(
                recovery_id=recovery_id,
                backup_id=manifest.backup_id,
                tenant_id=expected_tenant_id,
                ledger_status=RecoveryState.UNRECOVERABLE,
                lineage_status=RecoveryState.UNRECOVERABLE,
                telemetry_status=RecoveryState.UNRECOVERABLE,
                identity_status=RecoveryState.UNRECOVERABLE,
                evidence_status=RecoveryState.UNRECOVERABLE,
                key_status=RecoveryState.UNRECOVERABLE,
                rollback_status=rollback_status,
                chain_status=RecoveryState.CORRUPTED_RECOVERY,
                tenant_boundary_status=tenant_status,
                final_recovery_state=FinalRecoveryOutcome.RECOVERY_FAILED,
                components=component_statuses,
                warnings=warnings,
                errors=errors,
                recovery_duration_ms=duration_ms
            )
            self.audit_log.record_action(
                operator_id=operator_id,
                operator_role=operator_role,
                action="RESTORE_FAILED",
                tenant_id=expected_tenant_id,
                target_backup_id=manifest.backup_id,
                target_recovery_id=recovery_id,
                previous_state="RESTORING",
                new_state="FAILED",
                result="FAILED",
                failure_reason="; ".join(errors),
                dual_authorizer_id=dual_authorizer_id
            )
            return report

        # 4. Ingest and Unpack Datasets
        unpacked_datasets: Dict[str, List[Any]] = {}
        for obj_rec in manifest.objects:
            try:
                raw_obj = self.store.get_object(obj_rec.object_id)
                if manifest.is_encrypted:
                    if not encryption_passphrase:
                        raise ValueError("MISSING_PASSPHRASE: Backup is encrypted but no passphrase provided")
                    envelope = raw_obj[0]
                    decrypted_bytes = BackupCryptoEngine.decrypt_payload(
                        envelope=envelope,
                        passphrase=encryption_passphrase,
                        expected_tenant_id=expected_tenant_id,
                        expected_backup_id=manifest.backup_id,
                        expected_sequence=manifest.backup_sequence,
                    )
                    items = json.loads(decrypted_bytes.decode('utf-8'))
                    unpacked_datasets[obj_rec.dataset_type] = items
                else:
                    unpacked_datasets[obj_rec.dataset_type] = raw_obj
            except Exception as ex:
                errors.append(f"OBJECT_EXTRACTION_FAILED ({obj_rec.object_id}): {str(ex)}")

        if errors:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return RecoveryVerificationReport(
                recovery_id=recovery_id,
                backup_id=manifest.backup_id,
                tenant_id=expected_tenant_id,
                rollback_status=rollback_status,
                chain_status=RecoveryState.CORRUPTED_RECOVERY,
                tenant_boundary_status=tenant_status,
                final_recovery_state=FinalRecoveryOutcome.RECOVERY_FAILED,
                components=component_statuses,
                warnings=warnings,
                errors=errors,
                recovery_duration_ms=duration_ms
            )

        # 5. Component Restoration Sub-Pipelines

        # --- A. Ledger Recovery ---
        ledger_status = RecoveryState.VALID_RECOVERY
        if "ledger_events" in unpacked_datasets:
            raw_evs = [EvidenceEvent(**e) for e in unpacked_datasets["ledger_events"]]
            l_res = LedgerRecoveryEngine.recover_ledger(
                candidate_events=raw_evs,
                allow_tail_truncation=allow_tail_truncation,
            )
            ledger_status = l_res.state
            component_statuses["ledger"] = ComponentRecoveryStatus(
                component_name="ledger",
                status=l_res.state,
                records_recovered=l_res.events_recovered,
                records_quarantined=l_res.events_quarantined,
                errors=l_res.errors
            )
            if l_res.errors:
                errors.extend(l_res.errors)

        # --- B. Lineage Recovery ---
        lineage_status = RecoveryState.VALID_RECOVERY
        if "lineage_copies" in unpacked_datasets or "lineage_roots" in unpacked_datasets:
            raw_roots = [DocumentRoot(**r) for r in unpacked_datasets.get("lineage_roots", [])]
            raw_copies = [CopyInstance(**c) for c in unpacked_datasets.get("lineage_copies", [])]
            lin_res, _ = LineageRecoveryEngine.recover_lineage(
                roots=raw_roots,
                copies=raw_copies,
                expected_tenant_id=expected_tenant_id,
            )
            lineage_status = lin_res.state
            component_statuses["lineage"] = ComponentRecoveryStatus(
                component_name="lineage",
                status=lin_res.state,
                records_recovered=lin_res.copies_recovered,
                errors=lin_res.errors
            )
            if lin_res.errors:
                errors.extend(lin_res.errors)
            if lin_res.warnings:
                warnings.extend(lin_res.warnings)

        # --- C. Telemetry Recovery ---
        telemetry_status = RecoveryState.VALID_RECOVERY
        if "telemetry_events" in unpacked_datasets:
            raw_telemetry = [ForensicEvent(**t) for t in unpacked_datasets["telemetry_events"]]
            tel_res, _ = TelemetryRecoveryEngine.recover_telemetry(raw_telemetry)
            telemetry_status = tel_res.state
            component_statuses["telemetry"] = ComponentRecoveryStatus(
                component_name="telemetry",
                status=tel_res.state,
                records_recovered=tel_res.events_recovered,
                records_quarantined=tel_res.duplicates_detected,
                errors=tel_res.errors
            )
            if tel_res.errors:
                errors.extend(tel_res.errors)

        # --- D. Key Status ---
        key_status = RecoveryState.VALID_RECOVERY
        if "keys" in unpacked_datasets:
            key_recs = [KeyRecord(**k) for k in unpacked_datasets["keys"]]
            comp_count = sum(1 for k in key_recs if k.status == KeyState.COMPROMISED)
            component_statuses["keys"] = ComponentRecoveryStatus(
                component_name="keys",
                status=RecoveryState.VALID_RECOVERY,
                records_recovered=len(key_recs),
            )

        # --- E. Evidence Packages ---
        evidence_status = RecoveryState.VALID_RECOVERY
        if "evidence_packages" in unpacked_datasets:
            raw_bundles = [EvidenceBundle(**b) for b in unpacked_datasets["evidence_packages"]]
            ev_res, _ = EvidencePackageRecoveryEngine.recover_evidence_bundles(raw_bundles)
            evidence_status = ev_res.state
            component_statuses["evidence"] = ComponentRecoveryStatus(
                component_name="evidence",
                status=ev_res.state,
                records_recovered=ev_res.bundles_recovered,
                errors=ev_res.errors
            )
            if ev_res.errors:
                errors.extend(ev_res.errors)

        # 6. Synthesize Executive Outcome
        if any(s == RecoveryState.CORRUPTED_RECOVERY for s in (ledger_status, lineage_status, telemetry_status)):
            final_outcome = FinalRecoveryOutcome.RECOVERY_FAILED
        elif any(s == RecoveryState.PARTIAL_RECOVERY for s in (ledger_status, lineage_status, telemetry_status)):
            final_outcome = FinalRecoveryOutcome.PARTIALLY_RECOVERED
        elif errors:
            final_outcome = FinalRecoveryOutcome.RECOVERY_FAILED
        elif rollback_status == RecoveryState.PARTIAL_RECOVERY:
            final_outcome = FinalRecoveryOutcome.RECOVERY_REQUIRES_REVIEW
        else:
            final_outcome = FinalRecoveryOutcome.RECOVERED

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        report = RecoveryVerificationReport(
            recovery_id=recovery_id,
            backup_id=manifest.backup_id,
            tenant_id=expected_tenant_id,
            ledger_status=ledger_status,
            lineage_status=lineage_status,
            telemetry_status=telemetry_status,
            identity_status=RecoveryState.VALID_RECOVERY,
            evidence_status=evidence_status,
            key_status=key_status,
            rollback_status=rollback_status,
            chain_status=RecoveryState.VALID_RECOVERY,
            tenant_boundary_status=tenant_status,
            final_recovery_state=final_outcome,
            components=component_statuses,
            warnings=warnings,
            errors=errors,
            recovery_duration_ms=duration_ms
        )

        # Update monotonic tracker upon success
        if final_outcome in (FinalRecoveryOutcome.RECOVERED, FinalRecoveryOutcome.PARTIALLY_RECOVERED):
            self._tenant_highest_sequence[expected_tenant_id] = max(
                self._tenant_highest_sequence.get(expected_tenant_id, -1),
                manifest.backup_sequence
            )

        # Audit
        self.audit_log.record_action(
            operator_id=operator_id,
            operator_role=operator_role,
            action=f"RESTORE_COMPLETED_{final_outcome.value}",
            tenant_id=expected_tenant_id,
            target_backup_id=manifest.backup_id,
            target_recovery_id=recovery_id,
            previous_state="RESTORING",
            new_state=final_outcome.value,
            result="SUCCESS" if final_outcome != FinalRecoveryOutcome.RECOVERY_FAILED else "FAILED",
            failure_reason="; ".join(errors) if errors else None,
            dual_authorizer_id=dual_authorizer_id
        )

        return report


def base64_encode(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode('utf-8')


# Aliases for subsystem naming compatibility
ForensicBackupEngine = DisasterRecoveryEngine
ForensicRestoreEngine = DisasterRecoveryEngine


# Aliases for subsystem compatibility
ForensicBackupEngine = DisasterRecoveryEngine


class BackupEngineError(RuntimeError):
    """Raised on general backup engine errors."""
    pass


class BackupIntegrityError(ValueError):
    """Raised on backup integrity validation failures."""
    pass


class BackupTenantMismatchError(PermissionError):
    """Raised when cross-tenant backup or restore is attempted."""
    pass
