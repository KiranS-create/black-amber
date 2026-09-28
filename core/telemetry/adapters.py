"""
AegisTrace Telemetry Adapters & Device Forensics Provider.

Provides deterministic parsing and transformation adapters for heterogeneous
enterprise and external telemetry feeds (EDR, DLP, IdP, Network, Cloud, USB,
Print, Public Uploads, and Physical Device Forensics).

CRITICAL FORENSIC INVARIANT:
For Physical Device Forensics (PRNU camera sensor noise, MIC printer tracking dots):
A match is ONLY asserted if the observed sensor signature or serial matches an
enrolled reference corpus. If no reference match exists, the provider MUST set
reference_corpus_matched = False and state NO_REFERENCE. It must NEVER invent or
hallucinate a device match.
"""

from datetime import datetime, timezone
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

from core.telemetry.models import (
    TelemetrySource,
    IntegrityLevel,
    CollectionMethod,
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
from core.telemetry.event import ForensicEvent


class EDRAdapter:
    """Adapter for Endpoint Detection & Response (e.g. CrowdStrike, Defender for Endpoint)."""

    @staticmethod
    def parse_event(raw: Dict[str, Any]) -> ForensicEvent:
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        evidence = EndpointEvidence(
            evidence_id=raw.get("event_id", f"edr-{hashlib.sha256(str(raw).encode()).hexdigest()[:12]}"),
            source=TelemetrySource.EDR,
            event_type=raw.get("event_type", "FILE_READ"),
            timestamp=ts,
            actor_account_id=raw.get("user_account") or raw.get("username"),
            device_id=raw.get("hostname") or raw.get("computer_name") or raw.get("device_id"),
            resource_id=raw.get("target_file_path") or raw.get("file_path"),
            document_hash=raw.get("sha256") or raw.get("file_hash"),
            copy_id=raw.get("copy_id"),
            session_id=raw.get("logon_id") or raw.get("session_id"),
            process_name=raw.get("process_name"),
            process_pid=raw.get("process_pid"),
            process_path=raw.get("process_path"),
            parent_process_name=raw.get("parent_process_name"),
            file_operation=raw.get("operation", "READ"),
            source_integrity=IntegrityLevel.HIGH_SYSTEM,
            collection_method=CollectionMethod.AGENT_KERNEL,
            confidence_score=float(raw.get("confidence", 0.95)),
            raw_metadata=raw,
        )
        return ForensicEvent.from_evidence(evidence)


class DLPAdapter:
    """Adapter for Data Loss Prevention systems (e.g. Symantec DLP, Forcepoint, Microsoft Purview)."""

    @staticmethod
    def parse_event(raw: Dict[str, Any]) -> ForensicEvent:
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        evidence = DLPEvent(
            evidence_id=raw.get("incident_id", f"dlp-{hashlib.sha256(str(raw).encode()).hexdigest()[:12]}"),
            source=TelemetrySource.DLP,
            event_type=raw.get("event_type", "DLP_POLICY_VIOLATION"),
            timestamp=ts,
            actor_account_id=raw.get("sender") or raw.get("actor_account_id"),
            device_id=raw.get("endpoint_id") or raw.get("device_id"),
            resource_id=raw.get("file_name") or raw.get("resource_id"),
            document_hash=raw.get("file_sha256") or raw.get("document_hash"),
            copy_id=raw.get("copy_id"),
            policy_name=raw.get("policy_name", "CONFIDENTIAL_DATA_EGRESS"),
            policy_action=raw.get("action", "ALERT"),
            destination_type=raw.get("destination_type", "EXTERNAL_STORAGE"),
            severity=raw.get("severity", "HIGH"),
            source_integrity=IntegrityLevel.HIGH_SYSTEM,
            collection_method=CollectionMethod.AGENT_KERNEL,
            confidence_score=float(raw.get("confidence", 0.92)),
            raw_metadata=raw,
        )
        return ForensicEvent.from_evidence(evidence)


class IdPAdapter:
    """Adapter for Identity Providers (e.g. Okta, Entra ID, PingFederate)."""

    @staticmethod
    def parse_event(raw: Dict[str, Any]) -> ForensicEvent:
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        evidence = IdentityProviderEvidence(
            evidence_id=raw.get("event_id", f"idp-{hashlib.sha256(str(raw).encode()).hexdigest()[:12]}"),
            source=TelemetrySource.IDP,
            event_type=raw.get("event_type", "USER_AUTH_SUCCESS"),
            timestamp=ts,
            actor_account_id=raw.get("user_id") or raw.get("user_principal_name"),
            device_id=raw.get("device_id"),
            session_id=raw.get("session_id"),
            auth_method=raw.get("auth_method", "PASSWORD_MFA"),
            mfa_verified=bool(raw.get("mfa_verified", False)),
            tenant_id=raw.get("tenant_id"),
            auth_client_ip=raw.get("client_ip") or raw.get("ip_address"),
            user_agent=raw.get("user_agent"),
            source_integrity=IntegrityLevel.HIGH_SYSTEM,
            collection_method=CollectionMethod.API_AUDIT,
            confidence_score=float(raw.get("confidence", 0.98)),
            raw_metadata=raw,
        )
        return ForensicEvent.from_evidence(evidence)


class NetworkAdapter:
    """Adapter for Firewalls, Zeek/Bro, NetFlow, and Egress Gateways."""

    @staticmethod
    def parse_event(raw: Dict[str, Any]) -> ForensicEvent:
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        evidence = NetworkEvidence(
            evidence_id=raw.get("flow_id", f"net-{hashlib.sha256(str(raw).encode()).hexdigest()[:12]}"),
            source=TelemetrySource.NETWORK,
            event_type=raw.get("event_type", "NETWORK_EGRESS_FLOW"),
            timestamp=ts,
            actor_account_id=raw.get("associated_user"),
            device_id=raw.get("source_mac") or raw.get("device_id"),
            network_id=raw.get("source_ip"),
            source_ip=raw.get("source_ip", "0.0.0.0"),
            source_port=raw.get("source_port"),
            destination_ip=raw.get("destination_ip", "0.0.0.0"),
            destination_port=raw.get("destination_port"),
            protocol=raw.get("protocol", "TCP"),
            bytes_transferred=raw.get("bytes_transferred"),
            is_vpn_or_proxy=bool(raw.get("is_vpn_or_proxy", False)),
            is_tor_exit=bool(raw.get("is_tor_exit", False)),
            source_integrity=IntegrityLevel.MEDIUM_LOG,
            collection_method=CollectionMethod.NETWORK_TAP,
            confidence_score=float(raw.get("confidence", 0.85)),
            raw_metadata=raw,
        )
        return ForensicEvent.from_evidence(evidence)


class USBAdapter:
    """Adapter for USB / Mass-storage mount and write telemetry."""

    @staticmethod
    def parse_event(raw: Dict[str, Any]) -> ForensicEvent:
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        evidence = USBTransferEvent(
            evidence_id=raw.get("event_id", f"usb-{hashlib.sha256(str(raw).encode()).hexdigest()[:12]}"),
            source=TelemetrySource.USB,
            event_type=raw.get("event_type", "USB_FILE_WRITE"),
            timestamp=ts,
            actor_account_id=raw.get("username") or raw.get("actor_account_id"),
            device_id=raw.get("host_device_id") or raw.get("device_id"),
            resource_id=raw.get("destination_path") or raw.get("file_path"),
            document_hash=raw.get("file_sha256") or raw.get("document_hash"),
            copy_id=raw.get("copy_id"),
            vendor_id=raw.get("vendor_id"),
            product_id=raw.get("product_id"),
            volume_serial=raw.get("volume_serial"),
            volume_label=raw.get("volume_label"),
            drive_letter_or_mount=raw.get("mount_point") or raw.get("drive_letter"),
            bytes_written=raw.get("bytes_written"),
            source_integrity=IntegrityLevel.HIGH_SYSTEM,
            collection_method=CollectionMethod.AGENT_KERNEL,
            confidence_score=float(raw.get("confidence", 0.90)),
            raw_metadata=raw,
        )
        return ForensicEvent.from_evidence(evidence)


class PrintAdapter:
    """Adapter for Print Spoolers and Machine Identification Code (MIC) detection."""

    @staticmethod
    def parse_event(raw: Dict[str, Any]) -> ForensicEvent:
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        evidence = PrintEvent(
            evidence_id=raw.get("job_id", f"print-{hashlib.sha256(str(raw).encode()).hexdigest()[:12]}"),
            source=TelemetrySource.PRINT,
            event_type=raw.get("event_type", "PRINT_JOB_COMPLETED"),
            timestamp=ts,
            actor_account_id=raw.get("username") or raw.get("actor_account_id"),
            device_id=raw.get("workstation_id") or raw.get("device_id"),
            resource_id=raw.get("document_title") or raw.get("resource_id"),
            document_hash=raw.get("document_sha256") or raw.get("document_hash"),
            copy_id=raw.get("copy_id"),
            printer_name=raw.get("printer_name", "UNKNOWN_PRINTER"),
            printer_ip=raw.get("printer_ip"),
            pages_printed=int(raw.get("pages_printed", 1)),
            has_mic_yellow_dots=bool(raw.get("has_mic_yellow_dots", False)),
            mic_decoded_serial=raw.get("mic_decoded_serial"),
            source_integrity=IntegrityLevel.MEDIUM_LOG,
            collection_method=CollectionMethod.API_AUDIT,
            confidence_score=float(raw.get("confidence", 0.88)),
            raw_metadata=raw,
        )
        return ForensicEvent.from_evidence(evidence)


class PublicUploadAdapter:
    """Adapter for Public Drops, GitHub, Pastebin, and anonymous file hosting."""

    @staticmethod
    def parse_event(raw: Dict[str, Any]) -> ForensicEvent:
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        evidence = PublicUploadEvent(
            evidence_id=raw.get("upload_id", f"pub-{hashlib.sha256(str(raw).encode()).hexdigest()[:12]}"),
            source=TelemetrySource.PUBLIC_UPLOAD,
            event_type=raw.get("event_type", "PUBLIC_FILE_EXPOSURE"),
            timestamp=ts,
            actor_account_id=raw.get("uploader_handle") or raw.get("actor_account_id"),
            device_id=None,
            network_id=raw.get("uploader_ip"),
            resource_id=raw.get("public_url") or raw.get("target_url"),
            document_hash=raw.get("file_sha256") or raw.get("document_hash"),
            copy_id=raw.get("copy_id"),
            platform_name=raw.get("platform_name", "PASTEBIN"),
            public_url=raw.get("public_url"),
            uploader_account=raw.get("uploader_handle"),
            tls_fingerprint=raw.get("tls_fingerprint"),
            source_integrity=IntegrityLevel.LOW_USER_REPORTED if raw.get("user_reported") else IntegrityLevel.MEDIUM_LOG,
            collection_method=CollectionMethod.WEB_SCRAPER,
            confidence_score=float(raw.get("confidence", 0.75)),
            raw_metadata=raw,
        )
        return ForensicEvent.from_evidence(evidence)


class DeviceForensicsProvider:
    """
    Physical device forensic extraction provider.
    Verifies Photo Response Non-Uniformity (PRNU) camera sensor fingerprints
    and Machine Identification Code (MIC) printer serials against an enrolled reference corpus.

    CRITICAL RULE:
    If PRNU or MIC does not match an enrolled reference entry:
    reference_corpus_matched MUST be False, and result status must be NO_REFERENCE.
    Never assume or invent device identity!
    """

    def __init__(
        self,
        enrolled_prnu_sensors: Optional[Dict[str, str]] = None,
        enrolled_mic_printers: Optional[Dict[str, str]] = None,
    ):
        # enrolled_prnu_sensors: prnu_hash -> camera_device_id
        self._enrolled_prnu = enrolled_prnu_sensors or {}
        # enrolled_mic_printers: mic_serial -> printer_id
        self._enrolled_mic = enrolled_mic_printers or {}

    def enroll_camera_sensor(self, prnu_hash: str, camera_device_id: str) -> None:
        self._enrolled_prnu[prnu_hash] = camera_device_id

    def enroll_printer(self, mic_serial: str, printer_id: str) -> None:
        self._enrolled_mic[mic_serial] = printer_id

    def analyze_sensor_prnu(
        self,
        observed_prnu_hash: str,
        observed_timestamp: datetime,
        artifact_hash: Optional[str] = None,
        sensor_model: Optional[str] = None,
    ) -> Tuple[ForensicEvent, str]:
        """
        Analyze PRNU fingerprint. Returns (ForensicEvent, match_status).
        match_status: "MATCHED" or "NO_REFERENCE".
        """
        matched_device = self._enrolled_prnu.get(observed_prnu_hash)
        has_match = matched_device is not None
        match_status = "MATCHED" if has_match else "NO_REFERENCE"

        evidence = DeviceForensicEvidence(
            evidence_id=f"prnu-{observed_prnu_hash[:12]}",
            source=TelemetrySource.DEVICE_FORENSICS,
            event_type="PRNU_SENSOR_ANALYSIS",
            timestamp=observed_timestamp,
            device_id=matched_device if has_match else None,
            document_hash=artifact_hash,
            sensor_model=sensor_model,
            prnu_fingerprint=observed_prnu_hash,
            reference_corpus_matched=has_match,
            source_integrity=IntegrityLevel.CRYPTOGRAPHICALLY_VERIFIED if has_match else IntegrityLevel.MEDIUM_LOG,
            collection_method=CollectionMethod.FORENSIC_IMAGE_DUMP,
            confidence_score=0.98 if has_match else 0.3,
            raw_metadata={
                "observed_prnu": observed_prnu_hash,
                "reference_status": match_status,
                "matched_device": matched_device,
            },
        )
        return ForensicEvent.from_evidence(evidence), match_status

    def analyze_printer_mic(
        self,
        observed_mic_serial: str,
        observed_timestamp: datetime,
        artifact_hash: Optional[str] = None,
    ) -> Tuple[ForensicEvent, str]:
        """
        Analyze Printer Yellow Dot MIC serial. Returns (ForensicEvent, match_status).
        match_status: "MATCHED" or "NO_REFERENCE".
        """
        matched_printer = self._enrolled_mic.get(observed_mic_serial)
        has_match = matched_printer is not None
        match_status = "MATCHED" if has_match else "NO_REFERENCE"

        evidence = DeviceForensicEvidence(
            evidence_id=f"mic-{observed_mic_serial}",
            source=TelemetrySource.DEVICE_FORENSICS,
            event_type="MIC_PRINTER_ANALYSIS",
            timestamp=observed_timestamp,
            device_id=matched_printer if has_match else None,
            document_hash=artifact_hash,
            mic_serial=observed_mic_serial,
            reference_corpus_matched=has_match,
            source_integrity=IntegrityLevel.CRYPTOGRAPHICALLY_VERIFIED if has_match else IntegrityLevel.MEDIUM_LOG,
            collection_method=CollectionMethod.FORENSIC_IMAGE_DUMP,
            confidence_score=0.95 if has_match else 0.3,
            raw_metadata={
                "observed_mic_serial": observed_mic_serial,
                "reference_status": match_status,
                "matched_printer": matched_printer,
            },
        )
        return ForensicEvent.from_evidence(evidence), match_status


class TelemetryNormalizationLayer:
    """
    Deterministic multi-sensor normalization layer.
    Auto-detects heterogeneous external log sources (EDR, DLP, Netflow, Sysmon, USB, Print)
    and transforms them into canonical ForensicEvent instances.
    """

    @classmethod
    def normalize_raw_event(cls, raw: Dict[str, Any]) -> ForensicEvent:
        """
        Inspects fields and routes to the appropriate adapter.
        """
        source = (raw.get("source") or raw.get("vendor") or raw.get("sensor") or "").upper()
        event_type = (raw.get("event_type") or raw.get("type") or raw.get("action") or "").upper()

        if source in ("EDR", "CROWDSTRIKE", "DEFENDER", "SENTINELONE") or "PROCESS" in event_type or "FILE_" in event_type:
            return EDRAdapter.parse_event(raw)

        if source in ("DLP", "PURVIEW", "FORCEPOINT", "SYMANTEC") or "POLICY" in event_type or "VIOLATION" in event_type:
            return DLPAdapter.parse_event(raw)

        if source in ("IDP", "OKTA", "ENTRA", "AZURE_AD", "PING") or "AUTH" in event_type or "LOGON" in event_type:
            return IdPAdapter.parse_event(raw)

        if source in ("USB", "REMOVABLE") or "USB" in event_type or "volume_serial" in raw:
            return USBAdapter.parse_event(raw)

        if source in ("PRINT", "SPOOLER") or "PRINT" in event_type or "printer_name" in raw:
            return PrintAdapter.parse_event(raw)

        if source in ("NETWORK", "ZEEK", "FIREWALL", "NETFLOW") or ("source_ip" in raw and "destination_ip" in raw):
            return NetworkAdapter.parse_event(raw)

        if source in ("PUBLIC", "DROP", "PASTEBIN", "GITHUB") or "public_url" in raw or "PUBLIC" in event_type:
            return PublicUploadAdapter.parse_event(raw)

        # Fallback to EDR generic parser
        return EDRAdapter.parse_event(raw)
