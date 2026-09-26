import os
import uuid
import base64
import hashlib
import tempfile
from pathlib import Path
import pytest
import numpy as np
import cv2

from apps.api.models import ArtifactType, DocumentMetadata, LeakMetadata
from apps.api.storage import MetadataRepository, FilesystemArtifactStorage
from apps.api.adapters import WatermarkAnalysisAdapter
from core.attribution.evidence import TargetBinding
from core.watermark.pipeline import PrintCameraWatermarkEncoder
from core.watermark.base import WatermarkPayload
from core.crypto.signatures import MLDSA65
from core.ledger.ledger import EvidenceEvent, TamperEvidentLedger
from core.recipient import Recipient


def test_sqlite_persistence_across_reloads(tmp_path):
    """Verify MetadataRepository reloads documents and leaks from SQLite across instances."""
    db_file = tmp_path / "metadata_test.sqlite3"
    repo1 = MetadataRepository(db_path=db_file)

    doc = DocumentMetadata(
        document_id="doc_test_123",
        document_name="Classified Briefing.pdf",
        original_document_hash="a" * 64,
        size_bytes=1024,
        mime_type="application/pdf",
        created_at="2026-09-26T12:00:00Z",
        artifact_id="art_orig_test_123"
    )
    repo1.save_document(doc)

    leak = LeakMetadata(
        leak_id="leak_test_456",
        leak_artifact_hash="b" * 64,
        size_bytes=2048,
        mime_type="application/pdf",
        suspected_document_id="doc_test_123",
        suspected_release_id="rel_test_789",
        created_at="2026-09-26T12:05:00Z",
        artifact_id="art_leak_test_456"
    )
    repo1.save_leak(leak)

    # Initialize new repository instance on the same SQLite file
    repo2 = MetadataRepository(db_path=db_file)

    loaded_doc = repo2.get_document("doc_test_123")
    assert loaded_doc is not None
    assert loaded_doc.document_name == "Classified Briefing.pdf"
    assert loaded_doc.original_document_hash == "a" * 64

    loaded_leak = repo2.get_leak("leak_test_456")
    assert loaded_leak is not None
    assert loaded_leak.suspected_document_id == "doc_test_123"
    assert loaded_leak.suspected_release_id == "rel_test_789"

    assert len(repo2.list_documents()) == 1


def test_filesystem_artifact_storage_persistence(tmp_path):
    """Verify FilesystemArtifactStorage recovers metadata index across restarts."""
    storage_dir = tmp_path / "artifacts"
    db_file = storage_dir / "meta.sqlite3"

    store1 = FilesystemArtifactStorage(storage_dir=storage_dir, db_path=db_file)
    data = b"CONFIDENTIAL AIR-GAPPED PAYLOAD FOR REPOSITORY AUDIT"
    meta = store1.store_artifact(
        data=data,
        artifact_type=ArtifactType.ORIGINAL_DOCUMENT,
        document_id="doc_pers_1",
        release_id="rel_pers_1",
        mime_type="application/octet-stream"
    )

    art_id = meta.artifact_id

    # Restart storage on the same directory
    store2 = FilesystemArtifactStorage(storage_dir=storage_dir, db_path=db_file)
    recovered_meta = store2.retrieve_metadata(art_id)
    assert recovered_meta is not None
    assert recovered_meta.artifact_id == art_id
    assert recovered_meta.sha256_hash == hashlib.sha256(data).hexdigest()
    assert recovered_meta.document_id == "doc_pers_1"

    recovered_bytes = store2.retrieve_artifact_bytes(art_id)
    assert recovered_bytes == data


