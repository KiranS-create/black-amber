"""
AegisTrace External Telemetry Evidence Models.

Defines strongly-typed external operational evidence collected from enterprise
and external environments (EDR, DLP, CASB, Identity Providers, USB, Print, Email,
Public Drops, and Device Physical Forensics).

CRITICAL FORENSIC INVARIANT:
Never conflate Account, Device, Network Source, Forwarding Event,
Downstream Holder, and Human Operator.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TelemetrySource(str, Enum):
    EDR = "EDR"
    IDP = "IDP"
    NETWORK = "NETWORK"
    DLP = "DLP"
    CASB = "CASB"
    EMAIL_GATEWAY = "EMAIL_GATEWAY"
    CLOUD_STORAGE = "CLOUD_STORAGE"
    USB = "USB"
    PRINT = "PRINT"
    PRINT_SPOOLER = "PRINT_SPOOLER"
    BROWSER = "BROWSER"
    PUBLIC_UPLOAD = "PUBLIC_UPLOAD"
    DEVICE_FORENSICS = "DEVICE_FORENSICS"
    PHYSICAL_ACCESS = "PHYSICAL_ACCESS"
    USER_REPORT = "USER_REPORT"


class IntegrityLevel(str, Enum):
    CRYPTOGRAPHICALLY_VERIFIED = "CRYPTOGRAPHICALLY_VERIFIED"  # Hardware/signature bound
    HIGH_SYSTEM = "HIGH_SYSTEM"                                # Kernel/EDR authenticated log
    MEDIUM_LOG = "MEDIUM_LOG"                                  # Standard sys/application log
    LOW_USER_REPORTED = "LOW_USER_REPORTED"                    # Unverified submission
    UNTRUSTED = "UNTRUSTED"                                    # Failed or absent integrity check


class TelemetryTrustLevel(str, Enum):
    """
    Forensic trust classifications for external observations.
    Strictly distinguishes cryptographically sealed logs from raw unverified logs.
    """
    CRYPTOGRAPHICALLY_VERIFIED = "CRYPTOGRAPHICALLY_VERIFIED"
    HARDWARE_SEALED = "HARDWARE_SEALED"
    SIGNED = "SIGNED"
    AUTHENTICATED = "AUTHENTICATED"
    OBSERVED = "OBSERVED"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTED = "CONFLICTED"


class DeviceAttestationState(str, Enum):
    """
    Attestation and enrollment standing of an observed device.
    Never assumes a device is attested without explicit cryptographic proof.
    """
    DEVICE_OBSERVED = "DEVICE_OBSERVED"
    DEVICE_IDENTIFIED = "DEVICE_IDENTIFIED"
    DEVICE_ATTESTED = "DEVICE_ATTESTED"
    DEVICE_UNATTESTED = "DEVICE_UNATTESTED"
    DEVICE_REVOKED = "DEVICE_REVOKED"
    DEVICE_UNKNOWN = "DEVICE_UNKNOWN"


class CanonicalEventType(str, Enum):
    """
    Standardized, strongly-typed lifecycle custody event types across AegisTrace.
    Normalizes heterogeneous source telemetry into a unified sequence.
    """
    DOCUMENT_CREATED = "DOCUMENT_CREATED"
    RELEASED_TO_RECIPIENT = "RELEASED_TO_RECIPIENT"
    DECRYPTED = "DECRYPTED"
    RENDERED = "RENDERED"
    EXPORTED = "EXPORTED"
    COPIED = "COPIED"
    FORWARDED = "FORWARDED"
    WRITTEN_TO_USB = "WRITTEN_TO_USB"
    EMAILED = "EMAILED"
    UPLOADED = "UPLOADED"
    DOWNLOADED = "DOWNLOADED"
    PRINTED = "PRINTED"
    ACCESSED_FROM_BROWSER = "ACCESSED_FROM_BROWSER"
    NETWORK_TRANSMITTED = "NETWORK_TRANSMITTED"
    PUBLICATION_OBSERVED = "PUBLICATION_OBSERVED"


class CollectionMethod(str, Enum):
    AGENT_KERNEL = "AGENT_KERNEL"
    API_AUDIT = "API_AUDIT"
    NETWORK_TAP = "NETWORK_TAP"
    PASSIVE_SENSOR = "PASSIVE_SENSOR"
    EXPORT_SIGNED_BUNDLE = "EXPORT_SIGNED_BUNDLE"
    FORENSIC_IMAGE_DUMP = "FORENSIC_IMAGE_DUMP"
    WEB_SCRAPER = "WEB_SCRAPER"
    MANUAL_INGESTION = "MANUAL_INGESTION"


class BaseTelemetryEvidence(BaseModel):
    """
    Base external telemetry record.
    Preserves original source provenance, integrity level, and collection metadata.
    """
    evidence_id: str
    source: TelemetrySource
    event_type: str = "GENERIC_EVENT"
    canonical_type: Optional[CanonicalEventType] = None
    timestamp: datetime
    actor_account_id: Optional[str] = None  # Pseudonymous or enterprise account ID (NOT human name)
    recipient_principal_id: Optional[str] = None  # Resolved cryptographic recipient principal ID if mapped
    device_id: Optional[str] = None         # Hardware or asset serial / enrolled UUID
    device_attestation_state: DeviceAttestationState = DeviceAttestationState.DEVICE_UNKNOWN
    trust_level: TelemetryTrustLevel = TelemetryTrustLevel.OBSERVED
    network_id: Optional[str] = None        # Egress IP, CIDR, AS number, or MAC
    resource_id: Optional[str] = None       # File path, URI, or storage object key
    document_hash: Optional[str] = None     # SHA-256 of document/artifact if matched
    copy_id: Optional[str] = None           # Cryptographic watermark / recipient copy tag
    session_id: Optional[str] = None        # Logged interactive or API session ID
    parent_event_id: Optional[str] = None   # Causal predecessor event ID
    compound_event_id: Optional[str] = None # ID of deduplicated multi-sensor compound action
    cluster_id: Optional[str] = None        # Clustering identifier for concurrent sensor observations
    source_integrity: IntegrityLevel = IntegrityLevel.MEDIUM_LOG
    collection_method: CollectionMethod = CollectionMethod.API_AUDIT
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    retention_expiry: Optional[datetime] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)  # Preserved unmutated original fields


class EndpointEvidence(BaseTelemetryEvidence):
    """EDR / OS Endpoint file access, process execution, export events."""
    source: TelemetrySource = TelemetrySource.EDR
    process_name: Optional[str] = None
    process_pid: Optional[int] = None
    process_path: Optional[str] = None
    parent_process_name: Optional[str] = None
    file_operation: str = "READ"  # READ, WRITE, RENAME, DELETE, EXPORT


class IdentityProviderEvidence(BaseTelemetryEvidence):
    """IdP authentication, SSO tokens, MFA verification, privilege elevation."""
    source: TelemetrySource = TelemetrySource.IDP
    auth_method: str = "PASSWORD_MFA"  # FIDO2_WEBAUTHN, PASSWORD_MFA, OAUTH_TOKEN, CERTIFICATE
    mfa_verified: bool = False
    tenant_id: Optional[str] = None
    auth_client_ip: Optional[str] = None
    user_agent: Optional[str] = None


class NetworkEvidence(BaseTelemetryEvidence):
    """Firewall, Proxy, NetFlow, VPN, and egress gateway telemetry."""
    source: TelemetrySource = TelemetrySource.NETWORK
    source_ip: str
    source_port: Optional[int] = None
    destination_ip: str
    destination_port: Optional[int] = None
    protocol: str = "TCP"  # TCP, UDP, TLS, HTTP, HTTPS
    bytes_transferred: Optional[int] = None
    is_vpn_or_proxy: bool = False
    is_tor_exit: bool = False


class DLPEvent(BaseTelemetryEvidence):
    """Data Loss Prevention policy violation, egress blocking, file transfer detection."""
    source: TelemetrySource = TelemetrySource.DLP
    policy_name: str
    policy_action: str = "ALERT"  # ALERT, BLOCK, QUARANTINE, ENCRYPT
    destination_type: str = "EXTERNAL_STORAGE"  # EXTERNAL_STORAGE, EMAIL, WEB_UPLOAD, PRINTER
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL


class CASBEvent(BaseTelemetryEvidence):
    """Cloud Access Security Broker cloud service usage, upload, sharing event."""
    source: TelemetrySource = TelemetrySource.CASB
    cloud_service: str  # GoogleDrive, OneDrive, Dropbox, Box, AWS_S3
    sharing_scope: str = "PRIVATE"  # PRIVATE, INTERNAL, ANYONE_WITH_LINK, PUBLIC
    operation: str = "UPLOAD"  # UPLOAD, DOWNLOAD, SHARE, SYNC


class EmailGatewayEvent(BaseTelemetryEvidence):
    """Outbound email gateway message, attachment, recipient domain telemetry."""
    source: TelemetrySource = TelemetrySource.EMAIL_GATEWAY
    sender_address: str
    recipient_addresses: List[str]
    subject_hash: Optional[str] = None  # Salted hash of email subject for privacy
    attachment_filename: Optional[str] = None
    attachment_hash: Optional[str] = None
    message_id: Optional[str] = None


class CloudAccessEvent(BaseTelemetryEvidence):
    """Direct cloud API / Object storage audit log (S3 CloudTrail, Cloud Storage)."""
    source: TelemetrySource = TelemetrySource.CLOUD_STORAGE
    bucket_or_vault: str
    action: str = "GetObject"  # GetObject, PutObject, CreateLink
    caller_arn_or_sa: Optional[str] = None


class USBTransferEvent(BaseTelemetryEvidence):
    """Removable storage device mount, volume write, external mass-storage export."""
    source: TelemetrySource = TelemetrySource.USB
    vendor_id: Optional[str] = None
    product_id: Optional[str] = None
    volume_serial: Optional[str] = None
    volume_label: Optional[str] = None
    drive_letter_or_mount: Optional[str] = None
    bytes_written: Optional[int] = None


class PrintEvent(BaseTelemetryEvidence):
    """Spooler, network printer, or physical document printing event."""
    source: TelemetrySource = TelemetrySource.PRINT
    printer_name: str
    printer_ip: Optional[str] = None
    pages_printed: int = 1
    has_mic_yellow_dots: bool = False  # Machine Identification Code (MIC tracking dots)
    mic_decoded_serial: Optional[str] = None


class BrowserAccessEvent(BaseTelemetryEvidence):
    """Managed browser file download, form upload, extension telemetry."""
    source: TelemetrySource = TelemetrySource.BROWSER
    browser_name: str = "Chrome"
    tab_url_domain: str
    is_incognito: bool = False
    download_path: Optional[str] = None


class PublicUploadEvent(BaseTelemetryEvidence):
    """Public code hosting (GitHub, GitLab), pastebin, anonymous drop, file sharing."""
    source: TelemetrySource = TelemetrySource.PUBLIC_UPLOAD
    platform_name: str  # GitHub, Pastebin, AnonFiles, Telegram, Mega, Discord
    public_url: Optional[str] = None
    uploader_account: Optional[str] = None
    tls_fingerprint: Optional[str] = None


class DeviceForensicEvidence(BaseTelemetryEvidence):
    """Physical hardware forensic extraction, camera PRNU, TPM attestation."""
    source: TelemetrySource = TelemetrySource.DEVICE_FORENSICS
    sensor_model: Optional[str] = None
    prnu_fingerprint: Optional[str] = None         # Camera Photo Response Non-Uniformity hash
    mic_serial: Optional[str] = None               # Printer serial from yellow tracking dots
    tpm_quote: Optional[str] = None                # Hardware root-of-trust TPM quote
    hardware_attestation_key_id: Optional[str] = None
    reference_corpus_matched: bool = False         # Explicit flag: True ONLY if matched against known reference


class PhysicalAccessEvidence(BaseTelemetryEvidence):
    """Facility badge swipe, access control turnstile, biometric kiosk."""
    source: TelemetrySource = TelemetrySource.PHYSICAL_ACCESS
    portal_id: str
    badge_token_id: str
    access_granted: bool = True
    facility_zone: str
