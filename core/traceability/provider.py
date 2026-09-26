import os
import json
import hmac
import hashlib
import base64
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

class TraceabilityMarker(BaseModel):
    document_id: str
    release_id: str
    recipient_id: str
    document_hash: str
    signature_token: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TraceabilityEvidence(BaseModel):
    provider_name: str
    marker_found: bool
    document_id: Optional[str] = None
    release_id: Optional[str] = None
    recipient_id: Optional[str] = None
    document_hash: Optional[str] = None
    is_valid: bool = False
    confidence: float = 0.0  # 0.0 to 1.0
    verification_details: Dict[str, Any] = Field(default_factory=dict)

class TraceabilityProvider(ABC):
    """Abstract Base Class for Traceability Providers."""

    @abstractmethod
    def issue_marker(
        self,
        document_id: str,
        release_id: str,
        recipient_id: str,
        document_hash: str,
        secret_key: Optional[bytes] = None,
        **kwargs
    ) -> TraceabilityMarker:
        pass

    @abstractmethod
    def embed_marker(
        self,
        document_bytes: bytes,
        marker: TraceabilityMarker
    ) -> bytes:
        pass

    @abstractmethod
    def extract_marker(
        self,
        document_bytes: bytes
    ) -> Optional[TraceabilityMarker]:
        pass

    @abstractmethod
    def verify_marker(
        self,
        marker: TraceabilityMarker,
        secret_key: Optional[bytes] = None,
        expected_document_hash: Optional[str] = None
    ) -> bool:
        pass

    @abstractmethod
    def get_evidence(
        self,
        document_bytes: bytes,
        secret_key: Optional[bytes] = None,
        expected_document_hash: Optional[str] = None
    ) -> TraceabilityEvidence:
        pass

    @abstractmethod
    def estimate_confidence(self, evidence: TraceabilityEvidence) -> float:
        pass


class PrototypeTraceabilityProvider(TraceabilityProvider):
    """
    PrototypeTraceabilityProvider (v0.1):
    Cryptographically authenticated recipient-specific marker bound to:
    (document_id, release_id, recipient_id, document_hash).
    Uses HMAC-SHA256 for cryptographic authentication binding.
    """
    PROVIDER_NAME = "PrototypeTraceabilityProvider_v0.1"
    DEFAULT_SECRET_KEY = b"SIH26237-TRACEABILITY-PROTOTYPE-HMAC-KEY-V1"
    MARKER_HEADER = b"SIH26237-TRACEABILITY-MARKER-START"
    MARKER_FOOTER = b"SIH26237-TRACEABILITY-MARKER-END"

    def __init__(self, provider_secret: Optional[bytes] = None):
        self.provider_secret = provider_secret or self.DEFAULT_SECRET_KEY

    def _compute_token(
        self,
        document_id: str,
        release_id: str,
        recipient_id: str,
        document_hash: str,
        secret_key: Optional[bytes] = None
    ) -> str:
        key = secret_key or self.provider_secret
        msg = f"{document_id}:{release_id}:{recipient_id}:{document_hash}".encode('utf-8')
        return hmac.new(key, msg, hashlib.sha256).hexdigest()

    def issue_marker(
        self,
        document_id: str,
        release_id: str,
        recipient_id: str,
        document_hash: str,
        secret_key: Optional[bytes] = None,
        **kwargs
    ) -> TraceabilityMarker:
        from datetime import datetime, timezone
        token = self._compute_token(document_id, release_id, recipient_id, document_hash, secret_key)
        return TraceabilityMarker(
            document_id=document_id,
            release_id=release_id,
            recipient_id=recipient_id,
            document_hash=document_hash,
            signature_token=token,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=kwargs.get("metadata", {})
        )

    def embed_marker(
        self,
        document_bytes: bytes,
        marker: TraceabilityMarker
    ) -> bytes:
        """
        Embed marker into document. For PDF files or raw byte documents,
        appends a structural metadata trailer or stream object without corrupting valid PDF parsers.
        """
        marker_json = json.dumps(marker.model_dump()).encode('utf-8')
        payload = (
            b"\n%% " + self.MARKER_HEADER + b"\n"
            + b"%% " + base64.b64encode(marker_json) + b"\n"
            + b"%% " + self.MARKER_FOOTER + b"\n"
        )
        return document_bytes + payload

    def extract_marker(
        self,
        document_bytes: bytes
    ) -> Optional[TraceabilityMarker]:
        start_idx = document_bytes.find(self.MARKER_HEADER)
        if start_idx == -1:
            return None
        
        end_idx = document_bytes.find(self.MARKER_FOOTER, start_idx)
        if end_idx == -1:
            return None

        # Extract base64 payload
        block = document_bytes[start_idx:end_idx]
        lines = block.split(b"\n")
        for line in lines:
            line_str = line.strip()
            if line_str.startswith(b"%% ") and not line_str.startswith(b"%% SIH26237"):
                b64_data = line_str[3:].strip()
                try:
                    json_bytes = base64.b64decode(b64_data)
                    data = json.loads(json_bytes.decode('utf-8'))
                    return TraceabilityMarker(**data)
                except Exception:
                    return None
        return None

    def verify_marker(
        self,
        marker: TraceabilityMarker,
        secret_key: Optional[bytes] = None,
        expected_document_hash: Optional[str] = None
    ) -> bool:
        if expected_document_hash and marker.document_hash != expected_document_hash:
            return False
        
        expected_token = self._compute_token(
            marker.document_id,
            marker.release_id,
            marker.recipient_id,
            marker.document_hash,
            secret_key
        )
        # Constant time comparison
        return hmac.compare_digest(marker.signature_token, expected_token)

    def get_evidence(
        self,
        document_bytes: bytes,
        secret_key: Optional[bytes] = None,
        expected_document_hash: Optional[str] = None
    ) -> TraceabilityEvidence:
        marker = self.extract_marker(document_bytes)
        if not marker:
            return TraceabilityEvidence(
                provider_name=self.PROVIDER_NAME,
                marker_found=False,
                is_valid=False,
                confidence=0.0,
                verification_details={"reason": "Marker missing or not detected in carrier payload"}
            )
        
        is_valid = self.verify_marker(marker, secret_key, expected_document_hash)
        confidence = self.estimate_confidence(
            TraceabilityEvidence(
                provider_name=self.PROVIDER_NAME,
                marker_found=True,
                document_id=marker.document_id,
                release_id=marker.release_id,
                recipient_id=marker.recipient_id,
                document_hash=marker.document_hash,
                is_valid=is_valid
            )
        ) if is_valid else 0.0

        return TraceabilityEvidence(
            provider_name=self.PROVIDER_NAME,
            marker_found=True,
            document_id=marker.document_id,
            release_id=marker.release_id,
            recipient_id=marker.recipient_id,
            document_hash=marker.document_hash,
            is_valid=is_valid,
            confidence=confidence,
            verification_details={
                "signature_token": marker.signature_token,
                "timestamp": marker.timestamp,
                "verified": is_valid
            }
        )

    def estimate_confidence(self, evidence: TraceabilityEvidence) -> float:
        if not evidence.marker_found or not evidence.is_valid:
            return 0.0
        # For v0.1 cryptographic marker with verified HMAC binding
        return 0.99
