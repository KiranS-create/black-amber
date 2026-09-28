"""
SIH26237 - Multi-Format Forensic Content Architecture Models & Enums.
Defines format capability tiers, capability states, security failure classifications,
canonical representation types, and explicit original artifact vs forensic carrier identity structures.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
import hashlib


class FormatTier(str, Enum):
    """Tier classification for supported document and media formats."""
    TIER_1 = "TIER_1"  # Required: PDF, DOCX, PPTX, XLSX, PNG, JPEG
    TIER_2 = "TIER_2"  # Architecture Ready: TXT, CSV, RTF, ODT, ODS, ODP
    TIER_3 = "TIER_3"  # Explicitly Modeled: ZIP/Container, Video, Audio, CAD, Scientific


class CapabilityState(str, Enum):
    """
    Formal verified capability state of a file format adapter.
    Enforces honest capability reporting; no unverified claims.
    """
    SUPPORTED = "SUPPORTED"              # Fully verified end-to-end (ingest, inspect, render, watermark, extract)
    PARTIAL = "PARTIAL"                  # Verified subset of operations (e.g., render-only or metadata-only)
    RENDER_ONLY = "RENDER_ONLY"          # Visual carrier rendered; original content not directly modulated
    METADATA_ONLY = "METADATA_ONLY"      # Only structural and container metadata extracted; no watermarking
    EXTRACTION_ONLY = "EXTRACTION_ONLY"  # Watermark signal extraction supported; encoding unsupported
    UNSUPPORTED = "UNSUPPORTED"          # Explicitly rejected or not supported
    SIMULATION_ONLY = "SIMULATION_ONLY"  # Simulated behavior for experimental analysis
    NOT_VERIFIED = "NOT_VERIFIED"        # Implemented interface but lacking full physical/digital verification


class CarrierMode(str, Enum):
    """Method by which forensic watermarking is bound to a format."""
    DIRECTLY_IN_ORIGINAL = "DIRECTLY_IN_ORIGINAL"        # Watermark applied into original binary/pixels (e.g. PNG/JPEG)
    IN_RENDERED_CARRIER = "IN_RENDERED_CARRIER"          # Watermark embedded in rendered visual carrier (e.g. DOCX/PPTX/XLSX)
    IN_METADATA = "IN_METADATA"                          # Cryptographic binding in container metadata (weak, explicitly noted)
    IN_DERIVED_FORENSIC_COPY = "IN_DERIVED_FORENSIC_COPY"# Derived protected format (e.g. rasterized PDF page)
    UNSUPPORTED = "UNSUPPORTED"


class SecurityFailureClass(str, Enum):
    """Deterministic security and validation failure classifications."""
    TYPE_MISMATCH = "TYPE_MISMATCH"
    MALFORMED_CONTAINER = "MALFORMED_CONTAINER"
    POLYGLOT_DETECTED = "POLYGLOT_DETECTED"
    DECOMPRESSION_LIMIT = "DECOMPRESSION_LIMIT"
    PARSER_REJECTED = "PARSER_REJECTED"
    MACRO_PRESENT = "MACRO_PRESENT"
    EXTERNAL_REFERENCE_PRESENT = "EXTERNAL_REFERENCE_PRESENT"
    UNSUPPORTED_ENCRYPTION = "UNSUPPORTED_ENCRYPTION"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    PATH_TRAVERSAL_DETECTED = "PATH_TRAVERSAL_DETECTED"
    XML_ENTITY_HAZARD = "XML_ENTITY_HAZARD"
    OVERSIZED_DIMENSIONS = "OVERSIZED_DIMENSIONS"
    EXCESSIVE_COMPONENTS = "EXCESSIVE_COMPONENTS"
    SUSPICIOUS_EMBEDDED_OBJECT = "SUSPICIOUS_EMBEDDED_OBJECT"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"


class IdentityType(str, Enum):
    """Explicit identity layer distinctions."""
    BYTE_IDENTITY = "BYTE_IDENTITY"                      # Exact bitwise SHA-256 of original uploaded bytes
    CONTENT_IDENTITY = "CONTENT_IDENTITY"                # Normalized semantic content digest (text/tables/cells)
    VISUAL_IDENTITY = "VISUAL_IDENTITY"                  # Rendered perceptual canvas digest
    DERIVED_CARRIER_IDENTITY = "DERIVED_CARRIER_IDENTITY"# Watermarked forensic carrier artifact digest


class TransformationResultState(str, Enum):
    """Status of format transformation and recovery evaluation."""
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    NOT_TESTED = "NOT_TESTED"


class FormatSecurityException(Exception):
    """Raised when an artifact fails zero-trust security checks."""
    def __init__(self, failure_class: SecurityFailureClass, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"[{failure_class.value}] {message}")
        self.failure_class = failure_class
        self.message = message
        self.details = details or {}


class SecurityValidationResult(BaseModel):
    """Result of zero-trust security inspection on raw artifact bytes."""
    is_safe: bool
    failure_class: Optional[SecurityFailureClass] = None
    detected_mime: str
    detected_extension: str
    file_size_bytes: int
    uncompressed_size_bytes: int = 0
    compression_ratio: float = 1.0
    container_entry_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    security_details: Dict[str, Any] = Field(default_factory=dict)


class FormatIdentificationResult(BaseModel):
    """Result of format detection and magic-byte cross-validation."""
    detected_format: str           # e.g., "PDF", "DOCX", "PNG"
    mime_type: str                 # e.g., "application/pdf"
    extension: str                 # e.g., "pdf"
    format_tier: FormatTier
    magic_bytes_hex: str
    is_extension_consistent: bool
    is_mime_consistent: bool
    is_polyglot: bool = False
    confidence: float = 1.0


class OriginalArtifactIdentity(BaseModel):
    """
    Immutable identity of the pristine uploaded artifact.
    Must never be overwritten or replaced with rendered output hashes.
    """
    artifact_id: str
    original_hash: str             # SHA-256 hex digest of raw pristine input bytes
    byte_length: int
    detected_format: str           # e.g., "DOCX"
    declared_extension: str        # e.g., "docx"
    validated_mime: str            # e.g., "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    parser_adapter_version: str    # e.g., "AegisTrace-DocxAdapter-1.0"
    structural_summary: Dict[str, Any] = Field(default_factory=dict)
    ingestion_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tenant_id: str = "default_tenant"


class ForensicCarrierIdentity(BaseModel):
    """
    Identity of a rendered forensic carrier derived from an original artifact.
    Preserves carrier rendering metadata and watermark binding context.
    """
    carrier_id: str
    parent_artifact_id: str
    carrier_hash: str              # SHA-256 hex digest of watermarked/rendered output bytes
    carrier_mode: CarrierMode
    rendering_profile: str         # e.g., "CANONICAL_A4_800X1000_BGR"
    width_px: int
    height_px: int
    component_type: str            # "PAGE", "SLIDE", "SHEET", "IMAGE", "FRAME"
    component_index: int           # 0-indexed page/slide/sheet number
    total_components: int
    watermark_config: Dict[str, Any] = Field(default_factory=dict)
    embedding_metadata: Dict[str, Any] = Field(default_factory=dict)
    carrier_generation_version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FormatCapabilities(BaseModel):
    """Explicit capability matrix entry for a file format adapter."""
    format_name: str
    primary_extension: str
    supported_extensions: List[str]
    mime_types: List[str]
    tier: FormatTier
    capability_state: CapabilityState
    carrier_mode: CarrierMode
    can_inspect_structure: bool
    can_canonicalize: bool
    can_render_visual_carrier: bool
    can_embed_watermark: bool
    can_extract_watermark: bool
    can_transform_robustness_test: bool
    description: str
    known_limitations: List[str] = Field(default_factory=list)


class ForensicCarrier(BaseModel):
    """In-memory or serialized representation of a rendered forensic carrier."""
    carrier_id: str
    parent_artifact_id: str
    component_type: str            # "PAGE", "SLIDE", "SHEET", "IMAGE"
    component_index: int
    total_components: int
    width_px: int
    height_px: int
    carrier_mode: CarrierMode
    rendering_profile: str
    # Image data as BGR numpy array or PNG bytes
    image_bytes: Optional[bytes] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RecoveredArtifactIdentity(BaseModel):
    """
    Identity of a recovered/transferred artifact bytes.
    Preserves recipient recovery context and byte hash.
    """
    recovered_id: str
    parent_carrier_id: str
    original_artifact_id: str
    recovered_hash: str            # SHA-256 hex digest of recovered artifact bytes
    byte_length: int
    transfer_channel: str          # "STAGED_DEVICE_CHANNEL", "USB_ADB", "NETWORK_WIFI"
    is_bitwise_identical_to_carrier: bool
    is_bitwise_identical_to_original: bool
    recovery_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GoldenCaseResult(BaseModel):
    """
    Complete record of a canonical Golden Case execution across the 16-step forensic lifecycle.
    """
    case_id: str                   # e.g., "GOLDEN-PDF", "GOLDEN-DOCX"
    format: str                    # "PDF", "DOCX", "PPTX", "XLSX", "PNG", "JPEG"
    original_identity: OriginalArtifactIdentity
    canonical_hash: str
    security_validation: SecurityValidationResult
    recipient_count: int
    recipient_identities: List[str]
    carrier_identity: ForensicCarrierIdentity
    recovered_identity: RecoveredArtifactIdentity
    watermark_extracted: bool
    extracted_recipient_id: Optional[str] = None
    attribution_confidence: float = 1.0
    lineage_merkle_root: str
    custody_root_hash: str
    evidence_package_id: str
    offline_verified: bool
    steps_passed: int
    total_steps: int = 16
    execution_time_ms: float
    verdict: str                   # "VERIFIED_DEVICE_IN_LOOP"


class ExtractionMatrixEntry(BaseModel):
    """Entry in the format x transformation x extraction result matrix."""
    format: str
    transformation: str            # "NONE", "CROP_10", "RECOMPRESS_JPEG_80", "RESCALE_90", "ROTATION_1", "BRIGHTNESS_5"
    verdict: str                   # "PASS", "PARTIAL", "FAIL", "NOT_TESTED", "INSUFFICIENT_EVIDENCE"
    psnr_db: float
    ssim: float
    hamming_distance: int
    bit_accuracy: float


class DeviceFormatCrossMatrixEntry(BaseModel):
    """Entry in the format x device x recipient x transfer x verification cross-matrix."""
    format: str
    device_id: str
    device_model: str
    recipient_id: str
    transfer_channel: str
    verification_status: str
    epistemic_status: str


class MultiRecipientEquivalenceResult(BaseModel):
    """Verification result for multi-recipient protection of a single original artifact."""
    format: str
    original_hash: str
    recipient_count: int
    recipient_carrier_hashes: List[str]
    recipient_signals_distinct: bool
    min_hamming_distance: int
    avg_hamming_distance: float
    cross_attribution_prevented: bool


class TamperRejectionResult(BaseModel):
    """Result of adversarial evidence tampering tests."""
    format: str
    tamper_category: str           # "MODIFIED_PACKAGE", "MODIFIED_MANIFEST", "MODIFIED_SIG", "MODIFIED_MERKLE", "MODIFIED_RECIPIENT", "MODIFIED_CARRIER", "MODIFIED_ORIGINAL"
    target_object: str
    rejected: bool
    rejection_reason: str
    exception_class: str

