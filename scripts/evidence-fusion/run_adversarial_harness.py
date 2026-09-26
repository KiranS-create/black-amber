import os
import sys
import json
import random
import time
from typing import Dict, Any, List, Tuple, Set, Optional

sys.path.insert(0, os.path.abspath("."))

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

def generate_synthetic_dataset(seed: int = 42, num_scenarios: int = 200) -> List[Dict[str, Any]]:
    """
    Generate reproducible synthetic evidence scenarios across diverse recipient pool sizes,
    attack degradation levels, dependency topographies, and conflict states.
    """
    rng = random.Random(seed)
    dataset = []

    pool_sizes = [3, 10, 50, 100]
    strengths = ["none", "weak", "medium", "strong"]
    attack_modes = ["none", "jpeg", "crop", "print_camera", "tampered", "wrong_doc"]
    conflict_types = ["none", "weak_conflict", "strong_conflict"]

    for i in range(num_scenarios):
        sc_id = f"SYNTH_{i+1:04d}"
        n_recipients = rng.choice(pool_sizes)
        recipients = [f"recipient_{k+1}" for k in range(n_recipients)]
        
        # Ground truth primary target recipient (or None if un-enrolled leak)
        primary_target = rng.choice(recipients) if rng.random() > 0.15 else None

        strength = rng.choice(strengths)
        attack_mode = rng.choice(attack_modes)
        conflict_type = rng.choice(conflict_types)

        doc_id = f"DOC_{sc_id}"
        rel_id = f"REL_{sc_id}"

        target_binding = TargetBinding(document_id=doc_id, release_id=rel_id)
        bundle = EvidenceBundle(bundle_id=sc_id, target_binding=target_binding)

        has_primary_evidence = False
        has_rival_evidence = False
        has_mismatched_binding = False
        rival_candidate = None

        # Attack telemetry
        if attack_mode == "print_camera":
            bundle.attack_context = AttackContextObservation(
                source_id=f"{sc_id}_att", title="Print-Camera Capture",
                execution_mode="PHYSICAL", crop_ratio=0.80, ssim=0.55
            )
        elif attack_mode == "crop":
            bundle.attack_context = AttackContextObservation(
                source_id=f"{sc_id}_att", title="Severe Crop",
                execution_mode="SIMULATED", crop_ratio=0.40, ssim=0.75
            )
        elif attack_mode == "jpeg":
            bundle.attack_context = AttackContextObservation(
                source_id=f"{sc_id}_att", title="JPEG Recompression",
                execution_mode="SIMULATED", crop_ratio=1.0, ssim=0.60
            )

        # Build primary recipient observations
        if primary_target and strength != "none":
            has_primary_evidence = True
            llr_base = 3.0 if strength == "weak" else (7.0 if strength == "medium" else 11.0)
            ber = 0.02 if strength == "strong" else (0.15 if strength == "medium" else 0.35)
            wm_bind = target_binding if attack_mode != "wrong_doc" else TargetBinding(document_id="WRONG_DOC", release_id=rel_id)
            if attack_mode == "wrong_doc":
                has_mismatched_binding = True

            # 1. Primary Watermark Channel
            obs_wm = WatermarkObservation(
                source_id=f"{sc_id}_wm", title="Spatial Watermark",
                primary_candidate=primary_target,
                log_likelihood_ratio=llr_base * 0.7,
                bit_error_rate=ber, symbol_count=100, symbols_extracted=100,
                target_binding=wm_bind
            )
            bundle.add_observation(obs_wm)

            # 2. Derived Tardos Fingerprint
            obs_tardos = TraceabilityObservation(
                source_id=f"{sc_id}_tardos", title="Tardos Statistic",
                dependency_type=DependencyType.DERIVED, parent_source_id=f"{sc_id}_wm",
                primary_candidate=primary_target,
                log_likelihood_ratio=llr_base * 0.9,
                margin_over_threshold=6.0 if strength == "strong" else 2.0,
                target_binding=wm_bind
            )
            bundle.add_observation(obs_tardos)

            # 3. Provenance Signature
            if strength in ("medium", "strong") and attack_mode != "tampered":
                obs_pqc = ProvenanceObservation(
                    source_id=f"{sc_id}_pqc", title="ML-DSA Signature",
                    signer_recipient_id=primary_target, signature_valid=True,
                    log_likelihood_ratio=llr_base * 1.0, primary_candidate=primary_target,
                    target_binding=wm_bind
                )
                bundle.add_observation(obs_pqc)

        # Force a mismatched binding observation if wrong_doc attack mode
        if attack_mode == "wrong_doc":
            has_mismatched_binding = True
            if not has_primary_evidence:
                dummy_target = primary_target or recipients[0]
                bundle.add_observation(WatermarkObservation(
                    source_id=f"{sc_id}_mismatch_wm", title="Mismatched Watermark",
                    primary_candidate=dummy_target, log_likelihood_ratio=7.0,
                    bit_error_rate=0.02, symbol_count=100, symbols_extracted=100,
                    target_binding=TargetBinding(document_id="WRONG_DOC", release_id=rel_id)
                ))

        # Inject Rival Conflict if requested
        if conflict_type != "none" and len(recipients) > 1:
            candidates_for_rival = [r for r in recipients if r != primary_target]
            if candidates_for_rival:
                rival_candidate = rng.choice(candidates_for_rival)
                has_rival_evidence = True
                rival_llr = 4.5 if conflict_type == "weak_conflict" else 9.5
                
                if conflict_type == "strong_conflict":
                    obs_conflict = WatermarkObservation(
                        source_id=f"{sc_id}_rival_wm", title="Conflicting Watermark",
                        primary_candidate=rival_candidate, log_likelihood_ratio=rival_llr,
                        bit_error_rate=0.01, symbol_count=100, symbols_extracted=100,
                        target_binding=target_binding
                    )
                else:
                    obs_conflict = EvidenceObservation(
                        source_id=f"{sc_id}_rival_struct", family=EvidenceFamily.DOCUMENT_STRUCTURE,
                        primary_candidate=rival_candidate, log_likelihood_ratio=rival_llr,
                        target_binding=target_binding
                    )
                bundle.add_observation(obs_conflict)

        # Determine Ground Truth Expected State and Expected Candidate
        expected_candidate = None

        if has_mismatched_binding:
            expected_state = AttributionState.CONFLICT
        elif has_primary_evidence and has_rival_evidence and conflict_type == "strong_conflict":
            expected_state = AttributionState.CONFLICT
        elif not has_primary_evidence and not has_rival_evidence:
            expected_state = AttributionState.NO_SIGNAL
        elif not has_primary_evidence and has_rival_evidence:
            if conflict_type == "strong_conflict":
                expected_state = AttributionState.ATTRIBUTED
                expected_candidate = rival_candidate
            else:
                expected_state = AttributionState.INSUFFICIENT_EVIDENCE
        elif strength == "weak" or attack_mode in ("crop", "print_camera", "jpeg"):
            expected_state = AttributionState.INSUFFICIENT_EVIDENCE
            expected_candidate = primary_target
        else:
            expected_state = AttributionState.ATTRIBUTED
            expected_candidate = primary_target

        dataset.append({
            "id": sc_id,
            "pool_size": n_recipients,
            "true_recipient": expected_candidate,
            "strength": strength,
            "attack_mode": attack_mode,
            "conflict_type": conflict_type,
            "expected_state": expected_state,
            "bundle": bundle
        })

    return dataset

