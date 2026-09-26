import pytest
from core.attribution.engine import AttributionEngine, AttributionState
from core.attribution.evidence import (
    EvidenceBundle,
    WatermarkObservation,
    TraceabilityObservation,
    ProvenanceObservation,
    LedgerObservation,
    IntegrityObservation,
    AttackContextObservation,
    DependencyType,
    TargetBinding
)

def test_multi_channel_fusion_end_to_end():
    engine = AttributionEngine()

    bundle = EvidenceBundle(
        bundle_id="bnd_full_e2e",
        target_binding=TargetBinding(document_id="DOC_SECRET_42", release_id="REL_ALPHA"),
        attack_context=AttackContextObservation(
            source_id="att_ctx",
            title="Attack Telemetry",
            execution_mode="SIMULATED",
            crop_ratio=1.0,
            ssim=0.88
        )
    )

    # 1. Watermark channel (BER=0.04)
    bundle.add_observation(WatermarkObservation(
        source_id="wm_01",
        title="Spatial Watermark",
        dependency_type=DependencyType.INDEPENDENT,
        log_likelihood_ratio=6.0,
        primary_candidate="carol",
        bit_error_rate=0.04,
        symbol_count=128,
        symbols_extracted=128,
        target_binding=TargetBinding(document_id="DOC_SECRET_42", release_id="REL_ALPHA")
    ))

    # 2. Tardos Traitor-Tracing (derived from watermark)
    bundle.add_observation(TraceabilityObservation(
        source_id="tardos_01",
        title="Tardos Scoring",
        dependency_type=DependencyType.DERIVED,
        parent_source_id="wm_01",
        log_likelihood_ratio=9.5,
        primary_candidate="carol",
        observed_length=2048,
        margin_over_threshold=8.0,
        theoretical_false_alarm_bound=1e-5,
        target_binding=TargetBinding(document_id="DOC_SECRET_42", release_id="REL_ALPHA")
    ))

    # 3. Post-Quantum Provenance Signature
    bundle.add_observation(ProvenanceObservation(
        source_id="pqc_01",
        title="ML-DSA-65 Signature",
        dependency_type=DependencyType.INDEPENDENT,
        signer_recipient_id="carol",
        signature_valid=True,
        log_likelihood_ratio=10.0,
        primary_candidate="carol",
        target_binding=TargetBinding(document_id="DOC_SECRET_42", release_id="REL_ALPHA")
    ))

    # 4. Tamper-Evident Ledger Event
    bundle.add_observation(LedgerObservation(
        source_id="ledg_01",
        title="Ledger Chain Verification",
        dependency_type=DependencyType.INDEPENDENT,
        chain_valid=True,
        matching_events_count=1,
        event_ids=["EVT_99182"],
        log_likelihood_ratio=5.0,
        primary_candidate="carol",
        target_binding=TargetBinding(document_id="DOC_SECRET_42", release_id="REL_ALPHA")
    ))

    result = engine.analyze_evidence_bundle(bundle)

    assert result.state == AttributionState.ATTRIBUTED
    assert result.top_candidate_id == "carol"
    assert result.should_abstain is False
    assert result.fused_score > 15.0
    assert result.confidence > 0.99
