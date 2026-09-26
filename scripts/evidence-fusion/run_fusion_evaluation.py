import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import time
from typing import Dict, Any, List

from core.attribution.evidence import (
    AttributionState,
    EvidenceFamily,
    DependencyType,
    EvidenceConfidenceLevel,
    TargetBinding,
    EvidenceObservation,
    WatermarkObservation,
    TraceabilityObservation,
    ProvenanceObservation,
    LedgerObservation,
    IntegrityObservation,
    AttackContextObservation,
    EvidenceBundle,
)
from core.attribution.engine import AttributionEngine
from core.attribution.policy import DecisionPolicy

def generate_benchmark_scenarios() -> List[Dict[str, Any]]:
    scenarios = []

    # Scenario 1: Clean Uncompromised Multi-Channel Leak (Alice)
    b1 = EvidenceBundle(
        bundle_id="SCENARIO_01_CLEAN_ALICE",
        target_binding=TargetBinding(document_id="DOC_100", release_id="REL_A")
    )
    b1.add_observation(WatermarkObservation(
        source_id="wm_01",
        title="Spatial Watermark",
        primary_candidate="alice",
        log_likelihood_ratio=6.0,
        bit_error_rate=0.01,
        target_binding=TargetBinding(document_id="DOC_100", release_id="REL_A")
    ))
    b1.add_observation(TraceabilityObservation(
        source_id="tardos_01",
        title="Tardos Fingerprint",
        dependency_type=DependencyType.DERIVED,
        parent_source_id="wm_01",
        primary_candidate="alice",
        log_likelihood_ratio=8.5,
        margin_over_threshold=7.0,
        target_binding=TargetBinding(document_id="DOC_100", release_id="REL_A")
    ))
    b1.add_observation(ProvenanceObservation(
        source_id="pqc_01",
        title="ML-DSA-65 Signature",
        signer_recipient_id="alice",
        signature_valid=True,
        log_likelihood_ratio=10.0,
        primary_candidate="alice",
        target_binding=TargetBinding(document_id="DOC_100", release_id="REL_A")
    ))
    scenarios.append({
        "name": "Clean Multi-Channel Leak",
        "bundle": b1,
        "expected_state": AttributionState.ATTRIBUTED,
        "expected_candidate": "alice",
        "category": "TRUE_POSITIVE"
    })

    # Scenario 2: Severe JPEG Recompression & Print-Scan Degradation (Bob)
    b2 = EvidenceBundle(
        bundle_id="SCENARIO_02_DEGRADED_BOB",
        target_binding=TargetBinding(document_id="DOC_200", release_id="REL_B"),
        attack_context=AttackContextObservation(
            source_id="att_02",
            title="Severe Print-Scan & Noise",
            execution_mode="PHYSICAL",
            crop_ratio=0.85,
            ssim=0.45
        )
    )
    b2.add_observation(WatermarkObservation(
        source_id="wm_02",
        title="Spatial Watermark",
        primary_candidate="bob",
        log_likelihood_ratio=2.5,
        bit_error_rate=0.38,  # High BER discounts reliability significantly
        target_binding=TargetBinding(document_id="DOC_200", release_id="REL_B")
    ))
    scenarios.append({
        "name": "Severe Attack Fail-Closed Abstention",
        "bundle": b2,
        "expected_state": AttributionState.INSUFFICIENT_EVIDENCE,
        "expected_candidate": "bob",
        "category": "CORRECT_ABSTENTION"
    })

    # Scenario 3: Inter-Channel Conflict (Watermark=Charlie vs Ledger=Dave)
    b3 = EvidenceBundle(
        bundle_id="SCENARIO_03_CONFLICT",
        target_binding=TargetBinding(document_id="DOC_300", release_id="REL_C")
    )
    b3.add_observation(WatermarkObservation(
        source_id="wm_charlie",
        title="Spatial Watermark",
        primary_candidate="charlie",
        log_likelihood_ratio=8.0,
        bit_error_rate=0.02,
        target_binding=TargetBinding(document_id="DOC_300", release_id="REL_C")
    ))
    b3.add_observation(EvidenceObservation(
        source_id="meta_dave",
        title="Document Structure Metadata",
        family=EvidenceFamily.DOCUMENT_STRUCTURE,
        primary_candidate="dave",
        log_likelihood_ratio=7.8,
        target_binding=TargetBinding(document_id="DOC_300", release_id="REL_C")
    ))
    scenarios.append({
        "name": "Inter-Channel Conflict",
        "bundle": b3,
        "expected_state": AttributionState.CONFLICT,
        "expected_candidate": None,
        "category": "CONFLICT_DETECTION"
    })

    # Scenario 4: Cross-Document Contamination
    b4 = EvidenceBundle(
        bundle_id="SCENARIO_04_CROSS_CONTAMINATION",
        target_binding=TargetBinding(document_id="DOC_TOP_SECRET", release_id="REL_X")
    )
    b4.add_observation(WatermarkObservation(
        source_id="wm_valid",
        title="Watermark",
        primary_candidate="eve",
        log_likelihood_ratio=6.0,
        target_binding=TargetBinding(document_id="DOC_TOP_SECRET", release_id="REL_X")
    ))
    b4.add_observation(LedgerObservation(
        source_id="ledg_alien",
        title="Alien Ledger Record",
        primary_candidate="eve",
        log_likelihood_ratio=7.0,
        target_binding=TargetBinding(document_id="DOC_PUBLIC", release_id="REL_Y")
    ))
    scenarios.append({
        "name": "Cross-Document Contamination",
        "bundle": b4,
        "expected_state": AttributionState.CONFLICT,
        "expected_candidate": None,
        "category": "CONTAMINATION_ISOLATION"
    })

    # Scenario 5: Complete No-Signal
    b5 = EvidenceBundle(
        bundle_id="SCENARIO_05_NO_SIGNAL",
        target_binding=TargetBinding(document_id="DOC_BLANK", release_id="REL_Z")
    )
    scenarios.append({
        "name": "Empty Evidence No-Signal",
        "bundle": b5,
        "expected_state": AttributionState.NO_SIGNAL,
        "expected_candidate": None,
        "category": "NO_SIGNAL"
    })

    return scenarios

