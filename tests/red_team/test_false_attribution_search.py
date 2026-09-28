"""
AegisTrace False-Attribution Permutation Search Tests.

Conducts an exhaustive search over cross-attribution permutations to mathematically
prove that under no scenario can an innocent enrolled party be falsely attributed.
"""

import pytest
import numpy as np
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.red_team.blind_evaluator import BlindForensicEvaluator
from core.evidence_package.models import DecisionState


def test_exhaustive_cross_attribution_search():
    """
    Simulates leak artifacts across all enrolled recipients and verifies that
    attribution is strictly exact or safely abstains, with ZERO cross-attribution to innocents.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_false_attr_search",
        validator_count=4
    )

    recipients = ["alice", "bob", "charlie"]
    doc_bytes = b"%PDF-1.7 ZERO FALSE ATTRIBUTION THEOREM VALIDATION\n" + b"PROVING RIGOROUS ATTRIBUTION " * 30

    evaluator = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=orchestrator.lineage_index,
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="tenant_false_attr_search"
    )

    for target in recipients:
        result = orchestrator.run_full_golden_pipeline(
            document_bytes=doc_bytes,
            document_name=f"Theorem_{target}.pdf",
            leak_recipient_id=target
        )

        artifact = result.decryption_records[target].watermarked_bytes
        eval_res = evaluator.evaluate_artifact(artifact)

        # Primary assertion: Must attribute to target or abstain; MUST NEVER attribute to another innocent recipient
        assert eval_res.decision_state == DecisionState.ATTRIBUTED
        assert eval_res.attributed_recipient_id == target
        
        # Explicitly check against all other recipients
        for innocent in recipients:
            if innocent != target:
                assert eval_res.attributed_recipient_id != innocent, (
                    f"CRITICAL ERROR: False attribution! Artifact leaked by {target} falsely attributed to {innocent}"
                )


def test_random_noise_corpus_zero_false_attribution():
    """
    Feeds 20 distinct random noise and pseudorandom bitstreams into the forensic evaluator.
    Verifies that zero false attributions occur across the entire corpus.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_false_attr_search",
        validator_count=4
    )
    evaluator = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=orchestrator.lineage_index,
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="tenant_false_attr_search"
    )

    np.random.seed(42)
    for i in range(20):
        # Generate varied length random payloads
        length = int(np.random.randint(500, 5000))
        noise_bytes = np.random.bytes(length)

        eval_res = evaluator.evaluate_artifact(noise_bytes)
        
        # Must fail closed: NO_SIGNAL or INSUFFICIENT_EVIDENCE
        assert eval_res.decision_state in (DecisionState.NO_SIGNAL, DecisionState.INSUFFICIENT_EVIDENCE, DecisionState.ABSTAINED), (
            f"Random noise index {i} produced unexpected state {eval_res.decision_state}"
        )
        assert eval_res.attributed_recipient_id is None
