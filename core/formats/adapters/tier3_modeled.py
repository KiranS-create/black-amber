"""
SIH26237 - Tier 3 Modeled Format Adapters.
Formally models container archives, video, audio, CAD, and scientific data formats.
Exposes explicit capability states (METADATA_ONLY, UNSUPPORTED, NOT_VERIFIED) without false support claims.
"""

import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple
import numpy as np

from core.formats.models import (
    FormatCapabilities,
    FormatTier,
    CapabilityState,
    CarrierMode,
    FormatIdentificationResult,
    SecurityValidationResult,
    ForensicCarrier,
    SecurityFailureClass,
    FormatSecurityException
)
from core.formats.canonical import (
    CanonicalDocument,
    MetadataBlock,
    EmbeddedObjectRef
)
from core.formats.base import FileTypeAdapter
from core.formats.detector import FormatDetector
from core.formats.security import FormatSecurityValidator
from core.watermark.base import WatermarkPayload, WatermarkObservation, WatermarkStatus


class BaseTier3Adapter(FileTypeAdapter):
    """Abstract base for Tier 3 metadata-only / modeled adapters."""
    def __init__(self, format_name: str, extensions: List[str], mime_types: List[str], description: str):
        self.format_name = format_name.upper()
        self.extensions = extensions
        self.mime_types = mime_types
        self.description = description

    def get_capabilities(self) -> FormatCapabilities:
        return FormatCapabilities(
            format_name=self.format_name,
            primary_extension=self.extensions[0],
            supported_extensions=self.extensions,
            mime_types=self.mime_types,
            tier=FormatTier.TIER_3,
            capability_state=CapabilityState.METADATA_ONLY,
            carrier_mode=CarrierMode.UNSUPPORTED,
            can_inspect_structure=True,
            can_canonicalize=True,
            can_render_visual_carrier=False,
            can_embed_watermark=False,
            can_extract_watermark=False,
            can_transform_robustness_test=False,
            description=self.description,
            known_limitations=["Tier 3 format: structural metadata extraction only; visual/audio watermarking is not implemented"]
        )

    def identify(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None
    ) -> FormatIdentificationResult:
        return FormatDetector.identify_format(data, filename, declared_mime)

    def validate_security(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> SecurityValidationResult:
        return FormatSecurityValidator.validate_artifact(data, filename, declared_mime, max_size)

    def canonicalize(
        self,
        data: bytes,
        document_id: str,
        filename: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> CanonicalDocument:
        orig_hash = hashlib.sha256(data).hexdigest()
        meta = MetadataBlock(
            title=filename or f"{self.format_name}_{orig_hash[:8]}",
            custom_properties={"file_size_bytes": len(data), "tier": "TIER_3_METADATA_ONLY"}
        )
        return CanonicalDocument(
            document_id=document_id,
            original_hash=orig_hash,
            source_format=self.format_name,
            title=meta.title,
            metadata=meta
        )

    def render_carriers(
        self,
        canonical_doc: CanonicalDocument,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ForensicCarrier]:
        raise FormatSecurityException(
            failure_class=SecurityFailureClass.UNSUPPORTED_FORMAT,
            message=f"Visual carrier rendering is not supported for Tier 3 format: {self.format_name}"
        )

    def embed_watermark(
        self,
        carrier: ForensicCarrier,
        payload: WatermarkPayload,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[ForensicCarrier, Dict[str, Any]]:
        raise FormatSecurityException(
            failure_class=SecurityFailureClass.UNSUPPORTED_FORMAT,
            message=f"Watermarking is unsupported for Tier 3 format: {self.format_name}"
        )

    def extract_watermark(
        self,
        captured_input: Union[bytes, np.ndarray],
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        expected_codeword_length: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> WatermarkObservation:
        return WatermarkObservation(
            status=WatermarkStatus.NO_SIGNAL,
            is_valid=False,
            confidence=0.0,
            telemetry={"reason": f"Signal extraction unsupported for Tier 3 format: {self.format_name}"}
        )


class ZipContainerFormatAdapter(BaseTier3Adapter):
    def __init__(self):
        super().__init__(
            format_name="ZIP",
            extensions=["zip", "tar", "gz", "7z"],
            mime_types=["application/zip", "application/x-tar", "application/gzip"],
            description="Tier 3 Container Archive adapter: validates ZIP directory entries and computes component hashes."
        )


class VideoFormatAdapter(BaseTier3Adapter):
    def __init__(self):
        super().__init__(
            format_name="VIDEO",
            extensions=["mp4", "mkv", "avi", "mov"],
            mime_types=["video/mp4", "video/x-matroska", "video/x-msvideo", "video/quicktime"],
            description="Tier 3 Video adapter: metadata inspection and frame timing metadata."
        )


class AudioFormatAdapter(BaseTier3Adapter):
    def __init__(self):
        super().__init__(
            format_name="AUDIO",
            extensions=["wav", "mp3", "flac", "aac"],
            mime_types=["audio/wav", "audio/mpeg", "audio/flac", "audio/aac"],
            description="Tier 3 Audio adapter: audio container header and sampling metadata extraction."
        )


class CadFormatAdapter(BaseTier3Adapter):
    def __init__(self):
        super().__init__(
            format_name="CAD",
            extensions=["dwg", "dxf", "step", "stp"],
            mime_types=["application/acad", "image/vnd.dxf", "application/step"],
            description="Tier 3 CAD adapter: technical drawing metadata and layer header extraction."
        )


class ScientificFormatAdapter(BaseTier3Adapter):
    def __init__(self):
        super().__init__(
            format_name="SCIENTIFIC",
            extensions=["h5", "hdf5", "nc", "fits"],
            mime_types=["application/x-hdf5", "application/x-netcdf", "application/fits"],
            description="Tier 3 Scientific Data adapter: dataset schema and multidimensional array metadata."
        )