def run_evaluation() -> Dict[str, Any]:
    engine = AttributionEngine()
    scenarios = generate_benchmark_scenarios()

    results = []
    passed_count = 0

    start_time = time.time()

    for sc in scenarios:
        res = engine.analyze_evidence_bundle(sc["bundle"])
        is_state_match = (res.state == sc["expected_state"])
        if sc["expected_candidate"]:
            is_candidate_match = (res.top_candidate_id == sc["expected_candidate"])
        else:
            is_candidate_match = (res.top_candidate_id is None or res.should_abstain)

        success = is_state_match and is_candidate_match
        if success:
            passed_count += 1

        results.append({
            "scenario": sc["name"],
            "bundle_id": sc["bundle"].bundle_id,
            "category": sc["category"],
            "expected_state": sc["expected_state"].value,
            "actual_state": res.state.value,
            "expected_candidate": sc["expected_candidate"],
            "actual_candidate": res.top_candidate_id,
            "fused_score": round(res.fused_score, 3),
            "confidence": round(res.confidence, 4),
            "confidence_level": res.confidence_level.value,
            "should_abstain": res.should_abstain,
            "passed": success,
            "summary": res.summary,
            "reasoning_steps": res.reasoning_steps
        })

    duration = time.time() - start_time

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_scenarios": len(scenarios),
        "passed_scenarios": passed_count,
        "accuracy_rate": passed_count / len(scenarios),
        "duration_seconds": round(duration, 4),
        "decision_policy": {
            "min_attribution_score": engine.fusion_engine.policy.min_attribution_score,
            "min_separation_margin": engine.fusion_engine.policy.min_separation_margin,
            "high_confidence_score": engine.fusion_engine.policy.high_confidence_score,
            "strict_provenance_required": engine.fusion_engine.policy.strict_provenance_required,
        },
        "scenario_results": results
    }

    # Ensure output directory exists
    out_dir = os.path.join("artifacts", "evidence-fusion")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "calibration_report.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[+] Evaluation Complete: {passed_count}/{len(scenarios)} passed ({report['accuracy_rate']*100:.1f}%)")
    print(f"[+] Calibration report saved to: {out_path}")
    return report

if __name__ == "__main__":
    run_evaluation()
