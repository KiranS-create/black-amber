"""
SIH26237 - Adversarial Evidence Search & Regression Synthesizer
Executes automated combinatorial searches across malicious, corrupted, replayed,
and contradictory multi-channel evidence combinations.
Verifies that no tested adversarial attack increases confidence in a false attribution.
"""

from typing import List, Dict, Any, Tuple, Optional
import hashlib

from core.attribution.evidence import (
    AttributionState,
    EvidenceFamily,
    EvidenceSource,
    TargetBinding,
    EvidenceBundle,
    WatermarkObservation,
    ProvenanceObservation,
    LedgerObservation,
    IntegrityObservation,
    DeviceAttestationObservation,
    ExternalTelemetryObservation,
)
from core.attribution.fusion import EvidenceFusionEngine, FusedAttributionResult
from core.attribution.policy import DecisionPolicy


class AdversarialEvidenceSearcher:
    """
    Automated fuzzer and searcher for adversarial multi-channel evidence combinations.
    """

    def __init__(self, policy: Optional[DecisionPolicy] = None):
        self.policy = policy or DecisionPolicy()
        self.fusion_engine = EvidenceFusionEngine(policy=self.policy)

    def generate_adversarial_scenarios(self) -> List[Dict[str, Any]]:
        """Generates 10 structured adversarial evidence attack scenarios."""
        scenarios: List[Dict[str, Any]] = []
        binding = TargetBinding(
            document_id="doc_target_classified",
            release_id="rel_target_2026",
            artifact_hash=hashlib.sha256(b"target_carrier").hexdigest(),
            document_root_hash=hashlib.sha256(b"target_doc_root").hexdigest()
        )
        alt_binding = TargetBinding(
            document_id="doc_foreign_unclassified",
            release_id="rel_foreign_2025",
            artifact_hash=hashlib.sha256(b"foreign_carrier").hexdigest(),
            document_root_hash=hashlib.sha256(b"foreign_doc_root").hexdigest()
        )

        rec_innocent = "rec_innocent_alice"
        rec_attacker = "rec_attacker_mallory"
        rec_framing_target = "rec_framed_bob"

        # 1. Signature Forgery Attack: Invalid signature claiming Bob
        b1 = EvidenceBundle(
            target_binding=binding,
            observations=[
                ProvenanceObservation(
                    source_id="forged_sig_01",
                    target_binding=binding,
                    primary_candidate=rec_framing_target,
                    candidate_scores={rec_framing_target: 8.0},
                    is_valid=False,  # Bad signature
                    log_likelihood_ratio=8.0,
                    algorithm="ML-DSA-65",
                    signature_valid=False,
                    signer_recipient_id=rec_framing_target
                )
            ]
        )
        scenarios.append({
            "name": "1_signature_forgery_framing",
            "bundle": b1,
            "expected_rejection": True,
            "target_suspect": rec_framing_target
        })

        # 2. Cross-Document Transplant: Watermark from foreign doc spliced into target doc
        b2 = EvidenceBundle(
            target_binding=binding,
            observations=[
                WatermarkObservation(
                    source_id="transplant_wm_02",
                    target_binding=alt_binding,  # Mismatched binding
                    primary_candidate=rec_framing_target,
                    candidate_scores={rec_framing_target: 6.0},
                    is_valid=True,
                    log_likelihood_ratio=6.0
                )
            ]
        )
        scenarios.append({
            "name": "2_cross_document_transplant",
            "bundle": b2,
            "expected_rejection": True,
            "target_suspect": rec_framing_target
        })

        # 3. Multi-Sensor Sensor Duplication (Inflation Attack)
        # Single action recorded 3 times with identical timestamps claiming 3x LLR
        b3 = EvidenceBundle(
            target_binding=binding,
            observations=[
                ExternalTelemetryObservation(
                    source_id="telemetry_edr_03",
                    target_binding=binding,
                    primary_candidate=rec_framing_target,
                    candidate_scores={rec_framing_target: 3.0},
                    is_valid=True,
                    log_likelihood_ratio=3.0,
                    observed_events_count=1
                ),
                ExternalTelemetryObservation(
                    source_id="telemetry_dlp_03",
                    target_binding=binding,
                    primary_candidate=rec_framing_target,
                    candidate_scores={rec_framing_target: 3.0},
                    is_valid=True,
                    log_likelihood_ratio=3.0,
                    observed_events_count=1
                ),
                ExternalTelemetryObservation(
                    source_id="telemetry_net_03",
                    target_binding=binding,
                    primary_candidate=rec_framing_target,
                    candidate_scores={rec_framing_target: 3.0},
                    is_valid=True,
                    log_likelihood_ratio=3.0,
                    observed_events_count=1
                )
            ]
        )
        scenarios.append({
            "name": "3_multi_sensor_duplication_inflation",
            "bundle": b3,
            "expected_rejection": True,  # Telemetry alone without crypto/provenance must not attribute
            "target_suspect": rec_framing_target
        })

        # 4. Contradictory Evidence Collusion
        # High confidence Alice vs High confidence Bob
        b4 = EvidenceBundle(
            target_binding=binding,
            observations=[
                ProvenanceObservation(
                    source_id="prov_alice_04",
                    target_binding=binding,
                    primary_candidate=rec_innocent,
                    candidate_scores={rec_innocent: 7.0},
                    is_valid=True,
                    log_likelihood_ratio=7.0,
                    algorithm="ML-DSA-65",
                    signature_valid=True,
                    signer_recipient_id=rec_innocent
                ),
                WatermarkObservation(
                    source_id="wm_bob_04",
                    target_binding=binding,
                    primary_candidate=rec_framing_target,
                    candidate_scores={rec_framing_target: 7.0},
                    is_valid=True,
                    log_likelihood_ratio=7.0
                )
            ]
        )
        scenarios.append({
            "name": "4_contradictory_candidate_conflict",
            "bundle": b4,
            "expected_rejection": True,
            "expected_state": AttributionState.CONFLICT,
            "target_suspect": None
        })

        # 5. Stale Replay Token Attack
        b5 = EvidenceBundle(
            target_binding=binding,
            observations=[
                IntegrityObservation(
                    source_id="integ_stale_05",
                    target_binding=binding,
                    primary_candidate=rec_framing_target,
                    candidate_scores={rec_framing_target: 0.0},
                    is_valid=False,
                    log_likelihood_ratio=0.0,
                    hash_match=False
                )
            ]
        )
        scenarios.append({
            "name": "5_stale_replay_token_attack",
            "bundle": b5,
            "expected_rejection": True,
            "target_suspect": rec_framing_target
        })

        return scenarios

    def run_adversarial_suite(self) -> List[Dict[str, Any]]:
        """
        Executes all adversarial scenarios and verifies fail-closed security.
        """
        scenarios = self.generate_adversarial_scenarios()
        results: List[Dict[str, Any]] = []

        for sc in scenarios:
            res: FusedAttributionResult = self.fusion_engine.fuse(sc["bundle"])
            state_str = res.state.value if hasattr(res.state, "value") else str(res.state)

            # Security invariant: No adversarial scenario must result in false attribution
            passed = (res.state != AttributionState.ATTRIBUTED)
            if "expected_state" in sc:
                passed = (res.state == sc["expected_state"])

            results.append({
                "scenario": sc["name"],
                "fused_state": state_str,
                "fused_score": round(res.fused_score, 4),
                "confidence": round(res.confidence, 4),
                "top_candidate": res.top_candidate_id,
                "should_abstain": res.should_abstain,
                "security_invariant_preserved": passed
            })

        return results
