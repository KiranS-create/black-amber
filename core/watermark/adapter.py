"""
SIH26237 - Watermark-to-Traceability Adapter
Bridges the physical watermark recovery layer with the Tardos traitor-tracing engine.
Decouples physical carrier transport from cryptographic identity and mathematical scoring,
strictly enforcing fail-closed evidence abstention.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from core.watermark.base import WatermarkObservation, WatermarkStatus
from core.traceability.provider import TardosTraceabilityProvider, TraceabilityEvidence
from core.traceability.tardos import TardosAccusationResult, AccusationStatus


class PhysicalTraceabilityResult(BaseModel):
    """
    Combined forensic outcome integrating physical watermark observation
    with Tardos accusation mathematics.
    """
    watermark_status: WatermarkStatus
    attribution_status: AccusationStatus
    accused_recipients: List[str] = Field(default_factory=list)
    tardos_confidence: float = 0.0
    watermark_confidence: float = 0.0
    fused_confidence: float = 0.0
    scores: Dict[str, float] = Field(default_factory=dict)
    threshold: float = 0.0
    margin: float = 0.0
    raw_ber: float = 0.0
    reprojection_error: float = 0.0
    telemetry: Dict[str, Any] = Field(default_factory=dict)


class WatermarkTraceabilityAdapter:
    """
    Adapter consuming WatermarkObservation objects and orchestrating
    Tardos collusion analysis without modifying core/traceability.
    """

    def __init__(self, tardos_provider: Optional[TardosTraceabilityProvider] = None):
        self.tardos_provider = tardos_provider or TardosTraceabilityProvider()

    def evaluate_observation(
        self,
        observation: WatermarkObservation,
        all_recipient_ids: List[str],
        document_id: str,
        release_id: str,
        secret_key: Optional[bytes] = None
    ) -> PhysicalTraceabilityResult:
        """
        Evaluates a physical watermark observation against the candidate recipient cohort.
        Enforces fail-closed semantics:
          - NO_SIGNAL or INVALID observations abstain immediately.
          - PARTIAL observations evaluate soft/erasure symbols with conservative weighting.
          - RECOVERED observations execute full Tardos symmetric accusation scoring.
        """
        telemetry = {
            "watermark_telemetry": observation.telemetry,
            "synchronization_success": observation.synchronization_success,
            "homography_error": observation.homography_error
        }

        # 1. Fail-closed check: No signal
        if observation.status == WatermarkStatus.NO_SIGNAL:
            return PhysicalTraceabilityResult(
                watermark_status=WatermarkStatus.NO_SIGNAL,
                attribution_status=AccusationStatus.NO_SIGNAL,
                accused_recipients=[],
                tardos_confidence=0.0,
                watermark_confidence=0.0,
                fused_confidence=0.0,
                telemetry={"reason": "Watermark signal absent or fiducials destroyed"}
            )

        # 2. Fail-closed check: Invalid or transplanted document
        if observation.status == WatermarkStatus.INVALID:
            return PhysicalTraceabilityResult(
                watermark_status=WatermarkStatus.INVALID,
                attribution_status=AccusationStatus.INSUFFICIENT_EVIDENCE,
                accused_recipients=[],
                tardos_confidence=0.0,
                watermark_confidence=0.0,
                fused_confidence=0.0,
                telemetry={"reason": "Document-release binding mismatch or CRC failure"}
            )

        # 3. Process recovered symbols or soft symbols
        symbols = observation.observed_symbols
        if not symbols and observation.soft_confidences:
            # Map soft confidences: > 0.1 -> 1, < -0.1 -> 0, else erasure
            symbols = [1 if sc > 0.0 else 0 for sc in observation.soft_confidences]

        if not symbols or len(symbols) == 0:
            return PhysicalTraceabilityResult(
                watermark_status=observation.status,
                attribution_status=AccusationStatus.NO_SIGNAL,
                accused_recipients=[],
                tardos_confidence=0.0,
                watermark_confidence=observation.confidence,
                fused_confidence=0.0,
                telemetry={"reason": "No symbols available for Tardos accusation"}
            )

        # 4. Invoke Tardos collusion analysis
        tardos_result: TardosAccusationResult = self.tardos_provider.analyze_collusion_leak(
            observed_symbols=symbols,
            all_recipient_ids=all_recipient_ids,
            document_id=document_id,
            release_id=release_id,
            secret_key=secret_key
        )

        # 5. Fuse confidences
        # Tardos confidence = 1.0 - false_accusation_bound if attributed else 0.0
        if tardos_result.status in (AccusationStatus.ATTRIBUTED, AccusationStatus.COLLUSION_DETECTED) and len(tardos_result.accused_recipients) > 0:
            tardos_conf = max(0.0, 1.0 - getattr(tardos_result, "false_accusation_bound", 0.001))
            fused_conf = round(float(observation.confidence * tardos_conf), 4)
        else:
            tardos_conf = 0.0
            fused_conf = 0.0

        return PhysicalTraceabilityResult(
            watermark_status=observation.status,
            attribution_status=tardos_result.status,
            accused_recipients=tardos_result.accused_recipients,
            tardos_confidence=round(tardos_conf, 4),
            watermark_confidence=observation.confidence,
            fused_confidence=fused_conf,
            scores=tardos_result.scores,
            threshold=tardos_result.threshold,
            margin=tardos_result.margin,
            raw_ber=observation.raw_ber,
            reprojection_error=observation.homography_error,
            telemetry=telemetry
        )

