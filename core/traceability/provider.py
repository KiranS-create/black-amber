import os
import json
import hmac
import hashlib
import base64
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple, List
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


from core.traceability.keystore import (
    TraceabilityKeystore,
    KeyEpochUnavailableError,
    KeyEpochMismatchError,
)

class PrototypeTraceabilityProvider(TraceabilityProvider):
    """
    PrototypeTraceabilityProvider (v0.1):
    Cryptographically authenticated recipient-specific marker bound to:
    (document_id, release_id, recipient_id, document_hash).
    Uses HMAC-SHA256 for cryptographic authentication binding.
    """
    PROVIDER_NAME = "PrototypeTraceabilityProvider_v0.1"
    PROTOCOL_VERSION = "v0.1"
    CODEBOOK_VERSION = "prototype-hmac-v0.1"
    MARKER_HEADER = b"SIH26237-TRACEABILITY-MARKER-START"
    MARKER_FOOTER = b"SIH26237-TRACEABILITY-MARKER-END"

    def __init__(self, provider_secret: Optional[bytes] = None):
        self.provider_secret = TraceabilityKeystore.resolve_secret(provider_secret)
        self.key_id = TraceabilityKeystore.compute_key_id(self.provider_secret)

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
        effective_key = secret_key or self.provider_secret
        key_id = TraceabilityKeystore.compute_key_id(effective_key)
        metadata = kwargs.get("metadata", {}).copy()
        metadata.update({
            "key_id": key_id,
            "protocol_version": self.PROTOCOL_VERSION,
            "codebook_version": self.CODEBOOK_VERSION,
        })

        return TraceabilityMarker(
            document_id=document_id,
            release_id=release_id,
            recipient_id=recipient_id,
            document_hash=document_hash,
            signature_token=token,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata
        )

    def embed_marker(
        self,
        document_bytes: bytes,
        marker: TraceabilityMarker
    ) -> bytes:
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
        
        marker_key_id = marker.metadata.get("key_id")
        effective_key = None

        if secret_key is not None:
            if marker_key_id and TraceabilityKeystore.compute_key_id(secret_key) != marker_key_id:
                return False
            effective_key = secret_key
        elif marker_key_id:
            hist_key = TraceabilityKeystore.get_key_by_id(marker_key_id)
            if hist_key is not None:
                effective_key = hist_key
            elif marker_key_id == self.key_id:
                effective_key = self.provider_secret
            else:
                # Key epoch unavailable, fail closed
                return False
        else:
            effective_key = self.provider_secret

        expected_token = self._compute_token(
            marker.document_id,
            marker.release_id,
            marker.recipient_id,
            marker.document_hash,
            effective_key
        )
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
        
        marker_key_id = marker.metadata.get("key_id")
        epoch_status = "ACTIVE"

        if secret_key is not None:
            if marker_key_id and TraceabilityKeystore.compute_key_id(secret_key) != marker_key_id:
                return TraceabilityEvidence(
                    provider_name=self.PROVIDER_NAME,
                    marker_found=True,
                    document_id=marker.document_id,
                    release_id=marker.release_id,
                    recipient_id=marker.recipient_id,
                    document_hash=marker.document_hash,
                    is_valid=False,
                    confidence=0.0,
                    verification_details={
                        "reason": f"Supplied secret does not match marker key epoch '{marker_key_id}'",
                        "key_id": marker_key_id,
                        "key_epoch_status": "KEY_EPOCH_MISMATCH",
                        "protocol_version": marker.metadata.get("protocol_version", "v0.1")
                    }
                )
            epoch_status = "EXPLICIT_KEY"
        elif marker_key_id:
            hist_key = TraceabilityKeystore.get_key_by_id(marker_key_id)
            if hist_key is not None:
                epoch_status = "ACTIVE" if marker_key_id == self.key_id else "HISTORICAL"
            elif marker_key_id == self.key_id:
                epoch_status = "ACTIVE"
            else:
                return TraceabilityEvidence(
                    provider_name=self.PROVIDER_NAME,
                    marker_found=True,
                    document_id=marker.document_id,
                    release_id=marker.release_id,
                    recipient_id=marker.recipient_id,
                    document_hash=marker.document_hash,
                    is_valid=False,
                    confidence=0.0,
                    verification_details={
                        "reason": f"Required key epoch '{marker_key_id}' is unavailable in keystore registry",
                        "key_id": marker_key_id,
                        "key_epoch_status": "KEY_EPOCH_UNAVAILABLE",
                        "protocol_version": marker.metadata.get("protocol_version", "v0.1")
                    }
                )
        else:
            epoch_status = "LEGACY_PRE_EPOCH"

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
                "verified": is_valid,
                "key_id": marker_key_id,
                "key_epoch_status": epoch_status,
                "protocol_version": marker.metadata.get("protocol_version", self.PROTOCOL_VERSION),
                "codebook_version": marker.metadata.get("codebook_version", self.CODEBOOK_VERSION)
            }
        )

    def estimate_confidence(self, evidence: TraceabilityEvidence) -> float:
        if not evidence.marker_found or not evidence.is_valid:
            return 0.0
        return 0.99


