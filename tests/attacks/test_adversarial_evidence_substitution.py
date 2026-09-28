import pytest
from core.attribution.engine import AttributionEngine, AttributionState
from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceObservation,
    EvidenceFamily,
    EvidenceSource,
    EvidenceConfidenceLevel,
    TargetBinding,
)
from core.attribution.dependency import EvidenceDependencyGraph
from core.attribution.fusion import EvidenceFusionEngine

@pytest.fixture
def evidence_fusion_env():
    fusion_engine = EvidenceFusionEngine()
    engine = AttributionEngine(fusion_engine=fusion_engine)
    return {
        "fusion_engine": fusion_engine,
        "engine": engine,
    }

def test_evidence_sub_correct_watermark_wrong_provenance(evidence_fusion_env):
    env = evidence_fusion_env
    bundle = EvidenceBundle(
        bundle_id="bnd_sub_01",
        target_binding=TargetBinding(document_id="doc_100", release_id="rel_100"),
        observations=[
            EvidenceObservation(
                source_id="obs_wmk_alice",
                family=EvidenceFamily.WATERMARK_PAYLOAD,
                target_binding=TargetBinding(document_id="doc_100", release_id="rel_100", recipient_id="alice"),
                primary_candidate="alice",
                log_likelihood_ratio=4.5
            ),
            EvidenceObservation(
                source_id="obs_prov_bob",
                family=EvidenceFamily.PROVENANCE_SIGNATURE,
                target_binding=TargetBinding(document_id="doc_100", release_id="rel_100", recipient_id="bob"),
                primary_candidate="bob",
                log_likelihood_ratio=4.5
            )
        ]
    )
    res = env["engine"].analyze_evidence_bundle(bundle)
    assert res.state in (AttributionState.CONFLICT, AttributionState.INSUFFICIENT_EVIDENCE)
    assert res.should_abstain is True

def test_evidence_sub_correct_tardos_wrong_release_scope(evidence_fusion_env):
    env = evidence_fusion_env
    bundle = EvidenceBundle(
        bundle_id="bnd_sub_02",
        target_binding=TargetBinding(document_id="doc_100", release_id="rel_100"),
        observations=[
            EvidenceObservation(
                source_id="obs_tardos_foreign",
                family=EvidenceFamily.TARDOS_FINGERPRINT,
                target_binding=TargetBinding(document_id="doc_100", release_id="rel_FOREIGN_999", recipient_id="alice"),
                primary_candidate="alice",
                log_likelihood_ratio=4.0
            )
        ]
    )
    res = env["engine"].analyze_evidence_bundle(bundle)
    assert res.state in (AttributionState.CONFLICT, AttributionState.INSUFFICIENT_EVIDENCE, AttributionState.NO_SIGNAL)

def test_evidence_sub_duplicate_observation_deduplication(evidence_fusion_env):
    env = evidence_fusion_env
    obs = EvidenceObservation(
        source_id="obs_wmk_dup",
        family=EvidenceFamily.WATERMARK_PAYLOAD,
        target_binding=TargetBinding(document_id="doc_100", release_id="rel_100", recipient_id="alice"),
        primary_candidate="alice",
        log_likelihood_ratio=4.0
    )
    bundle = EvidenceBundle(
        bundle_id="bnd_sub_dup",
        target_binding=TargetBinding(document_id="doc_100", release_id="rel_100"),
        observations=[obs, obs.model_copy(deep=True), obs.model_copy(deep=True)]
    )
    res = env["engine"].analyze_evidence_bundle(bundle)
    assert res.confidence <= 0.99

def test_evidence_sub_conflicting_document_ids(evidence_fusion_env):
    env = evidence_fusion_env
    bundle = EvidenceBundle(
        bundle_id="bnd_sub_conflicting_docs",
        target_binding=TargetBinding(document_id="doc_100", release_id="rel_100"),
        observations=[
            EvidenceObservation(
                source_id="obs_doc_100",
                family=EvidenceFamily.WATERMARK_PAYLOAD,
                target_binding=TargetBinding(document_id="doc_100", release_id="rel_100", recipient_id="alice"),
                primary_candidate="alice",
                log_likelihood_ratio=4.0
            ),
            EvidenceObservation(
                source_id="obs_doc_200",
                family=EvidenceFamily.TARDOS_FINGERPRINT,
                target_binding=TargetBinding(document_id="doc_200", release_id="rel_100", recipient_id="alice"),
                primary_candidate="alice",
                log_likelihood_ratio=4.0
            )
        ]
    )
    res = env["engine"].analyze_evidence_bundle(bundle)
    assert res.state in (AttributionState.CONFLICT, AttributionState.INSUFFICIENT_EVIDENCE)
    assert res.should_abstain is True

def test_evidence_sub_conflicting_key_epochs(evidence_fusion_env):
    env = evidence_fusion_env
    bundle = EvidenceBundle(
        bundle_id="bnd_epoch_conflict",
        target_binding=TargetBinding(document_id="doc_100", release_id="rel_100", traceability_key_id="tkey_epoch1"),
        observations=[
            EvidenceObservation(
                source_id="obs_epoch_1",
                family=EvidenceFamily.TARDOS_FINGERPRINT,
                target_binding=TargetBinding(document_id="doc_100", release_id="rel_100", recipient_id="alice", traceability_key_id="tkey_epoch1"),
                primary_candidate="alice",
                log_likelihood_ratio=4.0
            ),
            EvidenceObservation(
                source_id="obs_epoch_2",
                family=EvidenceFamily.PROVENANCE_SIGNATURE,
                target_binding=TargetBinding(document_id="doc_100", release_id="rel_100", recipient_id="alice", traceability_key_id="tkey_epoch2"),
                primary_candidate="alice",
                log_likelihood_ratio=4.0
            )
        ]
    )
    res = env["engine"].analyze_evidence_bundle(bundle)
    assert res.state in (AttributionState.CONFLICT, AttributionState.INSUFFICIENT_EVIDENCE)
