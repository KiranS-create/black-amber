"""
AegisTrace Normalized Forensic Event Model.

Provides the canonical, strongly-typed ForensicEvent model that normalizes
operational telemetry collected from heterogeneous sources (EDR, DLP, CASB,
IdP, Network, Cloud, USB, Print, Public Uploads, and Physical Forensics).

CRITICAL FORENSIC INVARIANTS:
1. Never conflate Account, Device, Network Source, Forwarding Event,
   Downstream Holder, and Human Operator.
2. An event proves an action occurred on a system; it does NOT prove
   who was physically operating the keyboard unless corroborated.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from core.telemetry.models import (
    TelemetrySource,
    IntegrityLevel,
    TelemetryTrustLevel,
    DeviceAttestationState,
    CanonicalEventType,
    BaseTelemetryEvidence,
    EndpointEvidence,
    IdentityProviderEvidence,
    NetworkEvidence,
    DLPEvent,
    CASBEvent,
    EmailGatewayEvent,
    CloudAccessEvent,
    USBTransferEvent,
    PrintEvent,
    BrowserAccessEvent,
    PublicUploadEvent,
    DeviceForensicEvidence,
    PhysicalAccessEvidence,
)


class ForensicEvent(BaseModel):
    """
    Canonical normalized forensic event record.
    Unifies all heterogeneous telemetry signals into a common schema
    for graph ingestion, temporal sequencing, and fusion analysis.
    """
    event_id: str
    timestamp: datetime
    event_type: str
    canonical_type: CanonicalEventType = CanonicalEventType.DOCUMENT_CREATED
    source_system: TelemetrySource
    subject_type: str = "ACCOUNT"  # ACCOUNT, DEVICE, NETWORK, ANONYMOUS, HARDWARE
    subject_id: Optional[str] = None
    recipient_principal_id: Optional[str] = None
    device_id: Optional[str] = None
    device_attestation_state: DeviceAttestationState = DeviceAttestationState.DEVICE_UNKNOWN
    trust_level: TelemetryTrustLevel = TelemetryTrustLevel.OBSERVED
    network_id: Optional[str] = None
    resource_id: Optional[str] = None
    artifact_hash: Optional[str] = None
    copy_id: Optional[str] = None
    session_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    compound_event_id: Optional[str] = None
    cluster_id: Optional[str] = None
    location_metadata: Dict[str, Any] = Field(default_factory=dict)
    integrity_status: IntegrityLevel = IntegrityLevel.MEDIUM_LOG
    source_reliability: float = Field(default=0.8, ge=0.0, le=1.0)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)

    def compute_event_fingerprint(self) -> str:
        """
        Deterministic SHA-256 fingerprint of the core invariant event fields.
        Used for event deduplication and tamper detection.
        """
        # Normalize timestamp to UTC ISO string
        ts_str = self.timestamp.astimezone(timezone.utc).isoformat() if self.timestamp.tzinfo else self.timestamp.isoformat()
        canonical_dict = {
            "ts": ts_str,
            "source": self.source_system.value,
            "type": self.event_type,
            "subj_type": self.subject_type,
            "subj_id": self.subject_id or "",
            "dev_id": self.device_id or "",
            "net_id": self.network_id or "",
            "res_id": self.resource_id or "",
            "hash": self.artifact_hash or "",
            "copy": self.copy_id or "",
            "sess": self.session_id or "",
        }
        encoded = json.dumps(canonical_dict, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def from_evidence(cls, evidence: BaseTelemetryEvidence) -> "ForensicEvent":
        """
        Factory method normalizing any BaseTelemetryEvidence subclass into ForensicEvent.
        """
        raw = evidence.raw_metadata.copy()
        loc = {}
        subj_type = "ACCOUNT"
        subj_id = evidence.actor_account_id

        # Specific field extractions per telemetry type
        if isinstance(evidence, EndpointEvidence):
            raw.update({
                "process_name": evidence.process_name,
                "process_pid": evidence.process_pid,
                "process_path": evidence.process_path,
                "parent_process_name": evidence.parent_process_name,
                "file_operation": evidence.file_operation,
            })
            if not subj_id and evidence.device_id:
                subj_type = "DEVICE"
                subj_id = evidence.device_id

        elif isinstance(evidence, IdentityProviderEvidence):
            raw.update({
                "auth_method": evidence.auth_method,
                "mfa_verified": evidence.mfa_verified,
                "tenant_id": evidence.tenant_id,
                "user_agent": evidence.user_agent,
            })
            subj_type = "ACCOUNT"
            if evidence.auth_client_ip:
                evidence.network_id = evidence.auth_client_ip

        elif isinstance(evidence, NetworkEvidence):
            raw.update({
                "source_ip": evidence.source_ip,
                "source_port": evidence.source_port,
                "destination_ip": evidence.destination_ip,
                "destination_port": evidence.destination_port,
                "protocol": evidence.protocol,
                "bytes_transferred": evidence.bytes_transferred,
                "is_vpn_or_proxy": evidence.is_vpn_or_proxy,
                "is_tor_exit": evidence.is_tor_exit,
            })
            if evidence.actor_account_id:
                subj_type = "ACCOUNT"
                subj_id = evidence.actor_account_id
            else:
                subj_type = "NETWORK"
                subj_id = evidence.source_ip
            if not evidence.network_id:
                evidence.network_id = evidence.source_ip

        elif isinstance(evidence, DLPEvent):
            raw.update({
                "policy_name": evidence.policy_name,
                "policy_action": evidence.policy_action,
                "destination_type": evidence.destination_type,
                "severity": evidence.severity,
            })

        elif isinstance(evidence, CASBEvent):
            raw.update({
                "cloud_service": evidence.cloud_service,
                "sharing_scope": evidence.sharing_scope,
                "operation": evidence.operation,
            })

        elif isinstance(evidence, EmailGatewayEvent):
            raw.update({
                "sender_address": evidence.sender_address,
                "recipient_addresses": evidence.recipient_addresses,
                "subject_hash": evidence.subject_hash,
                "attachment_filename": evidence.attachment_filename,
                "message_id": evidence.message_id,
            })
            subj_type = "ACCOUNT"
            subj_id = evidence.sender_address
            if evidence.attachment_hash and not evidence.document_hash:
                evidence.document_hash = evidence.attachment_hash

        elif isinstance(evidence, CloudAccessEvent):
            raw.update({
                "bucket_or_vault": evidence.bucket_or_vault,
                "action": evidence.action,
                "caller_arn_or_sa": evidence.caller_arn_or_sa,
            })
            if evidence.caller_arn_or_sa:
                subj_type = "ACCOUNT"
                subj_id = evidence.caller_arn_or_sa

        elif isinstance(evidence, USBTransferEvent):
            raw.update({
                "vendor_id": evidence.vendor_id,
                "product_id": evidence.product_id,
                "volume_serial": evidence.volume_serial,
                "volume_label": evidence.volume_label,
                "drive_letter_or_mount": evidence.drive_letter_or_mount,
                "bytes_written": evidence.bytes_written,
            })
            if not subj_id and evidence.volume_serial:
                subj_type = "HARDWARE"
                subj_id = f"USB:{evidence.volume_serial}"

        elif isinstance(evidence, PrintEvent):
            raw.update({
                "printer_name": evidence.printer_name,
                "printer_ip": evidence.printer_ip,
                "pages_printed": evidence.pages_printed,
                "has_mic_yellow_dots": evidence.has_mic_yellow_dots,
                "mic_decoded_serial": evidence.mic_decoded_serial,
            })
            if not subj_id and evidence.mic_decoded_serial:
                subj_type = "HARDWARE"
                subj_id = f"PRINTER:{evidence.mic_decoded_serial}"

        elif isinstance(evidence, BrowserAccessEvent):
            raw.update({
                "browser_name": evidence.browser_name,
                "tab_url_domain": evidence.tab_url_domain,
                "is_incognito": evidence.is_incognito,
                "download_path": evidence.download_path,
            })

        elif isinstance(evidence, PublicUploadEvent):
            raw.update({
                "platform_name": evidence.platform_name,
                "public_url": evidence.public_url,
                "uploader_account": evidence.uploader_account,
                "tls_fingerprint": evidence.tls_fingerprint,
            })
            subj_type = "ANONYMOUS"
            subj_id = evidence.uploader_account or "anonymous_uploader"

        elif isinstance(evidence, DeviceForensicEvidence):
            raw.update({
                "sensor_model": evidence.sensor_model,
                "prnu_fingerprint": evidence.prnu_fingerprint,
                "mic_serial": evidence.mic_serial,
                "tpm_quote": evidence.tpm_quote,
                "hardware_attestation_key_id": evidence.hardware_attestation_key_id,
                "reference_corpus_matched": evidence.reference_corpus_matched,
            })
            subj_type = "HARDWARE"
            subj_id = evidence.device_id or evidence.prnu_fingerprint or evidence.mic_serial

        elif isinstance(evidence, PhysicalAccessEvidence):
            raw.update({
                "portal_id": evidence.portal_id,
                "badge_token_id": evidence.badge_token_id,
                "access_granted": evidence.access_granted,
                "facility_zone": evidence.facility_zone,
            })
            loc = {"portal_id": evidence.portal_id, "zone": evidence.facility_zone}
            subj_type = "BADGE"
            subj_id = evidence.badge_token_id
            if not evidence.device_id and evidence.portal_id:
                evidence.device_id = evidence.portal_id

        # Determine canonical_type if not explicitly set
        canonical_type = getattr(evidence, "canonical_type", None)
        if not canonical_type:
            evt_upper = (evidence.event_type or "").upper()
            if isinstance(evidence, EndpointEvidence):
                if evidence.file_operation == "EXPORT" or "EXPORT" in evt_upper:
                    canonical_type = CanonicalEventType.EXPORTED
                elif evidence.file_operation == "READ" or "READ" in evt_upper or "VIEW" in evt_upper:
                    canonical_type = CanonicalEventType.RENDERED
                else:
                    canonical_type = CanonicalEventType.COPIED
            elif isinstance(evidence, EmailGatewayEvent):
                canonical_type = CanonicalEventType.EMAILED
            elif isinstance(evidence, USBTransferEvent):
                canonical_type = CanonicalEventType.WRITTEN_TO_USB
            elif isinstance(evidence, PrintEvent):
                canonical_type = CanonicalEventType.PRINTED
            elif isinstance(evidence, BrowserAccessEvent):
                canonical_type = CanonicalEventType.ACCESSED_FROM_BROWSER
            elif isinstance(evidence, PublicUploadEvent):
                canonical_type = CanonicalEventType.PUBLICATION_OBSERVED
            elif isinstance(evidence, CASBEvent):
                if evidence.operation == "SHARE" or "SHARE" in evt_upper:
                    canonical_type = CanonicalEventType.FORWARDED
                elif evidence.operation == "UPLOAD" or "UPLOAD" in evt_upper:
                    canonical_type = CanonicalEventType.UPLOADED
                else:
                    canonical_type = CanonicalEventType.DOWNLOADED
            elif isinstance(evidence, CloudAccessEvent):
                if evidence.action in ("PutObject", "CreateLink") or "UPLOAD" in evt_upper:
                    canonical_type = CanonicalEventType.UPLOADED
                else:
                    canonical_type = CanonicalEventType.DOWNLOADED
            elif isinstance(evidence, NetworkEvidence):
                canonical_type = CanonicalEventType.NETWORK_TRANSMITTED
            elif isinstance(evidence, DLPEvent):
                canonical_type = CanonicalEventType.NETWORK_TRANSMITTED
            elif isinstance(evidence, DeviceForensicEvidence):
                canonical_type = CanonicalEventType.DECRYPTED
            elif isinstance(evidence, PhysicalAccessEvidence):
                canonical_type = CanonicalEventType.RENDERED
            elif "EXPORT" in evt_upper:
                canonical_type = CanonicalEventType.EXPORTED
            elif "PRINT" in evt_upper:
                canonical_type = CanonicalEventType.PRINTED
            elif "USB" in evt_upper:
                canonical_type = CanonicalEventType.WRITTEN_TO_USB
            elif "FORWARD" in evt_upper or "SHARE" in evt_upper:
                canonical_type = CanonicalEventType.FORWARDED
            elif "PUBLISH" in evt_upper or "UPLOAD" in evt_upper or "DROP" in evt_upper:
                canonical_type = CanonicalEventType.PUBLICATION_OBSERVED
            elif "DECRYPT" in evt_upper:
                canonical_type = CanonicalEventType.DECRYPTED
            else:
                canonical_type = CanonicalEventType.COPIED

        # Determine trust level from source integrity if not explicitly set
        trust_level = getattr(evidence, "trust_level", None)
        if not trust_level:
            if evidence.source_integrity == IntegrityLevel.CRYPTOGRAPHICALLY_VERIFIED:
                trust_level = TelemetryTrustLevel.CRYPTOGRAPHICALLY_VERIFIED
            elif evidence.source_integrity == IntegrityLevel.HIGH_SYSTEM:
                trust_level = TelemetryTrustLevel.AUTHENTICATED
            elif evidence.source_integrity == IntegrityLevel.MEDIUM_LOG:
                trust_level = TelemetryTrustLevel.OBSERVED
            elif evidence.source_integrity == IntegrityLevel.LOW_USER_REPORTED:
                trust_level = TelemetryTrustLevel.UNVERIFIED
            elif evidence.source_integrity == IntegrityLevel.UNTRUSTED:
                trust_level = TelemetryTrustLevel.CONFLICTED
            else:
                trust_level = TelemetryTrustLevel.OBSERVED

        dev_att_state = getattr(evidence, "device_attestation_state", DeviceAttestationState.DEVICE_UNKNOWN)
        rec_principal = getattr(evidence, "recipient_principal_id", None)
        compound_id = getattr(evidence, "compound_event_id", None)
        cluster_id = getattr(evidence, "cluster_id", None)

        # Normalize timestamp to UTC if naive
        ts = evidence.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        return cls(
            event_id=evidence.evidence_id,
            timestamp=ts,
            event_type=evidence.event_type,
            canonical_type=canonical_type,
            source_system=evidence.source,
            subject_type=subj_type,
            subject_id=subj_id,
            recipient_principal_id=rec_principal,
            device_id=evidence.device_id,
            device_attestation_state=dev_att_state,
            trust_level=trust_level,
            network_id=evidence.network_id,
            resource_id=evidence.resource_id,
            artifact_hash=evidence.document_hash,
            copy_id=evidence.copy_id,
            session_id=evidence.session_id,
            parent_event_id=evidence.parent_event_id,
            compound_event_id=compound_id,
            cluster_id=cluster_id,
            location_metadata=loc,
            integrity_status=evidence.source_integrity,
            source_reliability=evidence.confidence_score,
            raw_payload=raw,
        )
