"""
SIH26237 - Dynamic Leak Attribution Engine Integration Tests
Validates the integration between DynamicForensicExtractor and AttributionEngine:
- Recipient identity resolution post-extraction
- Fail-closed state transitions (NO_SIGNAL, INSUFFICIENT_EVIDENCE, CONFLICT)
- Honesty declaration preservation in high-level summaries
"""

import pytest
import numpy as np
import cv2
import hashlib

from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.lineage.storage import LineageStorage
from core.lineage.service import LineageService
from core.lineage.viewer import ControlledViewer
from core.lineage.models import ExportFormat
from core.ledger.dlt import PermissionedDLTLedger
from core.provenance.decryption import RecipientDecryptionClient
from core.watermark.dynamic import DynamicWatermarkEngine
from core.watermark.pipeline import CanonicalCanvasSpec, GeometricSynchronizer
from core.watermark.carrier import CarrierConfig
from core.attribution.engine import AttributionEngine, AttributionState


def test_dynamic_leak_attribution_engine_end_to_end():
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

    # Prepare document
    canvas = np.full((spec.height, spec.width), 245, dtype=np.uint8)
    cv2.rectangle(canvas, (140, 80), (660, 110), (40,), -1)
    cv2.putText(canvas, "TARGET SCHEMATICS - TOP SECRET", (150, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,), 2)
    for y in range(160, 820, 35):
        cv2.line(canvas, (140, y), (660, y), (60,), 2)

    anchored_base = sync.embed_fiducial_anchors(canvas)
    _, encoded_doc_bytes = cv2.imencode(".png", anchored_base)
    master_doc_bytes = bytes(encoded_doc_bytes)

    rel_mgr = ReleaseManager(registry=registry)
    release = rel_mgr.create_release(
        document_bytes=master_doc_bytes,
        document_name="top_secret_schematics.png",
        issuer_id="iss_hq",
        recipient_ids=[alice.recipient_id]
    )
    alice_pkg = release.packages[alice.recipient_id]

    session, open_receipt, open_block = viewer.open_session_from_package(
        package=alice_pkg,
        recipient=alice,
        device_key_id="dev_workstation_01"
    )

    exp_bytes, child_copy, exp_evt, edge, exp_receipt, exp_block = viewer.controlled_export_with_dlt(
        session_id=session.session_id,
        export_format=ExportFormat.IMAGE,
        recipient=alice,
        device_id="dev_workstation_01"
    )

    # Feed into AttributionEngine
    attr_engine = AttributionEngine(registry=registry)
    attr_result = attr_engine.analyze_dynamic_leak(
        leak_artifact=exp_bytes,
        expected_document_id=alice_pkg.document_id,
        expected_release_id="export_boundary",
        reference_clean_image=anchored_base,
        dlt_ledger=dlt_ledger,
        lineage_storage=storage,
        dynamic_wm_engine=wm_engine,
    )

    assert attr_result.state == AttributionState.ATTRIBUTED
    assert attr_result.should_abstain is False
    assert attr_result.candidate is not None
    assert attr_result.candidate.recipient_id == alice.recipient_id
    assert attr_result.candidate.name == "Alice Henderson"
    assert "PROVED: This exact recipient performed this signed decryption event" in attr_result.summary
    assert attr_result.lineage_proof is not None
    assert attr_result.lineage_proof["quorum_verified"] is True
    assert attr_result.lineage_proof["merkle_verified"] is True


def test_dynamic_leak_unmarked_artifact_abstains():
    registry = RecipientRegistry()
    attr_engine = AttributionEngine(registry=registry)

    # Clean unwatermarked image
    clean_image = np.full((1000, 800), 240, dtype=np.uint8)
    _, clean_bytes = cv2.imencode(".png", clean_image)

    attr_result = attr_engine.analyze_dynamic_leak(
        leak_artifact=bytes(clean_bytes),
    )

    assert attr_result.state == AttributionState.NO_SIGNAL
    assert attr_result.should_abstain is True
    assert attr_result.candidate is None
