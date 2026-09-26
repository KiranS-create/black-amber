import pytest
from core.traceability.provider import (
    PrototypeTraceabilityProvider,
    TardosTraceabilityProvider,
)
from core.traceability.collusion import (
    interleaving_collusion,
)
from core.traceability.tardos import (
    AccusationStatus,
)

def test_tardos_provider_roundtrip():
    """Verify issue, embed, extract, verify, and evidence retrieval for TardosTraceabilityProvider."""
    provider = TardosTraceabilityProvider(
        coalition_size=2,
        false_accusation_epsilon=1e-4,
        recipient_count_hint=10
    )

    doc_id = "doc-101"
    rel_id = "rel-202"
    rec_id = "bob"
    doc_hash = "d0c0ffee1234567890abcdef"
    sample_doc = b"%PDF-1.7\nSample document content for Bob\n%%EOF"

    # 1. Issue marker
    marker = provider.issue_marker(doc_id, rel_id, rec_id, doc_hash)
    assert marker.recipient_id == "bob"
    assert marker.document_id == doc_id
    assert marker.release_id == rel_id
    assert "tardos_codeword" in marker.metadata
    assert len(marker.metadata["tardos_codeword"]) > 0

    # 2. Embed marker into document
    marked_doc = provider.embed_marker(sample_doc, marker)
    assert len(marked_doc) > len(sample_doc)
    assert b"SIH26237-TARDOS-MARKER-START" in marked_doc

    # 3. Extract marker
    extracted = provider.extract_marker(marked_doc)
    assert extracted is not None
    assert extracted.recipient_id == "bob"
    assert extracted.signature_token == marker.signature_token
    assert extracted.metadata["tardos_codeword"] == marker.metadata["tardos_codeword"]

    # 4. Verify marker
    assert provider.verify_marker(extracted, expected_document_hash=doc_hash) is True

    # Tampered document hash fails verification
    assert provider.verify_marker(extracted, expected_document_hash="wrong_hash") is False

    # 5. Get Evidence
    evidence = provider.get_evidence(marked_doc, expected_document_hash=doc_hash)
    assert evidence.marker_found is True
    assert evidence.is_valid is True
    assert evidence.recipient_id == "bob"
    assert evidence.confidence > 0.99


def test_tardos_provider_capacity_insufficient_enforcement():
    """Verify that TardosTraceabilityProvider rejects marker issuance if carrier budget is insufficient."""
    provider = TardosTraceabilityProvider(
        coalition_size=3,
        false_accusation_epsilon=1e-5,
        carrier_budget=150,  # Far below ~2500+ required
        recipient_count_hint=15
    )

    with pytest.raises(ValueError, match="Capacity insufficient"):
        provider.issue_marker(
            document_id="doc-insufficient",
            release_id="rel-insufficient",
            recipient_id="alice",
            document_hash="hash123"
        )


def test_tardos_provider_analyze_collusion_leak():
    """Verify that analyze_collusion_leak successfully identifies colluders from extracted carrier symbols."""
    provider = TardosTraceabilityProvider(
        coalition_size=2,
        false_accusation_epsilon=1e-4,
        recipient_count_hint=10
    )

    doc_id = "doc-collusion"
    rel_id = "rel-collusion"
    doc_hash = "feedbeefcafebabe"

    all_recipients = [f"user_{i}" for i in range(10)]
    all_recipients[0] = "alice"
    all_recipients[1] = "bob"

    marker_alice = provider.issue_marker(doc_id, rel_id, "alice", doc_hash)
    marker_bob = provider.issue_marker(doc_id, rel_id, "bob", doc_hash)

    cw_alice = marker_alice.metadata["tardos_codeword"]
    cw_bob = marker_bob.metadata["tardos_codeword"]

    # Interleaving collusion between Alice and Bob
    forged_symbols = interleaving_collusion([cw_alice, cw_bob], seed=1234)

    # Analyze the leak
    result = provider.analyze_collusion_leak(
        observed_symbols=forged_symbols,
        all_recipient_ids=all_recipients,
        document_id=doc_id,
        release_id=rel_id
    )

    assert result.status in (AccusationStatus.ATTRIBUTED, AccusationStatus.COLLUSION_DETECTED)
    assert any(col in result.accused_recipients for col in ["alice", "bob"])
    for innocent_id in all_recipients[2:]:
        assert innocent_id not in result.accused_recipients


def test_clean_coexistence_with_prototype_provider():
    """Verify that PrototypeTraceabilityProvider and TardosTraceabilityProvider operate without collision."""
    proto_provider = PrototypeTraceabilityProvider()
    tardos_provider = TardosTraceabilityProvider()

    doc_bytes = b"Hello world document"
    proto_marker = proto_provider.issue_marker("d1", "r1", "alice", "h1")
    tardos_marker = tardos_provider.issue_marker("d1", "r1", "bob", "h1")

    proto_doc = proto_provider.embed_marker(doc_bytes, proto_marker)
    tardos_doc = tardos_provider.embed_marker(doc_bytes, tardos_marker)

    # Prototype cannot parse Tardos marker (different delimiters)
    assert proto_provider.extract_marker(tardos_doc) is None

    # Tardos cannot parse Prototype marker
    assert tardos_provider.extract_marker(proto_doc) is None

    # Each correctly parses its own
    assert proto_provider.extract_marker(proto_doc).recipient_id == "alice"
    assert tardos_provider.extract_marker(tardos_doc).recipient_id == "bob"
