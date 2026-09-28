"""
SIH26237 - Multi-Recipient Equivalence & Forensic Distinction Integration Tests.

Validates that:
1. All recipients (Alice, Bob, Charlie) receive identical decrypted document plaintexts.
2. Rendered watermarked pages exhibit high visual equivalence (PSNR >= 28 dB, SSIM >= 0.70).
3. Every recipient receives unique, forensically distinct dynamic watermark tokens,
   cryptographic commitments, orthogonal codewords, distinct ML-DSA-65 signatures,
   and isolated DLT Merkle leaves.
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.integration.equivalence import MultiRecipientEquivalenceAnalyzer


def test_multi_recipient_equivalence_and_isolation():
    """Audits multi-recipient release across Alice, Bob, and Charlie."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_defense_equivalence")
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")

    analyzer = MultiRecipientEquivalenceAnalyzer()
    report = analyzer.analyze_decryptions(
        decryptions=result.decryption_records,
        document_id=result.document_id,
        release_id=result.release_id
    )

    # 1. Overall Equivalence Verdict
    assert report.overall_verdict == "EQUIVALENT_AND_FORENSICALLY_DISTINCT"
    assert report.is_semantically_identical is True
    assert report.is_visually_equivalent is True
    assert report.is_forensically_distinct is True
    assert report.recipient_count == 3

    # 2. Pairwise Invariants
    for comp in report.pairwise_comparisons:
        assert comp.plaintext_exact_match is True
        assert comp.is_visually_equivalent is True
        assert comp.is_forensically_distinct is True
        assert comp.tokens_distinct is True
        assert comp.commitments_distinct is True
        assert comp.signatures_distinct is True
        assert comp.codeword_hamming_distance > 0
        assert abs(comp.codeword_cross_correlation) <= 0.35

    # 3. Individual Profiles
    alice_p = report.profiles["alice"]
    bob_p = report.profiles["bob"]
    charlie_p = report.profiles["charlie"]

    assert alice_p.token != bob_p.token != charlie_p.token
    assert alice_p.commitment != bob_p.commitment != charlie_p.commitment
    assert alice_p.copy_id != bob_p.copy_id != charlie_p.copy_id
