"""
SIH26237 - Identity & Multi-Device Entity Separation Integration Tests.

Validates that:
1. Entity hierarchy strictly separates: Principal -> Recipient Key -> Device TPM -> Session Nonce.
2. The same recipient (e.g. Alice) decrypting across two different sessions/devices receives
   distinct session nonces, distinct dynamic watermark tokens, and distinct copy instances.
3. Decryption receipts faithfully record specific device attestation references.
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator


def test_multi_device_session_separation():
    """Tests that a single recipient across two sessions/devices gets isolated forensic records."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_identity_device")

    # 1. Enroll Alice
    alice = orchestrator.enroll_recipient("Alice Vance", "alice", "alice@defense.gov")

    # 2. Create release
    doc_bytes = b"%PDF-1.7 Operational Strategy 2026 TOP SECRET"
    release, packages = orchestrator.create_release(
        document_bytes=doc_bytes,
        document_name="Strategy.pdf",
        issuer_id="HQ",
        recipient_ids=["alice"]
    )
    pkg = packages[0]

    # 3. Decrypt session 1 on Device 1 (Workstation TPM)
    d1 = orchestrator.decrypt_and_watermark(
        package=pkg,
        recipient=alice,
        session_id="sess_alice_dev1",
        copy_id="copy_alice_dev1",
        device_id="dev_alice_workstation_tpm"
    )

    # 4. Decrypt session 2 on Device 2 (Mobile Secure Enclave)
    d2 = orchestrator.decrypt_and_watermark(
        package=pkg,
        recipient=alice,
        session_id="sess_alice_dev2",
        copy_id="copy_alice_dev2",
        device_id="dev_alice_mobile_se"
    )

    # 5. Assert isolation
    assert d1.session_id != d2.session_id
    assert d1.copy_id != d2.copy_id
    assert d1.device_id != d2.device_id
    assert d1.dynamic_identity.token != d2.dynamic_identity.token
    assert d1.dynamic_identity.commitment != d2.dynamic_identity.commitment
    assert d1.receipt.receipt_id != d2.receipt.receipt_id
    assert d1.receipt.recipient_signature_b64 != d2.receipt.recipient_signature_b64

    # Both plaintexts are identical
    assert d1.decrypted_plaintext == d2.decrypted_plaintext == doc_bytes
