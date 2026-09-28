"""
SIH26237 - Controlled Viewer and DLT Performance Benchmarking Script
Executes standalone latency, throughput, and cryptographic benchmarks for:
- ML-KEM-768 Decapsulation & AES-256-GCM Decryption
- Dynamic Watermark Token, Commitment & Codeword Derivation
- Direct Sequence Spread Spectrum (DSSS) Modulation
- Recipient-Owned ML-DSA-65 Signature Generation
- 3-Validator BFT Quorum Consensus & 3-Node Offline Ledger Replication
- Forensic Leak Ingestion, Watermark Decoding & DLT Attribution Lookup
"""

import time
import os
import sys
import json
import hashlib
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.recipient import RecipientRegistry
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
from core.attribution.engine import AttributionEngine, AttributionState


def run_benchmark(num_iterations: int = 5):
    print("=" * 70)
    print("AEGISTRACE CONTROLLED VIEWER + DLT BENCHMARK HARNESS")
    print(f"Iterations: {num_iterations}")
    print("=" * 70)

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
    cv2.putText(canvas, "STANDALONE BENCHMARK DOCUMENT", (150, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,), 2)
    for y in range(160, 820, 35):
        cv2.line(canvas, (140, y), (660, y), (60,), 2)
    anchored_base = sync.embed_fiducial_anchors(canvas)
    _, encoded_doc_bytes = cv2.imencode(".png", anchored_base)
    master_doc_bytes = bytes(encoded_doc_bytes)

    rel_mgr = ReleaseManager(registry=registry)
    release = rel_mgr.create_release(
        document_bytes=master_doc_bytes,
        document_name="perf_bench.png",
        issuer_id="iss_hq",
        recipient_ids=[alice.recipient_id]
    )
    alice_package = release.packages[alice.recipient_id]

    latencies = {
        "session_open_decrypt_ms": [],
        "in_memory_render_ms": [],
        "export_watermark_dlt_ms": [],
        "leak_forensics_attribution_ms": [],
    }

    for i in range(num_iterations):
        print(f"Running iteration {i+1}/{num_iterations}...", end="", flush=True)

        # 1. Session Open & Decrypt
        t0 = time.perf_counter()
        session, open_receipt, open_block = viewer.open_session_from_package(
            package=alice_package,
            recipient=alice,
            device_key_id=f"dev_bench_{i}"
        )
        latencies["session_open_decrypt_ms"].append((time.perf_counter() - t0) * 1000.0)

        # 2. Render
        t0 = time.perf_counter()
        viewer.render_view(session.session_id)
        latencies["in_memory_render_ms"].append((time.perf_counter() - t0) * 1000.0)

        # 3. Export + Watermark + ML-DSA-65 Sign + DLT Commit
        t0 = time.perf_counter()
        exp_bytes, child_copy, exp_event, edge, exp_receipt, exp_block = viewer.controlled_export_with_dlt(
            session_id=session.session_id,
            export_format=ExportFormat.IMAGE,
            recipient=alice,
            device_id=f"dev_bench_{i}"
        )
        latencies["export_watermark_dlt_ms"].append((time.perf_counter() - t0) * 1000.0)

        # 4. Forensic Extraction & Attribution
        extractor = DynamicForensicExtractor(dlt_ledger=dlt_ledger, lineage_storage=storage, wm_engine=wm_engine)
        t0 = time.perf_counter()
        res = extractor.analyze_leak(
            leak_artifact=exp_bytes,
            expected_doc_id=alice_package.document_id,
            expected_release_id="export_boundary",
            reference_clean_image=anchored_base
        )
        latencies["leak_forensics_attribution_ms"].append((time.perf_counter() - t0) * 1000.0)
        assert res.status == ForensicVerificationStatus.PROVEN_AUTHENTIC
        print(" done.")

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "iterations": num_iterations,
        "metrics": {}
    }

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY RESULTS (Mean / Median / Min / Max):")
    print("=" * 70)
    for k, v in latencies.items():
        mean_val = float(np.mean(v))
        med_val = float(np.median(v))
        min_val = float(np.min(v))
        max_val = float(np.max(v))
        summary["metrics"][k] = {
            "mean_ms": round(mean_val, 2),
            "median_ms": round(med_val, 2),
            "min_ms": round(min_val, 2),
            "max_ms": round(max_val, 2),
        }
        print(f"  {k:<35}: {mean_val:8.2f} ms (med: {med_val:8.2f}, min: {min_val:8.2f}, max: {max_val:8.2f})")
    print("=" * 70)

    out_dir = os.path.join("artifacts", "performance")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "viewer_pipeline_benchmark.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Benchmark results saved to: {out_file}\n")


if __name__ == "__main__":
    run_benchmark(num_iterations=3)
