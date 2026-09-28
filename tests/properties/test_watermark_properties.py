"""
tests/properties/test_watermark_properties.py

Property-based testing and adversarial fuzzing for Dynamic Watermarking and Traceability:
- INVARIANT-006: Watermark cryptographic context binding
- Random noise and malformed token non-attribution
- Context substitution rejection (wrong recipient, wrong document, wrong release)
- Watermark corruption monotonicity and fail-closed decoding
"""

import copy
import hashlib
import pytest
from core.traceability.provider import (
    PrototypeTraceabilityProvider,
    TraceabilityMarker,
)
from core.testing.property_engine import PropertyRunner, DeterministicGenerator
from core.security.invariants import assert_invariant


def test_property_watermark_context_binding_invariant(runner: PropertyRunner):
    """
    INVARIANT-006: A watermark token is cryptographically bound to:
    (document_id, release_id, recipient_id, document_hash).
    Altering any single component must cause verify_marker() to strictly return False.
    """
    secret = b"test_secret_watermark_seed_32bytes!"
    provider = PrototypeTraceabilityProvider(provider_secret=secret)

    def prop(g: DeterministicGenerator):
        doc_id = g.generate_document_id()
        rel_id = f"REL-{g.alphanumeric(6, 8)}"
        rec_id = g.generate_recipient_id()
        doc_hash = hashlib.sha256(g.bytes_data(64)).hexdigest()

        # 1. Issue authentic marker
        marker = provider.issue_marker(
            document_id=doc_id,
            release_id=rel_id,
            recipient_id=rec_id,
            document_hash=doc_hash,
        )

        # Baseline: Authentic marker verifies cleanly
        assert provider.verify_marker(marker, expected_document_hash=doc_hash) is True

        # Choose an adversarial context substitution
        attack_type = g.choice([
            "substitute_recipient",
            "substitute_document",
            "substitute_release",
            "substitute_hash",
            "corrupt_token",
        ])

        tampered = copy.deepcopy(marker)

        if attack_type == "substitute_recipient":
            tampered.recipient_id = f"rec-attacker-{g.alphanumeric(4, 6)}"
        elif attack_type == "substitute_document":
            tampered.document_id = g.generate_document_id()
        elif attack_type == "substitute_release":
            tampered.release_id = f"REL-EVIL-{g.alphanumeric(4, 6)}"
        elif attack_type == "substitute_hash":
            tampered.document_hash = hashlib.sha256(g.bytes_data(32)).hexdigest()
        elif attack_type == "corrupt_token":
            tampered.signature_token = g.mutate_string(marker.signature_token)

        # Invariant: verify_marker must reject tampered context
        valid = provider.verify_marker(tampered, expected_document_hash=doc_hash)
        assert_invariant(
            valid is False,
            "INVARIANT-006",
            f"Watermark verified after context attack '{attack_type}'",
            g.seed,
            counterexample={"attack": attack_type, "original_recipient": rec_id},
        )

    res = runner.run_property("watermark_context_binding", prop, iterations=250)
    assert res.passed, res.error_message


def test_property_random_noise_never_creates_valid_attribution(runner: PropertyRunner):
    """
    Property: Feeding arbitrary random noise or corrupted payload into marker extraction
    and verification never resolves as a valid authenticated recipient.
    """
    secret = b"random_noise_test_secret_32bytes!!"
    provider = PrototypeTraceabilityProvider(provider_secret=secret)

    def prop(g: DeterministicGenerator):
        noise_bytes = g.bytes_data(g.integer(16, 2048))
        evidence = provider.get_evidence(noise_bytes)

        # If no marker header is found, marker_found must be False and is_valid must be False
        assert evidence.is_valid is False
        assert evidence.confidence == 0.0

    res = runner.run_property("random_noise_non_attribution", prop, iterations=200)
    assert res.passed, res.error_message


def test_property_watermark_transplanted_fragment_rejection(runner: PropertyRunner):
    """
    Property: Splicing or transplanting a marker fragment between two documents
    fails verification against the destination document's hash.
    """
    secret = b"transplant_test_secret_32bytes!!!"
    provider = PrototypeTraceabilityProvider(provider_secret=secret)

    def prop(g: DeterministicGenerator):
        doc_a_id = g.generate_document_id(1)
        doc_b_id = g.generate_document_id(2)
        doc_a_hash = hashlib.sha256(b"DOC_A_CONTENT").hexdigest()
        doc_b_hash = hashlib.sha256(b"DOC_B_CONTENT").hexdigest()

        marker_a = provider.issue_marker(
            document_id=doc_a_id,
            release_id="REL-001",
            recipient_id="rec-alice",
            document_hash=doc_a_hash,
        )

        # Embedded into doc A
        dummy_pdf_a = b"%PDF-1.4\n" + b"A" * 100
        marked_doc_a = provider.embed_marker(dummy_pdf_a, marker_a)

        # Extract from doc A
        extracted = provider.extract_marker(marked_doc_a)
        assert extracted is not None

        # Verify against doc B (transplanted context)
        valid_in_doc_b = provider.verify_marker(extracted, expected_document_hash=doc_b_hash)
        assert valid_in_doc_b is False

    res = runner.run_property("watermark_transplant_rejection", prop, iterations=100)
    assert res.passed, res.error_message
