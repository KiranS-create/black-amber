import os
import sys
import json
import time
from typing import Dict, Any

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.digital.image_attacks import (
    JpegRecompressionAttack,
    ResizeAttack,
    CropAttack,
    PerspectiveTransformAttack,
    GaussianBlurAttack,
    GaussianNoiseAttack,
)
from attacks.digital.document_attacks import (
    PdfRewriteAttack,
    PdfRasterizationAttack,
    PdfMetadataRemovalAttack,
    PdfTextExtractionRegenerationAttack,
)
from attacks.physical.simulation import PrintCameraSimulationAttack
from attacks.measurement.evaluator import RobustnessEvaluator, BenchmarkTiming

def run_benchmarks():
    print("=== RUNNING SIH26237 ATTACK LAB BENCHMARKS & MATRIX GENERATION ===")
    artifacts_dir = os.path.abspath("artifacts/attacks")
    os.makedirs(artifacts_dir, exist_ok=True)
    evaluator = RobustnessEvaluator(artifacts_dir=artifacts_dir)

    # 1. Generate test documents
    print("[*] Generating baseline deterministic test corpus...")
    hires_img = BaselineTestCorpus.generate_high_res_page_image()
    text_pdf = BaselineTestCorpus.generate_simple_text_pdf()
    multipage_pdf = BaselineTestCorpus.generate_multipage_pdf()
    carrier_pdf, marker = BaselineTestCorpus.generate_synthetic_carrier_fixture()

    print(f"    - Baseline High-Res Image: {len(hires_img)} bytes")
    print(f"    - Baseline Text PDF: {len(text_pdf)} bytes")
    print(f"    - Baseline Multi-page PDF: {len(multipage_pdf)} bytes")
    print(f"    - Baseline Carrier PDF: {len(carrier_pdf)} bytes")

    # 2. Timing benchmarks for representative attacks
    print("\n[*] Measuring performance timings (mean, median, P95, sizes)...")
    attacks_to_benchmark = [
        (JpegRecompressionAttack(), hires_img, {"quality": 75}, "JPEG Recompression (Q=75)"),
        (ResizeAttack(), hires_img, {"scale_factor": 0.5}, "Resize (50%)"),
        (CropAttack(), hires_img, {"crop_fraction": 0.1}, "Crop (10%)"),
        (PerspectiveTransformAttack(), hires_img, {"distortion_scale": 0.05}, "Perspective Transform (s=0.05)"),
        (PdfRewriteAttack(), text_pdf, {}, "PDF Rewrite (Decompress/Re-serialize)"),
        (PdfRasterizationAttack(), text_pdf, {"dpi": 150}, "PDF Rasterization (150 DPI)"),
        (PrintCameraSimulationAttack(), hires_img, {}, "Print-Camera Simulation (Level 2)"),
    ]

    benchmark_results = []
    for atk, data, params, label in attacks_to_benchmark:
        timing = evaluator.benchmark_attack(atk, data, parameters=params, iterations=10, seed=42)
        print(f"    - {label:<35} | Mean: {timing.mean_ms:>6.2f} ms | Median: {timing.median_ms:>6.2f} ms | P95: {timing.p95_ms:>6.2f} ms | In: {timing.input_size_bytes} B | Out: {timing.output_size_bytes} B")
        benchmark_results.append({
            "attack_name": atk.ATTACK_NAME,
            "label": label,
            "samples": timing.samples,
            "mean_ms": timing.mean_ms,
            "median_ms": timing.median_ms,
            "p95_ms": timing.p95_ms,
            "input_size_bytes": timing.input_size_bytes,
            "output_size_bytes": timing.output_size_bytes,
        })

    # 3. Parameter sweeps
    print("\n[*] Executing parameter sweeps...")
    # JPEG Quality Sweep: 95, 90, 80, 70, 50, 30, 10
    jpeg_qualities = [95, 90, 80, 70, 50, 30, 10]
    jpeg_sweep = evaluator.run_parameter_sweep(
        attack=JpegRecompressionAttack(),
        input_bytes=hires_img,
        param_name="quality",
        param_values=jpeg_qualities,
        seed=42
    )
    print(f"    - Completed JPEG Quality Sweep across {len(jpeg_qualities)} levels [95 -> 10]")

    # Resize Sweep: 100%, 75%, 50%, 25%
    resize_factors = [1.0, 0.75, 0.50, 0.25]
    resize_sweep = evaluator.run_parameter_sweep(
        attack=ResizeAttack(),
        input_bytes=hires_img,
        param_name="scale_factor",
        param_values=resize_factors,
        seed=42
    )
    print(f"    - Completed Resize Sweep across {len(resize_factors)} levels [100% -> 25%]")

    # Rotation Sweep: 0.5, 1.0, 2.0, 5.0
    rotation_angles = [0.5, 1.0, 2.0, 5.0]
    from attacks.digital.image_attacks import RotationAttack
    rotation_sweep = evaluator.run_parameter_sweep(
        attack=RotationAttack(),
        input_bytes=hires_img,
        param_name="angle",
        param_values=rotation_angles,
        seed=42
    )
    print(f"    - Completed Rotation Sweep across {len(rotation_angles)} levels [0.5 deg -> 5.0 deg]")

    # Crop Sweep: 5%, 10%, 20%, 30%
    crop_fractions = [0.05, 0.10, 0.20, 0.30]
    crop_sweep = evaluator.run_parameter_sweep(
        attack=CropAttack(),
        input_bytes=hires_img,
        param_name="crop_fraction",
        param_values=crop_fractions,
        seed=42
    )
    print(f"    - Completed Crop Sweep across {len(crop_fractions)} levels [5% -> 30%]")

    # 4. Generate structured summary matrix
    summary_matrix = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "laboratory": "SIH26237 Adversarial Attack & Robustness Lab",
        "benchmarks": benchmark_results,
        "sweeps": {
            "jpeg_quality": [
                {
                    "quality": e.parameter_value,
                    "attack_id": e.attack_result.attack_id,
                    "psnr": e.attack_result.metrics.psnr if e.attack_result.metrics else None,
                    "ssim": e.attack_result.metrics.ssim if e.attack_result.metrics else None,
                    "file_size_ratio": e.attack_result.metrics.file_size_ratio if e.attack_result.metrics else None,
                }
                for e in jpeg_sweep
            ],
            "resizing": [
                {
                    "scale_factor": e.parameter_value,
                    "attack_id": e.attack_result.attack_id,
                    "psnr": e.attack_result.metrics.psnr if e.attack_result.metrics else None,
                    "ssim": e.attack_result.metrics.ssim if e.attack_result.metrics else None,
                    "file_size_ratio": e.attack_result.metrics.file_size_ratio if e.attack_result.metrics else None,
                }
                for e in resize_sweep
            ],
            "rotation": [
                {
                    "angle_degrees": e.parameter_value,
                    "attack_id": e.attack_result.attack_id,
                    "psnr": e.attack_result.metrics.psnr if e.attack_result.metrics else None,
                    "ssim": e.attack_result.metrics.ssim if e.attack_result.metrics else None,
                }
                for e in rotation_sweep
            ],
            "crop": [
                {
                    "crop_fraction": e.parameter_value,
                    "attack_id": e.attack_result.attack_id,
                    "psnr": e.attack_result.metrics.psnr if e.attack_result.metrics else None,
                    "ssim": e.attack_result.metrics.ssim if e.attack_result.metrics else None,
                    "file_size_ratio": e.attack_result.metrics.file_size_ratio if e.attack_result.metrics else None,
                }
                for e in crop_sweep
            ],
        },
        "robustness_outcomes_summary": {
            "PASS": "High signal survival (>= 90%) and verifiable attribution with high confidence.",
            "DEGRADE": "Partial signal survival (70% - 90%) with marginal attribution evidence.",
            "FAIL": "False accusation of an innocent party or critical security violation.",
            "ABSTAIN": "Signal destroyed (< 70%) or corrupted; attribution engine strictly abstains (NO_SIGNAL / INSUFFICIENT_EVIDENCE)."
        }
    }

    summary_path = os.path.join(artifacts_dir, "summary_matrix.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_matrix, f, indent=2)

    print(f"\n[+] Saved summary matrix to: {summary_path}")
    print("[+] All benchmarks and sweep artifacts successfully generated!")

if __name__ == "__main__":
    run_benchmarks()
