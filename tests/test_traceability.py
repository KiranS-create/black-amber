import pytest
import os
import hashlib
from core.traceability.provider import PrototypeTraceabilityProvider, TraceabilityMarker

def test_trace_marker():
    """Verify marker issuance, embedding, extraction, and verification."""
    provider = PrototypeTraceabilityProvider()
    doc_bytes = b"%PDF-1.4 Mock PDF document content for testing"
    doc_hash = hashlib.sha256(doc_bytes).hexdigest()

    marker = provider.issue_marker(
        document_id="doc_100",
        release_id="rel_200",
        recipient_id="bob",
        document_hash=doc_hash
    )

    embedded = provider.embed_marker(doc_bytes, marker)
    assert len(embedded) > len(doc_bytes)

    extracted = provider.extract_marker(embedded)
    assert extracted is not None
    assert extracted.recipient_id == "bob"
    assert extracted.release_id == "rel_200"

    assert provider.verify_marker(extracted, expected_document_hash=doc_hash) is True

def test_forged_marker():
    """Verify that forged signature token fails marker verification."""
    provider = PrototypeTraceabilityProvider()
    forged_marker = TraceabilityMarker(
        document_id="doc_100",
        release_id="rel_200",
        recipient_id="bob",
        document_hash="hash_123",
        signature_token="fake_forged_hmac_token",
        timestamp="2026-09-26T12:00:00Z"
    )
    assert provider.verify_marker(forged_marker) is False

def test_modified_marker():
    """Verify that modified document hash or recipient fails verification."""
    provider = PrototypeTraceabilityProvider()
    marker = provider.issue_marker("doc_1", "rel_1", "alice", "hash_abc")

    # Modify recipient without updating HMAC token
    modified = marker.model_copy(update={"recipient_id": "bob"})
    assert provider.verify_marker(modified) is False
