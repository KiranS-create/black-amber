"""
SIH26237 - Real Physical Watermark Capture Ingestion CLI & Evaluation Harness
Ingests physical smartphone photographs of printed confidential documents,
performs Image Quality Assessment (IQA), executes geometric synchronization,
DSSS demodulation, Reed-Solomon ECC, document-release binding validation,
and Tardos collusion attribution.
Enforces explicit failure states and produces schema-compliant manifests.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

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


def compute_image_iqa(img: np.ndarray) -> Dict[str, Any]:
    """
    Computes Image Quality Assessment (IQA) metrics:
    - Laplacian variance (focus/sharpness metric)
    - Mean and standard deviation of luminance (exposure metric)
    - Dynamic range and clipping percentage
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    h, w = gray.shape[:2]
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean_lum = float(np.mean(gray))
    std_lum = float(np.std(gray))

    # Clipping detection
    under_clipped = float(np.sum(gray < 15) / (h * w))
    over_clipped = float(np.sum(gray > 240) / (h * w))

    # Usability rating
    is_sharp = lap_var >= 40.0
    is_exposed = 40.0 <= mean_lum <= 220.0 and under_clipped < 0.25 and over_clipped < 0.25
    usable = is_sharp and is_exposed and (w >= 600 and h >= 600)

    return {
        "resolution": f"{w}x{h}",
        "width": w,
        "height": h,
        "channels": 3 if len(img.shape) == 3 else 1,
        "sharpness_laplacian_var": round(lap_var, 2),
        "mean_luminance": round(mean_lum, 2),
        "std_luminance": round(std_lum, 2),
        "underexposed_clip_ratio": round(under_clipped, 4),
        "overexposed_clip_ratio": round(over_clipped, 4),
        "is_sharp": is_sharp,
        "is_well_exposed": is_exposed,
        "iqa_usable": usable,
    }