def test_watermark_adapter_physical_recovery():
    """Verify WatermarkAnalysisAdapter decodes embedded signals and abstains on unwatermarked data."""
    adapter = WatermarkAnalysisAdapter()
    encoder = PrintCameraWatermarkEncoder()

    # Create dummy white canvas
    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 255
    cv2.putText(canvas, "TEST PAGE", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

    doc_id = "doc_test_wm"
    rel_id = "rel_test_wm"
    codeword = [1, 0, 1, 1, 0, 0, 1, 0] * 16  # 128-bit codeword

    payload = WatermarkPayload(
        document_id=doc_id,
        release_id=rel_id,
        codeword=codeword
    )

    watermarked_png = encoder.encode(canvas, payload, as_bytes=True, format="PNG")

    target_binding = TargetBinding(document_id=doc_id, release_id=rel_id)
    obs = adapter.analyze(
        artifact_bytes=watermarked_png,
        target_binding=target_binding,
        context={"codeword_length_hint": 128}
    )

    assert obs is not None
    assert obs.is_valid is True
    assert obs.log_likelihood_ratio > 0.0
    assert obs.symbol_count == 128
    assert obs.carrier_type == "PRINT_CAMERA_DSSS"

    # Test abstention on blank unwatermarked image
    _, blank_png = cv2.imencode(".png", canvas)
    blank_obs = adapter.analyze(
        artifact_bytes=bytes(blank_png),
        target_binding=target_binding,
        context={"codeword_length_hint": 128}
    )
    assert blank_obs is None

    # Test abstention on random bytes
    garbage_obs = adapter.analyze(
        artifact_bytes=os.urandom(256),
        target_binding=target_binding
    )
    assert garbage_obs is None


def test_ledger_dual_verification_signatures():
    """Verify TamperEvidentLedger detects signature forgery even when sequential hash chain is intact."""
    from core.recipient import RecipientRegistry
    registry = RecipientRegistry()
    recipient = registry.enroll(name="Alice Recipient")
    pub_bytes = recipient.dsa_keypair.public_key_bytes
    priv_bytes = recipient.dsa_keypair.private_key_bytes

    ledger = TamperEvidentLedger()

    event_id = "evt_dec_test_001"
    doc_id = "doc_test"
    rel_id = "rel_test"
    art_hash = "c" * 64
    prev_hash = TamperEvidentLedger.GENESIS_HASH
    timestamp = "2026-09-26T12:00:00Z"

    sign_payload = (
        f"DECRYPTION_PROVENANCE:{event_id}:{doc_id}:"
        f"{rel_id}:{recipient.recipient_id}:{art_hash}:"
        f"{prev_hash}:{timestamp}"
    ).encode('utf-8')

    valid_sig = MLDSA65.sign(priv_bytes, sign_payload)

    event = EvidenceEvent(
        event_id=event_id,
        event_type="DECRYPTION_EVENT",
        timestamp=timestamp,
        document_id=doc_id,
        release_id=rel_id,
        recipient_id=recipient.recipient_id,
        algorithm=MLDSA65.ALGORITHM_NAME,
        artifact_hash=art_hash,
        evidence_hash="d" * 64,
        previous_event_hash=prev_hash,
        signature=base64.b64encode(valid_sig).decode('utf-8'),
        signer_public_key_b64=base64.b64encode(pub_bytes).decode('utf-8'),
    )

    ledger.append_event(event)

    # 1. Verification with valid signature should succeed
    is_valid, errors = ledger.verify_chain_and_signatures()
    assert is_valid is True
    assert len(errors) == 0

    # 2. Forge second event: valid hash chain link, but forged signature
    eve = registry.enroll(name="Eve Impostor")
    event_id_2 = "evt_dec_test_002"
    prev_hash_2 = ledger.get_last_event_hash()

    fake_sign_payload = (
        f"DECRYPTION_PROVENANCE:{event_id_2}:{doc_id}:"
        f"{rel_id}:{recipient.recipient_id}:{art_hash}:"
        f"{prev_hash_2}:{timestamp}"
    ).encode('utf-8')

    # Eve signs claiming to be Alice
    forged_sig = MLDSA65.sign(eve.dsa_keypair.private_key_bytes, fake_sign_payload)

    forged_event = EvidenceEvent(
        event_id=event_id_2,
        event_type="DECRYPTION_EVENT",
        timestamp=timestamp,
        document_id=doc_id,
        release_id=rel_id,
        recipient_id=recipient.recipient_id,  # Claims to be Alice
        algorithm=MLDSA65.ALGORITHM_NAME,
        artifact_hash=art_hash,
        evidence_hash="e" * 64,
        previous_event_hash=prev_hash_2,
        signature=base64.b64encode(forged_sig).decode('utf-8'),
        signer_public_key_b64=base64.b64encode(pub_bytes).decode('utf-8'),  # Alice's public key
    )

    ledger.append_event(forged_event)

    # Standard chain verification only checks hashes (which match)
    chain_ok, chain_errs = ledger.verify_chain()
    assert chain_ok is True

    # Dual verification checks digital signature with Alice's public key -> MUST fail
    dual_ok, dual_errs = ledger.verify_chain_and_signatures()
    assert dual_ok is False
    assert any("Cryptographic signature mismatch" in err for err in dual_errs)