class TardosTraceabilityProvider(TraceabilityProvider):
    """
    TardosTraceabilityProvider (v1.0):
    Production-oriented traitor-tracing provider based on Symbol-Symmetric Tardos codes.
    
    Features:
    - Enforces capacity feasibility through TardosCapacityPlanner before issuing marks.
    - Generates recipient-specific binary fingerprint codewords X_i in {0, 1}^m.
    - Cryptographically binds markers to (document_id, release_id, recipient_id, document_hash, codeword).
    - Exposes analyze_collusion_leak() to score observed leaked symbols against the codebook,
      providing formal false-accusation bounds (epsilon_1) and fail-closed abstention.
    - Supports multi-epoch historical forensics: verifies artifacts across rotation epochs
      via direct O(1) key_id lookup in TraceabilityKeystore.
    """
    PROVIDER_NAME = "TardosTraceabilityProvider_v1.0"
    PROTOCOL_VERSION = "v1.0"
    CODEBOOK_VERSION = "tardos-sym-v1.0"
    MARKER_HEADER = b"SIH26237-TARDOS-MARKER-START"
    MARKER_FOOTER = b"SIH26237-TARDOS-MARKER-END"

    def __init__(
        self,
        coalition_size: int = 3,
        false_accusation_epsilon: float = 1e-4,
        carrier_budget: Optional[int] = None,
        recipient_count_hint: int = 10,
        kappa_factor: float = 20.0,
        provider_secret: Optional[bytes] = None
    ):
        self.coalition_size = coalition_size
        self.false_accusation_epsilon = false_accusation_epsilon
        self.carrier_budget = carrier_budget
        self.recipient_count_hint = recipient_count_hint
        self.kappa_factor = kappa_factor
        self.provider_secret = TraceabilityKeystore.resolve_secret(provider_secret)
        self.key_id = TraceabilityKeystore.compute_key_id(self.provider_secret)

    def _derive_release_seed(
        self,
        document_id: str,
        release_id: str,
        secret_key: Optional[bytes] = None
    ) -> bytes:
        key = secret_key or self.provider_secret
        msg = f"{document_id}:{release_id}:seed".encode('utf-8')
        return hmac.new(key, msg, hashlib.sha256).digest()

    def _compute_token(
        self,
        document_id: str,
        release_id: str,
        recipient_id: str,
        document_hash: str,
        codeword_digest: str,
        secret_key: Optional[bytes] = None
    ) -> str:
        key = secret_key or self.provider_secret
        msg = f"{document_id}:{release_id}:{recipient_id}:{document_hash}:{codeword_digest}".encode('utf-8')
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
        from core.traceability.planner import TardosCapacityPlanner, CapacityPlanRequest, PlannerStatus
        from core.traceability.tardos import SymmetricTardosEngine

        c = kwargs.get("coalition_size", self.coalition_size)
        eps = kwargs.get("false_accusation_epsilon", self.false_accusation_epsilon)
        N = kwargs.get("recipient_count", self.recipient_count_hint)
        carrier_budget = kwargs.get("carrier_budget", self.carrier_budget)
        kappa = kwargs.get("kappa_factor", self.kappa_factor)

        # 1. Capacity Planning Check
        plan_req = CapacityPlanRequest(
            recipient_count=N,
            coalition_size=c,
            false_accusation_epsilon=eps,
            available_carrier_budget=carrier_budget,
            kappa_factor=kappa
        )
        plan_res = TardosCapacityPlanner.plan(plan_req)
        if plan_res.status == PlannerStatus.CAPACITY_INSUFFICIENT:
            raise ValueError(
                f"Capacity insufficient: carrier budget {carrier_budget} < required {plan_res.required_code_length} "
                f"for c={c}, N={N}, epsilon={eps}"
            )

        # 2. Derive release seed and generate codeword for this recipient
        effective_key = secret_key or self.provider_secret
        key_id = TraceabilityKeystore.compute_key_id(effective_key)
        code_length = plan_res.available_code_length or plan_res.required_code_length
        release_seed = self._derive_release_seed(document_id, release_id, effective_key)
        biases = SymmetricTardosEngine.generate_biases(code_length, c, release_seed)
        codebook = SymmetricTardosEngine.generate_codebook([recipient_id], biases, release_seed)
        codeword = codebook[recipient_id]

        # 3. Cryptographic binding token
        codeword_bytes = bytes(codeword)
        codeword_digest = hashlib.sha256(codeword_bytes).hexdigest()
        token = self._compute_token(
            document_id, release_id, recipient_id, document_hash, codeword_digest, effective_key
        )

        metadata = kwargs.get("metadata", {}).copy()
        metadata.update({
            "key_id": key_id,
            "protocol_version": self.PROTOCOL_VERSION,
            "codebook_version": self.CODEBOOK_VERSION,
            "tardos_codeword": codeword,
            "codeword_digest": codeword_digest,
            "code_length": code_length,
            "coalition_size": c,
            "false_accusation_epsilon": eps,
            "threshold": plan_res.accusation_threshold,
            "cutoff_parameter_t": plan_res.cutoff_parameter_t,
            "kappa_factor": kappa
        })

        return TraceabilityMarker(
            document_id=document_id,
            release_id=release_id,
            recipient_id=recipient_id,
            document_hash=document_hash,
            signature_token=token,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata
        )

    def embed_marker(
        self,
        document_bytes: bytes,
        marker: TraceabilityMarker
    ) -> bytes:
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
        
        codeword = marker.metadata.get("tardos_codeword")
        if not codeword:
            return False
        
        codeword_bytes = bytes(codeword)
        codeword_digest = hashlib.sha256(codeword_bytes).hexdigest()

        marker_key_id = marker.metadata.get("key_id")
        effective_key = None

        if secret_key is not None:
            if marker_key_id and TraceabilityKeystore.compute_key_id(secret_key) != marker_key_id:
                return False
            effective_key = secret_key
        elif marker_key_id:
            hist_key = TraceabilityKeystore.get_key_by_id(marker_key_id)
            if hist_key is not None:
                effective_key = hist_key
            elif marker_key_id == self.key_id:
                effective_key = self.provider_secret
            else:
                # Required key epoch unavailable in keystore
                return False
        else:
            effective_key = self.provider_secret

        expected_token = self._compute_token(
            marker.document_id,
            marker.release_id,
            marker.recipient_id,
            marker.document_hash,
            codeword_digest,
            effective_key
        )
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
                verification_details={"reason": "Tardos marker missing or not detected"}
            )
        
        marker_key_id = marker.metadata.get("key_id")
        epoch_status = "ACTIVE"

        if secret_key is not None:
            if marker_key_id and TraceabilityKeystore.compute_key_id(secret_key) != marker_key_id:
                return TraceabilityEvidence(
                    provider_name=self.PROVIDER_NAME,
                    marker_found=True,
                    document_id=marker.document_id,
                    release_id=marker.release_id,
                    recipient_id=marker.recipient_id,
                    document_hash=marker.document_hash,
                    is_valid=False,
                    confidence=0.0,
                    verification_details={
                        "reason": f"Supplied secret does not match marker key epoch '{marker_key_id}'",
                        "key_id": marker_key_id,
                        "key_epoch_status": "KEY_EPOCH_MISMATCH",
                        "protocol_version": marker.metadata.get("protocol_version", "v1.0")
                    }
                )
            epoch_status = "EXPLICIT_KEY"
        elif marker_key_id:
            hist_key = TraceabilityKeystore.get_key_by_id(marker_key_id)
            if hist_key is not None:
                epoch_status = "ACTIVE" if marker_key_id == self.key_id else "HISTORICAL"
            elif marker_key_id == self.key_id:
                epoch_status = "ACTIVE"
            else:
                return TraceabilityEvidence(
                    provider_name=self.PROVIDER_NAME,
                    marker_found=True,
                    document_id=marker.document_id,
                    release_id=marker.release_id,
                    recipient_id=marker.recipient_id,
                    document_hash=marker.document_hash,
                    is_valid=False,
                    confidence=0.0,
                    verification_details={
                        "reason": f"Required key epoch '{marker_key_id}' is unavailable in keystore registry",
                        "key_id": marker_key_id,
                        "key_epoch_status": "KEY_EPOCH_UNAVAILABLE",
                        "protocol_version": marker.metadata.get("protocol_version", "v1.0")
                    }
                )
        else:
            epoch_status = "LEGACY_PRE_EPOCH"

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
                "verified": is_valid,
                "key_id": marker_key_id,
                "key_epoch_status": epoch_status,
                "protocol_version": marker.metadata.get("protocol_version", self.PROTOCOL_VERSION),
                "codebook_version": marker.metadata.get("codebook_version", self.CODEBOOK_VERSION),
                "code_length": marker.metadata.get("code_length"),
                "coalition_size": marker.metadata.get("coalition_size")
            }
        )

    def estimate_confidence(self, evidence: TraceabilityEvidence) -> float:
        if not evidence.marker_found or not evidence.is_valid:
            return 0.0
        return 0.999

    def analyze_collusion_leak(
        self,
        observed_symbols: List[int],
        all_recipient_ids: List[str],
        document_id: str,
        release_id: str,
        secret_key: Optional[bytes] = None,
        key_id: Optional[str] = None,
        coalition_size: Optional[int] = None,
        false_accusation_epsilon: Optional[float] = None
    ):
        """
        Analyze an observed/leaked sequence of carrier symbols against the population of recipients.
        Supports key_id epoch lookup for historical forensic analysis.
        
        Returns TardosAccusationResult detailing scores, accused recipients, threshold margin,
        and statistical confidence under the Marking Assumption.
        """
        from core.traceability.tardos import SymmetricTardosEngine, AccusationStatus, TardosAccusationResult

        c = coalition_size or self.coalition_size
        eps = false_accusation_epsilon or self.false_accusation_epsilon
        m = len(observed_symbols)
        N = len(all_recipient_ids)

        if m == 0 or N == 0:
            return TardosAccusationResult(
                status=AccusationStatus.NO_SIGNAL,
                accused_recipients=[],
                scores={},
                threshold=0.0,
                max_score=0.0,
                margin=0.0,
                mean_score=0.0,
                score_std_dev=0.0,
                false_accusation_bound=eps,
                observed_length=0,
                details={"reason": "Empty observed symbols or recipient population"}
            )

        # Resolve effective secret for this epoch
        effective_secret = None
        if secret_key is not None:
            if key_id and TraceabilityKeystore.compute_key_id(secret_key) != key_id:
                return TardosAccusationResult(
                    status=AccusationStatus.NO_SIGNAL,
                    accused_recipients=[],
                    scores={},
                    threshold=0.0,
                    max_score=0.0,
                    margin=0.0,
                    mean_score=0.0,
                    score_std_dev=0.0,
                    false_accusation_bound=eps,
                    observed_length=m,
                    details={"reason": f"Supplied secret does not match requested epoch '{key_id}'"}
                )
            effective_secret = secret_key
        elif key_id is not None:
            hist_key = TraceabilityKeystore.get_key_by_id(key_id)
            if hist_key is not None:
                effective_secret = hist_key
            elif key_id == self.key_id:
                effective_secret = self.provider_secret
            else:
                return TardosAccusationResult(
                    status=AccusationStatus.NO_SIGNAL,
                    accused_recipients=[],
                    scores={},
                    threshold=0.0,
                    max_score=0.0,
                    margin=0.0,
                    mean_score=0.0,
                    score_std_dev=0.0,
                    false_accusation_bound=eps,
                    observed_length=m,
                    details={"reason": f"Required key epoch '{key_id}' is unavailable in keystore registry"}
                )
        else:
            effective_secret = self.provider_secret

        # 1. Reconstruct biases and codebook for this release
        release_seed = self._derive_release_seed(document_id, release_id, effective_secret)
        biases = SymmetricTardosEngine.generate_biases(m, c, release_seed)
        codebook = SymmetricTardosEngine.generate_codebook(all_recipient_ids, biases, release_seed)

        # 2. Score all recipients
        scores = SymmetricTardosEngine.score_all(observed_symbols, codebook, biases)

        # 3. Compute threshold Z
        threshold = SymmetricTardosEngine.compute_threshold(m, N, eps)

        # 4. Count erasures
        erasure_count = sum(1 for sym in observed_symbols if sym == -1)

        # 5. Evaluate accusation
        return SymmetricTardosEngine.accuse(
            scores=scores,
            threshold=threshold,
            epsilon_1=eps,
            observed_length=m,
            erasure_count=erasure_count
        )

