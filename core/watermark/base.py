"""
SIH26237 - Core Watermark Base Interfaces & Data Structures
Defines abstract contracts for watermark encoding, decoding, observation telemetry,
and fail-closed status enumerations.
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class WatermarkStatus(str, Enum):
    """
    Standardized observation status for the physical watermark decoder.
    Enforces fail-closed semantics: corrupted, unwatermarked, or foreign documents
    never guess or produce false accusations.
    """
    RECOVERED = "RECOVERED"      # Geometric sync OK, ECC passed, CRC-32 verified
    PARTIAL = "PARTIAL"          # Geometric sync OK, uncorrectable ECC, soft symbols available
    NO_SIGNAL = "NO_SIGNAL"      # Fiducials missing, image blank, carrier wiped, or non-watermarked
    INVALID = "INVALID"          # CRC error, corrupted framing, or document-binding mismatch


class WatermarkPayload(BaseModel):
    """
    Decoupled payload container carrying abstract fingerprint symbols
    and cryptographic integrity/binding metadata.
    """
    document_id: str
    release_id: str
    codeword: List[int]          # Binary symbols {0, 1}^m from Tardos
    preamble: int = 0xE9B6       # 16-bit Barker-like sync preamble
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WatermarkObservation(BaseModel):
    """
    Decoded observation telemetry returned by the watermark decoder.
    Consumed by the Traceability Adapter and Tardos accusation engine.
    """
    status: WatermarkStatus
    is_valid: bool
    confidence: float            # 0.0 to 1.0 confidence score
    raw_ber: float = 0.0         # Pre-ECC raw bit error rate [0.0, 1.0]
    symbol_count: int = 0
    document_release_id: Optional[str] = None
    observed_symbols: List[Optional[int]] = Field(default_factory=list)  # 0, 1, or None (erasure)
    soft_confidences: List[float] = Field(default_factory=list)          # Symbol-wise margin [-1.0, +1.0]
    synchronization_success: bool = False
    homography_error: float = 0.0
    telemetry: Dict[str, Any] = Field(default_factory=dict)


class WatermarkEncoder(ABC):
    """Abstract Base Class for Watermark Encoders."""

    @abstractmethod
    def encode(
        self,
        carrier_input: Union[bytes, Any],
        payload: WatermarkPayload,
        **kwargs
    ) -> Any:
        """
        Embeds the watermark payload into the provided document carrier.
        Returns the watermarked carrier artifact (bytes or image array).
        """
        pass


class WatermarkDecoder(ABC):
    """Abstract Base Class for Watermark Decoders."""

    @abstractmethod
    def decode(
        self,
        captured_input: Union[bytes, Any],
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        expected_codeword_length: Optional[int] = None,
        codeword_length_hint: Optional[int] = None,
        **kwargs
    ) -> WatermarkObservation:
        """
        Detects, synchronizes, demodulates, and error-corrects the watermark
        from a digital or physical camera captured artifact.
        
        Enforces fail-closed semantics:
        - If expected_codeword_length is provided and does not match the decoded payload, returns INVALID.
        - If synchronization or carrier is missing/destroyed, returns NO_SIGNAL or PARTIAL.
        """
        pass
