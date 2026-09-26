import hashlib
import uuid
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from core.attribution.evidence import (
    AttributionState,
    EvidenceFamily,
    EvidenceSource,
    TargetBinding,
    EvidenceObservation,
    WatermarkObservation,
    TraceabilityObservation,
    ProvenanceObservation,
    LedgerObservation,
    AttackContextObservation,
    EvidenceBundle,
)
from core.attribution.engine import AttributionEngine, AttributionResult, Candidate, EvidenceItem
from core.attribution.fusion import EvidenceFusionEngine, FusedAttributionResult
from core.attribution.policy import DecisionPolicy
from core.traceability.provider import (
    TraceabilityProvider,
    PrototypeTraceabilityProvider,
    TardosTraceabilityProvider,
)
from core.traceability.planner import TardosCapacityPlanner, CapacityPlanRequest, PlannerStatus
from apps.api.models import AttackTelemetryInput

class WatermarkAnalysisAdapter:
    """
    Application-level adapter contract for physical/digital watermark analysis.
    Bridges PrintCameraWatermarkDecoder to standardized EvidenceObservations
    while strictly enforcing fail-closed abstention on missing signals.
    """
    ADAPTER_NAME = "WatermarkAnalysisAdapter_v1.0"

    def analyze(
        self,
        artifact_bytes: bytes,
        target_binding: TargetBinding,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[WatermarkObservation]:
        """
        Attempts to extract watermark signals via PrintCameraWatermarkDecoder.
        If watermark extraction is unavailable, damaged, or fails, returns None.
        Missing watermark channels are 100% legal under fail-closed fusion.
        """
        try:
            from core.watermark.pipeline import PrintCameraWatermarkDecoder
            from core.watermark.base import WatermarkStatus

            decoder = PrintCameraWatermarkDecoder()
            exp_doc = target_binding.document_id
            exp_rel = target_binding.release_id
            codeword_hint = context.get("codeword_length_hint") if context else None

            wm_obs = decoder.decode(
                captured_input=artifact_bytes,
                expected_document_id=exp_doc,
                expected_release_id=exp_rel,
                codeword_length_hint=codeword_hint
            )

            if wm_obs.status == WatermarkStatus.RECOVERED and wm_obs.observed_symbols:
                llr = 10.0 * float(wm_obs.confidence)
                return WatermarkObservation(
                    source_id=f"wm_obs_{uuid.uuid4().hex[:8]}",
                    title="Physical Print-Camera Watermark Signal",
                    is_valid=True,
                    log_likelihood_ratio=llr,
                    bit_error_rate=float(wm_obs.raw_ber),
                    symbol_count=int(wm_obs.symbol_count),
                    symbols_extracted=len(wm_obs.observed_symbols),
                    carrier_type="PRINT_CAMERA_DSSS",
                    target_binding=target_binding,
                    details={
                        "status": wm_obs.status.value,
                        "reprojection_error": wm_obs.homography_error,
                        "synchronization_success": wm_obs.synchronization_success,
                        "telemetry": wm_obs.telemetry,
                        "observed_symbols": wm_obs.observed_symbols,
                    }
                )
            elif wm_obs.status == WatermarkStatus.PARTIAL and wm_obs.soft_confidences:
                llr = 2.0 * float(wm_obs.confidence)
                return WatermarkObservation(
                    source_id=f"wm_obs_{uuid.uuid4().hex[:8]}",
                    title="Partial Print-Camera Watermark Signal",
                    is_valid=True,
                    log_likelihood_ratio=llr,
                    bit_error_rate=float(wm_obs.raw_ber),
                    symbol_count=int(wm_obs.symbol_count),
                    symbols_extracted=len(wm_obs.soft_confidences),
                    carrier_type="PRINT_CAMERA_DSSS",
                    target_binding=target_binding,
                    details={
                        "status": wm_obs.status.value,
                        "reprojection_error": wm_obs.homography_error,
                        "synchronization_success": wm_obs.synchronization_success,
                        "telemetry": wm_obs.telemetry,
                        "soft_confidences": wm_obs.soft_confidences,
                    }
                )
            return None
        except Exception:
            return None

class AttackContextAdapter:
    """
    Adapter translating external attack lab telemetry into standardized
    AttackContextObservation payloads for the EvidenceBundle.
    """
    @classmethod
    def from_telemetry(
        cls,
        telemetry: Optional[AttackTelemetryInput],
        target_binding: TargetBinding
    ) -> Optional[AttackContextObservation]:
        if not telemetry:
            return None
        
        return AttackContextObservation(
            source_id=f"atk_{telemetry.attack_id or uuid.uuid4().hex[:8]}",
            title=f"Attack Lab Telemetry: {telemetry.attack_name or telemetry.attack_family or 'Generic'}",
            attack_family=telemetry.attack_family,
            attack_name=telemetry.attack_name,
            execution_mode=telemetry.execution_mode,
            psnr=telemetry.psnr,
            ssim=telemetry.ssim,
            crop_ratio=telemetry.crop_ratio,
            noise_level=telemetry.noise_level,
            target_binding=target_binding,
            details=telemetry.parameters
        )

class TraceabilityAdapter:
    """
    Adapter for Traceability providers, enforcing capacity checks
    and providing unified extraction for both prototype HMAC and Tardos codes.
    """
    def __init__(
        self,
        prototype_provider: Optional[PrototypeTraceabilityProvider] = None,
        tardos_provider: Optional[TardosTraceabilityProvider] = None
    ):
        self.prototype_provider = prototype_provider or PrototypeTraceabilityProvider()
        self.tardos_provider = tardos_provider or TardosTraceabilityProvider()

    def validate_capacity(
        self,
        recipient_count: int,
        coalition_size: int = 3,
        false_accusation_epsilon: float = 1e-4,
        carrier_budget: Optional[int] = None
    ) -> Tuple[bool, Optional[str], int]:
        req = CapacityPlanRequest(
            recipient_count=recipient_count,
            coalition_size=coalition_size,
            false_accusation_epsilon=false_accusation_epsilon,
            available_carrier_budget=carrier_budget
        )
        plan = TardosCapacityPlanner.plan(req)
        if plan.status == PlannerStatus.CAPACITY_INSUFFICIENT:
            return False, plan.reason, plan.required_code_length
        return True, None, plan.required_code_length

class EvidenceFusionAdapter:
    """
    Constructs an EvidenceBundle and invokes the attribution engine.
    Does NOT reimplement fusion logic.
    """
    def __init__(self, attribution_engine: Optional[AttributionEngine] = None):
        self.attribution_engine = attribution_engine or AttributionEngine()

    def execute_fusion(
        self,
        leaked_bytes: bytes,
        expected_release_id: Optional[str] = None,
        expected_document_id: Optional[str] = None,
        attack_telemetry: Optional[AttackTelemetryInput] = None
    ) -> AttributionResult:
        # Step 1: Use AttributionEngine.analyze_leak
        result = self.attribution_engine.analyze_leak(
            leaked_document_bytes=leaked_bytes,
            expected_release_id=expected_release_id
        )

        # Step 2: If expected_document_id is provided and candidate is found, verify document consistency
        if expected_document_id and result.candidate:
            # Check whether verified events match document
            for item in result.evidence_items:
                doc_in_item = item.details.get("document_id")
                if doc_in_item and doc_in_item != expected_document_id:
                    return AttributionResult(
                        state=AttributionState.CONFLICT,
                        candidate=None,
                        confidence=0.0,
                        confidence_level="NONE",
                        evidence_items=result.evidence_items,
                        summary=f"Abstain: Evidence document_id '{doc_in_item}' conflicts with expected '{expected_document_id}'.",
                        should_abstain=True
                    )

        return result
