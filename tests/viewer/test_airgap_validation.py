"""
SIH26237 - Air-Gapped Pipeline Validation Tests
Validates that the entire AegisTrace Controlled Viewer and Dynamic Decryption Pipeline:
Broadcast Encryption -> Recipient Decryption -> Dynamic Watermark -> Recipient ML-DSA-65 Signature
-> Offline DLT Quorum Consensus -> Multi-node Replication -> Controlled Export -> Leak Ingestion
-> Watermark Recovery -> Merkle Inclusion Proof -> Lineage Derivation -> Recipient Attribution
executes 100% locally with all network sockets disabled.
"""

import pytest
import socket
import os
import hashlib
import numpy as np
import cv2

from core.recipient import RecipientRegistry, Recipient
from core.release import ReleaseManager
from core.lineage.storage import LineageStorage
from core.lineage.service import LineageService
from core.lineage.viewer import ControlledViewer
from core.lineage.models import ExportFormat
from core.ledger.dlt import PermissionedDLTLedger
from core.provenance.decryption import RecipientDecryptionClient
from core.watermark.dynamic import DynamicWatermarkEngine
from core.lineage.forensics import DynamicForensicExtractor, ForensicVerificationStatus
from core.watermark.pipeline import CanonicalCanvasSpec, GeometricSynchronizer
from core.watermark.carrier import CarrierConfig


@pytest.fixture(autouse=True)
def enforce_airgap_socket_block(monkeypatch):
    """Strictly blocks all network socket creation to verify air-gap compliance."""
    def _blocked_socket(*args, **kwargs):
        raise RuntimeError("AIRGAP_ENFORCEMENT_VIOLATION: Network socket access is strictly prohibited.")

    monkeypatch.setattr(socket, "socket", _blocked_socket)


def test_airgap_canonical_end_to_end_pipeline():
    # 1. Initialize offline infrastructure
    registry = RecipientRegistry()
    alice = registry.enroll(
        name="Alice Henderson",
        email="alice@defense.gov",
        organization_id="Strategic Operations",
    )


    spec = CanonicalCanvasSpec()
    sync = GeometricSynchronizer(spec)
    cfg = CarrierConfig(embedding_strength_alpha=10.0)
    wm_engine = DynamicWatermarkEngine(canvas_spec=spec, carrier_config=cfg)


    dlt_ledger = PermissionedDLTLedger(num_validators=3, num_nodes=3)
    decryption_client = RecipientDecryptionClient(
        dlt_ledger=dlt_ledger,
        dynamic_wm_engine=wm_engine
    )

    storage = LineageStorage()
    lineage_service = LineageService(storage)
    viewer = ControlledViewer(
        lineage_service=lineage_service,
        dlt_ledger=dlt_ledger,
        dynamic_wm_engine=wm_engine,
        decryption_client=decryption_client
    )

    # 2. Master Document Preparation
    canvas = np.full((spec.height, spec.width), 245, dtype=np.uint8)
    cv2.rectangle(canvas, (140, 80), (660, 110), (40,), -1)
    cv2.putText(canvas, "CLASSIFIED FLIGHT LOGS", (160, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,), 2)
    for y in range(160, 820, 35):
        cv2.line(canvas, (140, y), (660, y), (60,), 2)
    
    anchored_base = sync.embed_fiducial_anchors(canvas)
    _, encoded_doc_bytes = cv2.imencode(".png", anchored_base)
    master_doc_bytes = bytes(encoded_doc_bytes)
    master_doc_hash = hashlib.sha256(master_doc_bytes).hexdigest()

    # 3. Create Release with Broadcast Encryption
    release_manager = ReleaseManager(registry=registry)
    release = release_manager.create_release(
        document_bytes=master_doc_bytes,
        document_name="classified_flight_logs.png",
        issuer_id="iss_hq",
        recipient_ids=[alice.recipient_id],
    )
    alice_package = release.packages[alice.recipient_id]


    # 4. Controlled Viewer Session Ingest
    session, open_receipt, open_block = viewer.open_session_from_package(
        package=alice_package,
        recipient=alice,
        device_key_id="dev_alice_workstation_airgap",
        expires_in_seconds=7200
    )
    assert session.is_active is True
    assert open_receipt.recipient_id == alice.recipient_id
    assert open_block is not None

    # 5. In-Memory Controlled View
    view_result = viewer.render_view(session.session_id)
    assert view_result["status"] == "RENDERED_CONTROLLED"

    # 6. Controlled Export with Dynamic Watermarking & DLT Commitment
    exported_bytes, child_copy, exp_event, edge, exp_receipt, exp_block = viewer.controlled_export_with_dlt(
        session_id=session.session_id,
        export_format=ExportFormat.IMAGE,
        recipient=alice,
        device_id="dev_alice_workstation_airgap"
    )

    assert child_copy.lineage_depth == 1
    assert exp_receipt.recipient_signature_b64 != ""
    assert exp_block is not None
    assert exp_block.header.block_height == 2

    # Verify replication across all 3 offline nodes
    for nid, node in dlt_ledger.nodes.items():
        assert node.get_tip_height() == 2
        assert node.get_receipt(exp_receipt.receipt_id) is not None

    # 7. Forensic Extraction & Attribution from Leaked Artifact
    extractor = DynamicForensicExtractor(
        dlt_ledger=dlt_ledger,
        lineage_storage=storage,
        wm_engine=wm_engine
    )

    result = extractor.analyze_leak(
        leak_artifact=exported_bytes,
        expected_doc_id=alice_package.document_id,
        expected_release_id="export_boundary",
        reference_clean_image=anchored_base
    )

    assert result.status == ForensicVerificationStatus.PROVEN_AUTHENTIC
    assert result.attributed_recipient_id == alice.recipient_id
    assert result.watermark_recovered is True
    assert result.recipient_signature_verified is True
    assert result.quorum_verified is True
    assert result.merkle_verified is True
    assert result.lineage_depth == 1
    assert len(result.lineage_path) >= 1
    assert "PROVED: This exact recipient performed this signed decryption event" in result.honesty_declaration
    assert "NOT AUTOMATICALLY PROVED: This human personally leaked the file downstream" in result.honesty_declaration
    assert result.visual_metrics is not None
    assert result.visual_metrics["ssim"] >= 0.75
    assert result.visual_metrics["psnr_db"] >= 28.0