def evaluate_harness():
    engine = AttributionEngine()
    dataset = generate_synthetic_dataset(seed=2026, num_scenarios=200)

    # Train/Calibration vs Evaluation split (100 / 100)
    train_set = dataset[:100]
    eval_set = dataset[100:]

    def process_split(split_data: List[Dict[str, Any]], split_name: str) -> Dict[str, Any]:
        results = []
        confusion_counts: Dict[str, Dict[str, int]] = {
            "TRUE_ATTRIBUTED": {"PRED_ATTR": 0, "PRED_ABSTAIN": 0, "PRED_CONFLICT": 0},
            "TRUE_NONE": {"PRED_ATTR": 0, "PRED_ABSTAIN": 0, "PRED_CONFLICT": 0},
            "TRUE_CONFLICT": {"PRED_ATTR": 0, "PRED_ABSTAIN": 0, "PRED_CONFLICT": 0}
        }

        correct_count = 0
        false_attribution_count = 0

        for item in split_data:
            res = engine.analyze_evidence_bundle(item["bundle"])

            # Map actual prediction
            if res.state == AttributionState.ATTRIBUTED:
                pred_cat = "PRED_ATTR"
            elif res.state == AttributionState.CONFLICT:
                pred_cat = "PRED_CONFLICT"
            else:
                pred_cat = "PRED_ABSTAIN"

            # Map ground truth
            if item["expected_state"] == AttributionState.ATTRIBUTED:
                truth_cat = "TRUE_ATTRIBUTED"
            elif item["expected_state"] == AttributionState.CONFLICT:
                truth_cat = "TRUE_CONFLICT"
            else:
                truth_cat = "TRUE_NONE"

            confusion_counts[truth_cat][pred_cat] += 1

            # False attribution check (attributed to wrong recipient)
            is_false_attribution = False
            if res.state == AttributionState.ATTRIBUTED:
                if item["true_recipient"] is None or res.top_candidate_id != item["true_recipient"]:
                    is_false_attribution = True
                    false_attribution_count += 1

            is_match = (res.state == item["expected_state"])
            if is_match and not is_false_attribution:
                correct_count += 1

            results.append({
                "id": item["id"],
                "pool_size": item["pool_size"],
                "true_recipient": item["true_recipient"],
                "predicted_recipient": res.top_candidate_id,
                "expected_state": item["expected_state"].value,
                "actual_state": res.state.value,
                "fused_score": round(res.fused_score, 3),
                "confidence": round(res.confidence, 4),
                "should_abstain": res.should_abstain,
                "is_false_attribution": is_false_attribution,
                "passed": is_match and not is_false_attribution
            })

        return {
            "split_name": split_name,
            "total_samples": len(split_data),
            "correct_decisions": correct_count,
            "false_attributions": false_attribution_count,
            "decision_match_rate": round(correct_count / len(split_data), 4),
            "confusion_matrix": confusion_counts,
            "scenarios": results
        }

    train_report = process_split(train_set, "Calibration/Train Split")
    eval_report = process_split(eval_set, "Held-Out Evaluation Split")

    out_dir = os.path.join("artifacts", "evidence-fusion")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Export adversarial_evaluation.json
    adv_path = os.path.join(out_dir, "adversarial_evaluation.json")
    with open(adv_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "evaluation_harness_version": "2.0.0",
            "eval_summary": {
                "total_scenarios": eval_report["total_samples"],
                "correct_decisions": eval_report["correct_decisions"],
                "false_attributions": eval_report["false_attributions"],
                "match_rate": eval_report["decision_match_rate"]
            },
            "eval_scenarios": eval_report["scenarios"]
        }, f, indent=2)

    # 2. Export confusion_matrix.json
    cm_path = os.path.join(out_dir, "confusion_matrix.json")
    with open(cm_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "train_confusion_matrix": train_report["confusion_matrix"],
            "eval_confusion_matrix": eval_report["confusion_matrix"]
        }, f, indent=2)

    # 3. Export calibration_vs_evaluation.json
    cal_path = os.path.join(out_dir, "calibration_vs_evaluation.json")
    with open(cal_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "train_set": {
                "sample_count": train_report["total_samples"],
                "decision_match_rate": train_report["decision_match_rate"],
                "false_attribution_count": train_report["false_attributions"]
            },
            "held_out_eval_set": {
                "sample_count": eval_report["total_samples"],
                "decision_match_rate": eval_report["decision_match_rate"],
                "false_attribution_count": eval_report["false_attributions"]
            }
        }, f, indent=2)

    print(f"[+] Harness Complete!")
    print(f"[+] Train Match Rate: {train_report['decision_match_rate']*100:.1f}% (False Accusations: {train_report['false_attributions']})")
    print(f"[+] Eval Match Rate:  {eval_report['decision_match_rate']*100:.1f}% (False Accusations: {eval_report['false_attributions']})")

if __name__ == "__main__":
    evaluate_harness()
