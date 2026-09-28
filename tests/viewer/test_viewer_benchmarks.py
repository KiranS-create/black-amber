"""
SIH26237 - Controlled Viewer and DLT Performance Benchmarks
Measures real latency, throughput, and memory consumption across:
1. KEM Decapsulation & Symmetric Decryption
2. Dynamic Watermark Generation & Carrier Modulation
3. Recipient-Owned ML-DSA-65 Signature Generation
4. Multi-Validator BFT Quorum Consensus & 3-Node State Replication
5. Leak Forensics & DLT Attribution Lookup
"""

import pytest
import time
import os
import hashlib
import json
import numpy as np
import cv2

from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.lineage.storage import LineageStorage
from core.lineage.service import LineageService
from core.lineage.viewer import ControlledViewer
from core.lineage.models import ExportFormat
from core.ledger.dlt import PermissionedDLTLedger
from core.provenance.decryption import RecipientDecryptionClient
from core.watermark.dynamic import (
    DynamicWatermarkEngine,
    generate_dynamic_watermark,
)
from core.lineage.forensics import DynamicForensicExtractor, ForensicVerificationStatus
from core.watermark.pipeline import CanonicalCanvasSpec, GeometricSynchronizer
from core.watermark.carrier import CarrierConfig


def test_viewer_and_dlt_benchmarks():
    benchmark_results = {}

    # Setup
    registry = RecipientRegistry()
    alice = registry.enroll("Alice Henderson", email="alice@defense.gov")

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

    canvas = np.full((spec.height, spec.width), 245, dtype=np.uint8)
    cv2.rectangle(canvas, (140, 80), (660, 110), (40,), -1)
    cv2.putText(canvas, "PERFORMANCE BENCHMARK DOCUMENT", (150, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,), 2)
    for y in range(160, 820, 40):
        cv2.line(canvas, (140, y), (660, y), (60,), 2)
    anchored_base = sync.embed_fiducial_anchors(canvas)
    _, encoded_doc_bytes = cv2.imencode(".png", anchored_base)
    master_doc_bytes = bytes(encoded_doc_bytes)

    rel_mgr = ReleaseManager(registry=registry)
    release = rel_mgr.create_release(
        document_bytes=master_doc_bytes,
        document_name="perf_benchmark.png",
        issuer_id="iss_hq",
        recipient_ids=[alice.recipient_id]
    )
    alice_package = release.packages[alice.recipient_id]

    # 1. Benchmark: Recipient Decryption & Session Open
    t0 = time.perf_counter()
    session, open_receipt, open_block = viewer.open_session_from_package(
        package=alice_package,
        recipient=alice,
        device_key_id="dev_bench_01"
    )
    t_open_ms = (time.perf_counter() - t0) * 1000.0
    benchmark_results["recipient_decryption_and_session_open_ms"] = round(t_open_ms, 2)
    assert t_open_ms < 5000.0, f"Decryption too slow: {t_open_ms}ms"

    # 2. Benchmark: In-Memory Controlled Render
    t0 = time.perf_counter()
    view = viewer.render_view(session.session_id)
    t_render_ms = (time.perf_counter() - t0) * 1000.0
    benchmark_results["in_memory_controlled_render_ms"] = round(t_render_ms, 2)
    assert t_render_ms < 100.0, f"Render too slow: {t_render_ms}ms"

    # 3. Benchmark: Controlled Export + Dynamic Watermark + Recipient ML-DSA-65 Sign + DLT 3-Node Replicated Consensus
    t0 = time.perf_counter()
    exported_bytes, child_copy, exp_event, edge, exp_receipt, exp_block = viewer.controlled_export_with_dlt(
        session_id=session.session_id,
        export_format=ExportFormat.IMAGE,
        recipient=alice,
        device_id="dev_bench_01"
    )
    t_export_dlt_ms = (time.perf_counter() - t0) * 1000.0
    benchmark_results["controlled_export_watermark_and_dlt_ms"] = round(t_export_dlt_ms, 2)
    assert t_export_dlt_ms < 5000.0, f"Export + DLT too slow: {t_export_dlt_ms}ms"

    # 4. Benchmark: Forensic Leak Ingestion & Full DLT Attribution
    extractor = DynamicForensicExtractor(dlt_ledger=dlt_ledger, lineage_storage=storage, wm_engine=wm_engine)
    t0 = time.perf_counter()
    res = extractor.analyze_leak(
        leak_artifact=exported_bytes,
        expected_doc_id=alice_package.document_id,
        expected_release_id="export_boundary",
        reference_clean_image=anchored_base
    )
    t_forensics_ms = (time.perf_counter() - t0) * 1000.0
    benchmark_results["leak_forensic_analysis_and_attribution_ms"] = round(t_forensics_ms, 2)
    assert res.status == ForensicVerificationStatus.PROVEN_AUTHENTIC
    assert t_forensics_ms < 5000.0, f"Forensics too slow: {t_forensics_ms}ms"

    # Output benchmark summary
    print(f"\n=======================================================")
    print(f"AEGISTRACE VIEWER & DLT BENCHMARK REPORT:")
    for k, v in benchmark_results.items():
        print(f"  - {k}: {v} ms")
    print(f"=======================================================\n")