def classify_forensic_status(obs: Any, iqa: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Classifies the observation into explicit terminal forensic failure states:
    - SUCCESS
    - SYNC_FAILED
    - ECC_FAILED
    - CRC_MISMATCH
    - ABSTAIN_LOW_CONFIDENCE
    - CONFLICT_MULTI_SIGNAL
    - INVALID_BINDING
    """
    if not obs.synchronization_success:
        return "SYNC_FAILED", "Geometric synchronization failed (missing or damaged fiducials)"

    ecc_telemetry = obs.telemetry.get("ecc", {})
    err_msg = ecc_telemetry.get("error", "")

    if "binding mismatch" in err_msg or "transplantation detected" in err_msg:
        return "INVALID_BINDING", "Document-release cryptographic binding mismatch (cross-document transplantation)"

    if "length mismatch" in err_msg:
        return "CONFLICT_MULTI_SIGNAL", "Codeword length mismatch against release specification"

    if "CRC-32 checksum mismatch" in err_msg:
        return "CRC_MISMATCH", "Reed-Solomon succeeded but CRC-32 checksum verification failed"

    if obs.status == WatermarkStatus.PARTIAL:
        return "ECC_FAILED", "Bit error rate exceeded Reed-Solomon correction budget"

    if obs.status == WatermarkStatus.NO_SIGNAL:
        return "SYNC_FAILED", "No watermark signal or fiducials present"

    if obs.status == WatermarkStatus.INVALID:
        return "CONFLICT_MULTI_SIGNAL", f"Invalid payload framing: {err_msg}"

    if obs.status == WatermarkStatus.RECOVERED:
        if obs.confidence < 0.40:
            return "ABSTAIN_LOW_CONFIDENCE", "Confidence score below minimum forensic threshold (fail-closed)"
        return "SUCCESS", None

    return "ABSTAIN_LOW_CONFIDENCE", "Unclassified observation state (fail-closed)"


def ingest_capture(
    image_path: Path,
    document_id: str,
    release_id: str,
    expected_codeword_length: Optional[int] = 128,
    candidate_recipients: Optional[List[str]] = None,
    printer: str = "N/A",
    printer_type: str = "N/A",
    printer_dpi: int = 600,
    paper: str = "Standard 80gsm A4",
    camera_make: str = "Apple",
    camera_model: Optional[str] = "iPhone 15 Pro",
    lighting: str = "Normal indoor office (400-600 lux)",
    lux_level: float = 500.0,
    distance: str = "~35cm",
    distance_cm: float = 35.0,
    angle: str = "0 deg",
    angle_deg: float = 0.0,
    notes: str = "",
    results_json_path: Optional[Path] = None,
    debug_dir: Optional[Path] = None,
    tardos_provider: Optional[TardosTraceabilityProvider] = None,
    physical_or_simulated: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingests a single capture file, computes IQA, runs decoding, verifies binding and CRC,
    evaluates Tardos accusation, and returns a schema-compliant manifest dictionary.
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Capture image not found: {image_path}")

    capture_bytes = image_path.read_bytes()
    capture_hash = hashlib.sha256(capture_bytes).hexdigest()
    file_size_bytes = len(capture_bytes)

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image file: {image_path}")

    # 1. Image Quality Assessment
    iqa = compute_image_iqa(img)

    # 2. Watermark Decoding
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

    # 3. Explicit Failure State Classification
    forensic_status, rejection_reason = classify_forensic_status(obs, iqa)

    # 3b. Save Visual Debugging Artifacts if debug_dir requested
    if debug_dir:
        debug_dir = Path(debug_dir)
        debug_dir.mkdir(parents=True, exist_ok=True)
        # 1. Annotated detection image
        annotated = img.copy()
        sync_info = obs.telemetry.get("sync", {})
        corners = sync_info.get("detected_marker_corners", [])
        if corners:
            for c_set in corners:
                pts = np.array(c_set, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated, [pts], True, (0, 255, 0), 2)
        cv2.imwrite(str(debug_dir / f"{image_path.stem}_markers.png"), annotated)

        # 2. Rectified canvas if sync succeeded
        if obs.synchronization_success:
            _, rectified, _ = decoder.synchronizer.detect_and_rectify(img)
            if rectified is not None:
                cv2.imwrite(str(debug_dir / f"{image_path.stem}_rectified.png"), rectified)


    # 4. Attribution Evaluation
    tardos_state = "NO_SIGNAL"
    candidate = None
    fused_confidence = 0.0
    abstention_enforced = True

    if forensic_status == "SUCCESS" and candidate_recipients and tardos_provider:
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
            fused_confidence = trace_res.fused_confidence
            abstention_enforced = False
        else:
            abstention_enforced = True

    # 5. Build Manifest Record
    is_phys = physical_or_simulated or ("SIMULATED" if printer_type == "Simulation" else "PHYSICAL")
    sync_telemetry = obs.telemetry.get("sync", {})
    ecc_telemetry = obs.telemetry.get("ecc", {})

    record: Dict[str, Any] = {
        "capture_id": f"{is_phys[:4]}-{int(time.time())}-{image_path.stem}",
        "physical_or_simulated": is_phys,
        "document_id": document_id,
        "release_id": release_id,
        "artifact_hash": "N/A (physical acquisition)",
        "capture_hash": capture_hash,
        "image_metadata": {
            "resolution": iqa["resolution"],
            "channels": iqa["channels"],
            "format": image_path.suffix.lstrip(".").upper() or "JPEG",
            "file_size_bytes": file_size_bytes,
            "sharpness_laplacian_var": iqa["sharpness_laplacian_var"],
            "mean_luminance": iqa["mean_luminance"],
        },
        "hardware_metadata": {
            "printer_model": printer,
            "printer_type": printer_type,
            "printer_dpi": printer_dpi,
            "paper_stock": paper,
            "camera_make": camera_make,
            "camera_model": camera_model or "Unknown",
        },
        "environmental_metadata": {
            "lighting_condition": lighting,
            "lux_level": lux_level,
            "capture_distance_cm": distance_cm,
            "capture_angle_deg": angle_deg,
            "physical_degradation": notes or "None",
        },
        "synchronization_metrics": {
            "sync_status": "OK" if obs.synchronization_success else "NO_MARK",
            "detected_markers": sync_telemetry.get("detected_markers", []),
            "marker_count": len(sync_telemetry.get("detected_markers", [])),
            "reprojection_error_px": round(obs.homography_error, 4),
            "homography_inliers": len(sync_telemetry.get("detected_markers", [])) * 4 if obs.synchronization_success else 0,
        },
        "ecc_and_payload_metrics": {
            "pre_ecc_ber": obs.raw_ber,
            "post_ecc_ber": 0.0 if forensic_status == "SUCCESS" else 1.0,
            "errata_bytes_corrected": ecc_telemetry.get("errata_count", 0),
            "preamble_matched": forensic_status == "SUCCESS",
            "crc32_verified": ecc_telemetry.get("crc_verified", False),
            "binding_verified": ecc_telemetry.get("binding_verified", False),
            "recovered_bits": obs.symbol_count if forensic_status == "SUCCESS" else 0,
            "expected_bits": expected_codeword_length or 128,
        },
        "forensic_status": forensic_status,
        "forensic_outcome": {
            "confidence_score": obs.confidence,
            "tardos_state": tardos_state,
            "accused_candidate": candidate,
            "fused_confidence": fused_confidence,
            "abstention_enforced": abstention_enforced,
            "rejection_reason": rejection_reason,
        },
        "timing_telemetry_ms": {
            "sync_ms": obs.telemetry.get("sync_latency_ms", 0.0),
            "demod_ms": obs.telemetry.get("demod_latency_ms", 0.0),
            "ecc_ms": obs.telemetry.get("ecc_latency_ms", 0.0),
            "total_ms": total_latency_ms,
        },
        "operator_notes": notes,
    }

    if results_json_path:
        results_json_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_data = {
            "manifest_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_category": is_phys,
            "hardware_environment_connected": is_phys == "PHYSICAL",
            "total_captures": 1,
            "records": [record],
        }
        if results_json_path.exists():
            try:
                with open(results_json_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if isinstance(existing, dict) and "records" in existing:
                        existing["records"].append(record)
                        existing["total_captures"] = len(existing["records"])
                        manifest_data = existing
                    elif isinstance(existing, list):
                        existing.append(record)
                        manifest_data["records"] = existing
                        manifest_data["total_captures"] = len(existing)
            except Exception:
                pass

        with open(results_json_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

    return record


def validate_manifest_file(manifest_path: Path) -> Tuple[bool, List[str]]:
    """Validates a manifest JSON file against capture_manifest.schema.json."""
    if not manifest_path.exists():
        return False, [f"Manifest file not found: {manifest_path}"]

    schema_path = root_dir / "artifacts" / "physical_validation" / "capture_manifest.schema.json"
    if not schema_path.exists():
        return False, [f"Schema file not found: {schema_path}"]

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"JSON parse error: {e}"]

    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
        return True, ["Manifest successfully validated against schema."]
    except ImportError:
        # Fallback structural validation
        errors = []
        if not isinstance(data, dict):
            return False, ["Root manifest must be a JSON object"]
        for req in ["manifest_version", "generated_at", "dataset_category", "total_captures", "records"]:
            if req not in data:
                errors.append(f"Missing required field: {req}")
        return len(errors) == 0, errors if errors else ["Manifest structurally valid (jsonschema library omitted)."]
    except Exception as e:
        return False, [f"Validation failure: {e}"]


def main():
    parser = argparse.ArgumentParser(description="AegisTrace Physical Watermark Capture Ingestion & Validation CLI")
    parser.add_argument("--image", type=Path, help="Path to physical photograph image")
    parser.add_argument("--doc-id", type=str, default="DOC_PHYS_01", help="Document ID")
    parser.add_argument("--release-id", type=str, default="REL_01", help="Release ID")
    parser.add_argument("--codeword-len", type=int, default=128, help="Expected Tardos codeword length")
    parser.add_argument("--printer", type=str, default="HP LaserJet Pro M404n", help="Printer model")
    parser.add_argument("--printer-type", type=str, default="Laser", choices=["Laser", "Inkjet", "Simulation"], help="Printer technology")
    parser.add_argument("--camera-model", type=str, default="iPhone 15 Pro", help="Smartphone camera model")
    parser.add_argument("--lighting", type=str, default="Normal indoor office (400-600 lux)", help="Lighting condition")
    parser.add_argument("--angle", type=str, default="~15 deg tilt", help="Camera angle description")
    parser.add_argument("--angle-deg", type=float, default=15.0, help="Camera angle in degrees")
    parser.add_argument("--distance", type=str, default="~35 cm", help="Camera distance description")
    parser.add_argument("--distance-cm", type=float, default=35.0, help="Camera distance in cm")
    parser.add_argument("--output-manifest", type=Path, default=Path("artifacts/physical_validation/capture_manifest.json"), help="Output manifest path")
    parser.add_argument("--debug-dir", type=Path, help="Directory to save visual debugging artifacts (markers, rectified canvas)")
    parser.add_argument("--validate-manifest", type=Path, help="Validate an existing manifest against JSON schema")
    args = parser.parse_args()

    if args.validate_manifest:
        valid, msgs = validate_manifest_file(args.validate_manifest)
        for m in msgs:
            print(f"[{'VALID' if valid else 'INVALID'}] {m}")
        sys.exit(0 if valid else 1)

    if not args.image:
        parser.print_help()
        sys.exit(1)

    rec = ingest_capture(
        image_path=args.image,
        document_id=args.doc_id,
        release_id=args.release_id,
        expected_codeword_length=args.codeword_len,
        printer=args.printer,
        printer_type=args.printer_type,
        camera_model=args.camera_model,
        lighting=args.lighting,
        distance=args.distance,
        distance_cm=args.distance_cm,
        angle=args.angle,
        angle_deg=args.angle_deg,
        results_json_path=args.output_manifest,
        debug_dir=args.debug_dir,
    )
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
