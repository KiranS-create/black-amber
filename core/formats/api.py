"""
SIH26237 - Format-Agnostic Forensic Content API.
Provides the primary unified interface for artifact ingestion, format identification,
security validation, canonicalization, visual carrier rendering, and watermark embedding/extraction.
"""

import hashlib
import os
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timezone
import numpy as np

from core.formats.models import (
    OriginalArtifactIdentity,
    ForensicCarrierIdentity,
    FormatIdentificationResult,
    SecurityValidationResult,
    FormatCapabilities,
    ForensicCarrier,
    CarrierMode,
    FormatTier
)
from core.formats.canonical import CanonicalDocument
from core.formats.registry import default_adapter_registry, FormatAdapterRegistry
from core.formats.detector import FormatDetector
from core.formats.security import FormatSecurityValidator
from core.watermark.base import WatermarkPayload, WatermarkObservation


class ForensicFormatAPI:
    """
    Unified format-agnostic forensic API for AegisTrace.
    """

    def __init__(self, registry: Optional[FormatAdapterRegistry] = None):
        self.registry = registry or default_adapter_registry

    def identify_format(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None
    ) -> FormatIdentificationResult:
        """Identifies file signature and checks extension/MIME consistency."""
        return FormatDetector.identify_format(data, filename, declared_mime)

    def validate_artifact(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> SecurityValidationResult:
        """Executes zero-trust security validation, failing closed on any hazard."""
        return FormatSecurityValidator.validate_artifact(data, filename, declared_mime, max_size)

    def ingest_artifact(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None,
        tenant_id: str = "default_tenant",
        document_id: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> Tuple[OriginalArtifactIdentity, CanonicalDocument, SecurityValidationResult]:
        """
        Full ingestion pipeline:
        1. Validates size, signatures, container integrity, and active content hazards.
        2. Obtains format adapter from registry.
        3. Computes immutable OriginalArtifactIdentity (SHA-256 of raw pristine bytes).
        4. Canonicalizes content into a format-agnostic CanonicalDocument.
        """
        # 1. Zero-trust security validation
        sec_result = self.validate_artifact(data, filename, declared_mime, max_size)

        # 2. Adapter lookup
        adapter, id_result = self.registry.detect_and_get_adapter(data, filename, declared_mime)

        # 3. Compute original artifact identity
        orig_hash = hashlib.sha256(data).hexdigest()
        doc_id = document_id or f"doc_{orig_hash[:12]}"
        _, ext = os.path.splitext(filename or f"doc.{id_result.extension}")
        declared_ext = ext.lstrip(".").lower() or id_result.extension

        caps = adapter.get_capabilities()
        artifact_identity = OriginalArtifactIdentity(
            artifact_id=doc_id,
            original_hash=orig_hash,
            byte_length=len(data),
            detected_format=id_result.detected_format,
            declared_extension=declared_ext,
            validated_mime=id_result.mime_type,
            parser_adapter_version=f"AegisTrace-{caps.format_name}Adapter-1.0",
            structural_summary=sec_result.security_details,
            ingestion_timestamp=datetime.now(timezone.utc).isoformat(),
            tenant_id=tenant_id
        )

        # 4. Canonicalize
        canonical_doc = adapter.canonicalize(data, doc_id, filename)

        return artifact_identity, canonical_doc, sec_result

    def render_forensic_carriers(
        self,
        canonical_doc: CanonicalDocument,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ForensicCarrier]:
        """Renders canonical document into one or more forensic visual carriers."""
        adapter = self.registry.get_adapter(canonical_doc.source_format)
        if not adapter:
            raise ValueError(f"No adapter registered for format: {canonical_doc.source_format}")
        return adapter.render_carriers(canonical_doc, options)

    def watermark_carrier(
        self,
        carrier: ForensicCarrier,
        payload: WatermarkPayload,
        format_hint: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[ForensicCarrier, Dict[str, Any]]:
        """Modulates watermark payload into the forensic carrier."""
        # Find matching adapter
        fmt = format_hint or "PDF"
        adapter = self.registry.get_adapter(fmt) or self.registry.get_adapter("PDF")
        return adapter.embed_watermark(carrier, payload, options)

    def extract_watermark(
        self,
        captured_input: Union[bytes, np.ndarray],
        format_hint: Optional[str] = None,
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        expected_codeword_length: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> WatermarkObservation:
        """Extracts and verifies watermark signal from captured image or leaked artifact."""
        fmt = format_hint or "PDF"
        adapter = self.registry.get_adapter(fmt) or self.registry.get_adapter("PDF")
        return adapter.extract_watermark(
            captured_input=captured_input,
            expected_document_id=expected_document_id,
            expected_release_id=expected_release_id,
            expected_codeword_length=expected_codeword_length,
            options=options
        )

    def query_format_guarantees(self, format_or_ext: str) -> FormatCapabilities:
        """Queries the formal forensic guarantees for a specific format or extension."""
        return self.registry.query_guarantees(format_or_ext)

    def get_capability_matrix(self) -> Dict[str, FormatCapabilities]:
        """Returns the full capability matrix across all registered formats."""
        return self.registry.get_all_capabilities()


# Singleton instance
default_format_api = ForensicFormatAPI()
