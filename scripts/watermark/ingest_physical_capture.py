"""
SIH26237 - Real Physical Watermark Capture Ingestion CLI & Evaluation Harness
Ingests physical smartphone photographs of printed confidential documents,
records hardware & lighting metadata, runs synchronization, demodulation, RS-ECC,
and Tardos attribution, appending structured records to artifacts/watermark/physical_results.json.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import cv2
import numpy as np

from core.watermark import (
    PrintCameraWatermarkDecoder,
    WatermarkTraceabilityAdapter,
    WatermarkStatus,
    CanonicalCanvasSpec,
    CarrierConfig,
    PhysicalExperimentRecord,
)
from core.traceability import TardosTraceabilityProvider


def compute_file_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def ingest_capture(
    image_path: Path,
    document_id: str,
    release_id: str,
    expected_codeword_length: Optional[int] = None,
    candidate_recipients: Optional[List[str]] = None,
    printer: str = "N/A",
    printer_type: str = "N/A",
    paper: str = "Standard 80gsm A4",
    camera: str = "Smartphone Camera",
    camera_model: Optional[str] = None,
    lighting: str = "Normal indoor",
    distance: str = "~30cm",
    angle: str = "0 deg",
    notes: str = "",
    results_json_path: Optional[Path] = None,
    tardos_provider: Optional[TardosTraceabilityProvider] = None,
) -> PhysicalExperimentRecord:
    """
    Ingests a single physical or simulated capture file, executes decoding and attribution,
    and returns a structured PhysicalExperimentRecord.
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Capture image not found: {image_path}")

    capture_bytes = image_path.read_bytes()
    capture_hash = hashlib.sha256(capture_bytes).hexdigest()

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image file: {image_path}")

    h_img, w_img = img.shape[:2]
    img_res = f"{w_img}x{h_img}"

    decoder = PrintCameraWatermarkDecoder()
    t_start = time.perf_counter()
    obs = decoder.decode(
        img,
        expected_document_id=document_id,
        expected_release_id=release_id,
        expected_codeword_length=expected_codeword_length,
        codeword_length_hint=expected_codeword_length or 128,
    )
    t_end = time.perf_counter()
    total_latency_ms = round((t_end - t_start) * 1000.0, 2)

    # Attribution evaluation if candidates provided
    tardos_state = "NO_SIGNAL"
    candidate = None
    if candidate_recipients and tardos_provider and obs.status in (WatermarkStatus.RECOVERED, WatermarkStatus.PARTIAL):
        adapter = WatermarkTraceabilityAdapter(tardos_provider)
        trace_res = adapter.evaluate_observation(
            observation=obs,
            all_recipient_ids=candidate_recipients,
            document_id=document_id,
            release_id=release_id,
        )
        tardos_state = trace_res.attribution_status.value
        if trace_res.accused_recipients:
            candidate = trace_res.accused_recipients[0]

    record = PhysicalExperimentRecord(
        test_id=f"PHYS-{int(time.time())}-{image_path.stem}",
        physical_or_simulated="PHYSICAL" if printer_type != "Simulation" else "SIMULATED",
        printer=printer,
        printer_type=printer_type,
        paper=paper,
        camera=camera,
        camera_model_if_known=camera_model,
        lighting=lighting,
        distance=distance,
        angle=angle,
        document_id=document_id,
        release_id=release_id,
        artifact_hash="N/A (external physical)",
        capture_hash=capture_hash,
        image_resolution=img_res,
        sync_status="OK" if obs.synchronization_success else ("NO_MARK" if obs.status == WatermarkStatus.NO_SIGNAL else "FAILED"),
        marker_count=len(obs.telemetry.get("sync", {}).get("detected_markers", [])),
        reprojection_error=round(obs.homography_error, 4),
        pre_ecc_ber=obs.raw_ber,
        post_ecc_ber=0.0 if obs.status == WatermarkStatus.RECOVERED else 1.0,
        ecc_corrected=obs.telemetry.get("ecc", {}).get("errata_count", 0),
        watermark_status=obs.status.value,
        recovered_bits=obs.symbol_count if obs.status == WatermarkStatus.RECOVERED else 0,
        expected_bits=expected_codeword_length or 128,
        tardos_state=tardos_state,
        candidate=candidate,
        abstention=obs.status in (WatermarkStatus.NO_SIGNAL, WatermarkStatus.INVALID),
        sync_latency_ms=obs.telemetry.get("sync_latency_ms", 0.0),
        demod_latency_ms=obs.telemetry.get("demod_latency_ms", 0.0),
        ecc_latency_ms=obs.telemetry.get("ecc_latency_ms", 0.0),
        total_latency_ms=total_latency_ms,
        notes=notes,
        telemetry=obs.telemetry,
    )

    if results_json_path:
        results_json_path.parent.mkdir(parents=True, exist_ok=True)
        existing_data = []
        if results_json_path.exists():
            try:
                with open(results_json_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception:
                existing_data = []
        existing_data.append(record.model_dump())
        with open(results_json_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2)

    return record


def main():
    parser = argparse.ArgumentParser(description="SIH26237 Physical Watermark Capture Ingestion CLI")
    parser.add_argument("--image", required=True, type=Path, help="Path to physical photograph image")
    parser.add_argument("--doc-id", required=True, type=str, help="Document ID")
    parser.add_argument("--release-id", required=True, type=str, help="Release ID")
    parser.add_argument("--codeword-len", type=int, default=128, help="Expected Tardos codeword length")
    parser.add_argument("--printer", type=str, default="HP LaserJet Pro M404n", help="Printer model")
    parser.add_argument("--printer-type", type=str, default="Laser", choices=["Laser", "Inkjet", "Simulation"], help="Printer technology")
    parser.add_argument("--camera-model", type=str, default="iPhone 15 Pro", help="Smartphone camera model")
    parser.add_argument("--lighting", type=str, default="Normal indoor office (400 lux)", help="Lighting condition")
    parser.add_argument("--angle", type=str, default="~15 deg tilt", help="Camera angle/skew")
    parser.add_argument("--distance", type=str, default="~35 cm", help="Camera distance")
    parser.add_argument("--output-json", type=Path, default=Path("artifacts/watermark/physical_results.json"), help="Output JSON path")
    args = parser.parse_args()

    record = ingest_capture(
        image_path=args.image,
        document_id=args.doc_id,
        release_id=args.release_id,
        expected_codeword_length=args.codeword_len,
        printer=args.printer,
        printer_type=args.printer_type,
        camera_model=args.camera_model,
        lighting=args.lighting,
        distance=args.distance,
        angle=args.angle,
        results_json_path=args.output_json,
    )
    print(json.dumps(record.model_dump(), indent=2))


if __name__ == "__main__":
    main()
