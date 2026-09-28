"""
SIH26237 - Multi-Format FileTypeAdapter Abstract Base Contract.
Defines the unified abstract interface implemented by all format-specific adapters
(PDF, DOCX, PPTX, XLSX, PNG, JPEG, TXT, CSV, RTF, ODF, and Tier 3 containers).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
import numpy as np

from core.formats.models import (
    FormatCapabilities,
    FormatIdentificationResult,
    SecurityValidationResult,
    ForensicCarrier,
    OriginalArtifactIdentity,
    ForensicCarrierIdentity,
    CarrierMode
)
from core.formats.canonical import CanonicalDocument
from core.watermark.base import WatermarkPayload, WatermarkObservation


class FileTypeAdapter(ABC):
    """
    Unified abstract base contract for all AegisTrace format adapters.
    Guarantees strict separation of original artifact identity from rendered forensic carriers.
    """

    @abstractmethod
    def get_capabilities(self) -> FormatCapabilities:
        """Returns the formal capability descriptor for this format adapter."""
        pass

    @abstractmethod
    def identify(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None
    ) -> FormatIdentificationResult:
        """Identifies file signature and verifies extension/MIME consistency."""
        pass

    @abstractmethod
    def validate_security(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> SecurityValidationResult:
        """Executes zero-trust security checks, failing closed on any hazard."""
        pass

    @abstractmethod
    def canonicalize(
        self,
        data: bytes,
        document_id: str,
        filename: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> CanonicalDocument:
        """
        Parses and transforms raw format binary into a normalized CanonicalDocument.
        Operates completely offline.
        """
        pass

    @abstractmethod
    def render_carriers(
        self,
        canonical_doc: CanonicalDocument,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ForensicCarrier]:
        """
        Renders the canonical document into one or more forensic visual carriers
        (e.g., page, slide, or worksheet canvas images).
        """
        pass

    @abstractmethod
    def embed_watermark(
        self,
        carrier: ForensicCarrier,
        payload: WatermarkPayload,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[ForensicCarrier, Dict[str, Any]]:
        """
        Modulates the forensic watermark payload into the forensic carrier.
        Returns the watermarked carrier and embedding telemetry.
        """
        pass

    @abstractmethod
    def extract_watermark(
        self,
        captured_input: Union[bytes, np.ndarray],
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        expected_codeword_length: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> WatermarkObservation:
        """
        Extracts and verifies forensic watermark signals from a captured/leaked carrier.
        Enforces fail-closed observation semantics.
        """
        pass
