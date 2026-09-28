"""
SIH26237 - Master Physical Laboratory Validation Program
Executes the comprehensive hardware-grounded validation workflow:
1. Hardware discovery (cameras, printers, scanners, displays)
2. Laboratory run manifest & cryptographic attestation
3. Golden physical source document generation & hashing
4. Decryption-time watermark physical trials (Alice, Bob, Charlie)
5. Screen photograph, print, and multi-stage transformation experiments
6. Negative corpus & adversarial rejection evaluation
7. Cross-recipient physical separation matrix
8. Visual equivalence distribution measurement
9. Physical failure boundaries & operating envelope
10. Chain of custody tracking & raw evidence preservation
11. Evidence package assembly & offline air-gap verification
12. Export of all 9 machine-readable JSON artifacts
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import cv2
import numpy as np

# Ensure repository root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.physical import (
    HardwareDiscoveryEngine,
    RunManifestFactory,
    GoldenPhysicalSourceBuilder,
    PhysicalTrialEngine,
    PhysicalExperimentRunner,
    PhysicalNegativeCorpusBuilder,
    PhysicalSeparationMatrixAnalyzer,
    PhysicalVisualEquivalenceAnalyzer,
    PhysicalChainOfCustodyTracker,
    PhysicalFailureBoundaryAnalyzer,
    PhysicalMetricsCalculator,
    PhysicalEvidenceBridge,
)
from core.watermark.sync import CanonicalCanvasSpec


def run_master_physical_lab():
    print("[*] ==================================================================")
    print("[*] Starting AegisTrace Physical Laboratory Validation Program")
    print("[*] ==================================================================")

    output_dir = repo_root / "artifacts" / "physical_validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Hardware Discovery
    print("[+] 1. Performing autonomous physical hardware discovery...")
    inventory = HardwareDiscoveryEngine.discover_all()
    print(f"    - Host: {inventory.host_name} ({inventory.platform})")
    print(f"    - Cameras: {inventory.camera_status.value} ({len(inventory.get_devices_by_modality('CAMERA'))} detected)")
    print(f"    - Printers: {inventory.printer_status.value} ({len(inventory.get_devices_by_modality('PRINTER'))} detected)")
    print(f"    - Scanners: {inventory.scanner_status.value} ({len(inventory.get_devices_by_modality('SCANNER'))} detected)")
    print(f"    - Displays: {inventory.display_status.value} ({len(inventory.get_devices_by_modality('DISPLAY'))} detected)")
    print(f"    - Lab Hardware Status: {inventory.epistemic_classification}")

    with open(output_dir / "hardware_inventory.json", "w", encoding="utf-8") as f:
        f.write(inventory.model_dump_json(indent=2))

    # 2. Laboratory Run Manifest & Cryptographic Attestation
    print("[+] 2. Generating laboratory run manifest & cryptographic attestation...")
    manifest = RunManifestFactory.create_run_manifest(
        inventory=inventory,
        operator="AEGISTRACE_LAB_OPERATOR_AIRGAP",
        random_seed=26237,
        custom_metadata={"testbench_version": "v2.1-physical-harness"}
    )
    print(f"    - Run ID: {manifest.run_id}")
    print(f"    - Manifest SHA-256: {manifest.manifest_hash}")
    print(f"    - Epistemic Classification: {manifest.epistemic_classification}")

    with open(output_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))

    # 3. Initialize Chain of Custody Tracker & Golden Source Document
    print("[+] 3. Initializing Chain of Custody & rendering Golden Physical Source...")
    custody_tracker = PhysicalChainOfCustodyTracker(
        run_id=manifest.run_id,
        base_dir=str(output_dir / "runs"),
        operator=manifest.operator
    )

    canvas_spec = CanonicalCanvasSpec(width=800, height=1000)
    golden_canvas, golden_spec = GoldenPhysicalSourceBuilder.render_canonical_canvas(spec=canvas_spec)
    golden_bytes = golden_canvas.tobytes()

    custody_tracker.record_transition(
        action="COLLECTED",
        artifact_bytes=golden_bytes,
        filename="golden_source_canonical.raw",
        device_id="HOST_CANVAS_RENDERER",
        folder="raw",
        notes=f"Golden source canvas SHA-256: {golden_spec.source_sha256}"
    )

    # 4. Decryption-Time Dynamic Watermark Trials
    print("[+] 4. Executing decryption-time dynamic watermark trials (Alice, Bob, Charlie)...")
    trial_engine = PhysicalTrialEngine(canvas_spec=canvas_spec)
    trial_engine.setup_standard_laboratory_recipients()

    alice_canvas, alice_rec = trial_engine.execute_decryption_and_render_artifact("rec_alice")
    bob_canvas, bob_rec = trial_engine.execute_decryption_and_render_artifact("rec_bob")
    charlie_canvas, charlie_rec = trial_engine.execute_decryption_and_render_artifact("rec_charlie")

    custody_tracker.record_transition(
        action="PRINTED",
        artifact_bytes=alice_canvas.tobytes(),
        filename="alice_rendered_watermarked.raw",
        device_id="DECRYPTION_WATERMARK_ENGINE",
        folder="processed",
        notes=f"Alice trial {alice_rec.trial_id} DLT height {alice_rec.dlt_block_height}"
    )

    # 5. Controlled Optical Experiments (Screen, Print, Multi-Stage)
    print("[+] 5. Running controlled optical & physical experiment suites...")
    runner = PhysicalExperimentRunner(trial_engine=trial_engine, inventory=inventory, canvas_spec=canvas_spec)

    screen_trials = runner.run_screen_photo_experiments(recipient_id="rec_alice")
    print(f"    - Screen Photo Trials: {len(screen_trials)} executed")

    print_trials = runner.run_print_experiments(recipient_id="rec_bob")
    print(f"    - Print Simulation Trials: {len(print_trials)} executed")

    multistage_trials = runner.run_multi_stage_transformations(recipient_id="rec_charlie")
    print(f"    - Multi-Stage Transformation Trials: {len(multistage_trials)} executed")

    all_positive_trials = screen_trials + print_trials + multistage_trials
    with open(output_dir / "physical_trial_results.json", "w", encoding="utf-8") as f:
        f.write(json.dumps([t.model_dump() for t in all_positive_trials], indent=2))

    # 6. Physical Negative Corpus Evaluation
    print("[+] 6. Evaluating 40-sample physical negative & adversarial corpus...")
    neg_builder = PhysicalNegativeCorpusBuilder(canvas_spec=canvas_spec, trial_engine=trial_engine)
    neg_results = neg_builder.evaluate_negative_corpus()
    fp_count = sum(1 for n in neg_results if n.false_positive_attribution)
    print(f"    - Negative Samples: {len(neg_results)} evaluated")
    print(f"    - False Positives Observed: {fp_count} / {len(neg_results)}")

    with open(output_dir / "physical_negative_results.json", "w", encoding="utf-8") as f:
        f.write(json.dumps([n.model_dump() for n in neg_results], indent=2))

    # 7. Cross-Recipient Physical Separation Matrix
    print("[+] 7. Computing cross-recipient physical separation matrix...")
    separation_summary = PhysicalSeparationMatrixAnalyzer.analyze_cross_recipient_separation(
        trial_engine=trial_engine,
        canvas_spec=canvas_spec
    )
    print(f"    - Mean Hamming Distance: {separation_summary.mean_pairwise_hamming_distance} bits")
    print(f"    - Cross-Recipient Collisions: {separation_summary.observed_cross_recipient_collisions} / {len(separation_summary.pairwise_entries)}")

    with open(output_dir / "physical_separation_matrix.json", "w", encoding="utf-8") as f:
        f.write(separation_summary.model_dump_json(indent=2))

    # 8. Visual Equivalence Distribution
    print("[+] 8. Measuring visual equivalence distributions under physical render...")
    visual_metrics = PhysicalVisualEquivalenceAnalyzer.evaluate_visual_distribution(
        sample_count=30,
        trial_engine=trial_engine,
        canvas_spec=canvas_spec
    )
    print(f"    - SSIM Median: {visual_metrics.ssim_median} (P99: {visual_metrics.ssim_p99})")
    print(f"    - PSNR Median: {visual_metrics.psnr_median_db} dB")
    print(f"    - Max Pixel Delta Median: {visual_metrics.max_pixel_delta_median}")

    with open(output_dir / "physical_visual_equivalence.json", "w", encoding="utf-8") as f:
        f.write(visual_metrics.model_dump_json(indent=2))

    # 9. Hardware Failure Boundaries & Operating Envelope
    print("[+] 9. Establishing empirical hardware failure boundaries...")
    operating_envelope = PhysicalFailureBoundaryAnalyzer.evaluate_failure_boundaries(
        trial_engine=trial_engine,
        canvas_spec=canvas_spec
    )
    print(f"    - Max Safe Angle: {operating_envelope.max_safe_angle_deg}°")
    print(f"    - Max Safe Distance: {operating_envelope.max_safe_distance_cm} cm")
    print(f"    - Max Safe Optical Blur: sigma {operating_envelope.max_safe_blur_sigma}")

    with open(output_dir / "physical_failure_boundaries.json", "w", encoding="utf-8") as f:
        f.write(operating_envelope.model_dump_json(indent=2))

    # 10. Statistical Uncertainty & Confidence Intervals
    print("[+] 10. Calculating statistical error rates and exact Clopper-Pearson CIs...")
    uncertainty_summary = PhysicalMetricsCalculator.compute_summary(
        positive_results=all_positive_trials,
        negative_results=neg_results
    )
    print(f"    - Evaluated Total: {uncertainty_summary.total_samples}")
    print(f"    - Empirical FPR: {uncertainty_summary.fpr_empirical_str} (95% CI: [{uncertainty_summary.fpr_ci_clopper_pearson.lower_bound_95:.4f}, {uncertainty_summary.fpr_ci_clopper_pearson.upper_bound_95:.4f}])")
    print(f"    - Empirical FNR: {uncertainty_summary.fnr_empirical_str} (95% CI: [{uncertainty_summary.fnr_ci_clopper_pearson.lower_bound_95:.4f}, {uncertainty_summary.fnr_ci_clopper_pearson.upper_bound_95:.4f}])")

    with open(output_dir / "physical_uncertainty.json", "w", encoding="utf-8") as f:
        f.write(uncertainty_summary.model_dump_json(indent=2))

    # 11. Evidence Package Bridge & Offline Verification
    print("[+] 11. Assembling Evidence Packages & verifying offline in air-gap...")
    golden_trial_result = screen_trials[0]
    pkg_1, ver_1 = PhysicalEvidenceBridge.assemble_physical_evidence_package(
        case_id="PHYS_CASE_GOLDEN_01",
        trial_record=alice_rec,
        trial_result=golden_trial_result,
        custody_tracker=custody_tracker,
        is_downstream_gap=False
    )
    print(f"    - Golden Case 1 (Direct Leak): Signed & Verified offline (Status: {ver_1.overall_status.value}, Errors: {len(ver_1.errors)})")

    pkg_2, ver_2 = PhysicalEvidenceBridge.assemble_physical_evidence_package(
        case_id="PHYS_CASE_DOWNSTREAM_02",
        trial_record=bob_rec,
        trial_result=print_trials[0],
        custody_tracker=custody_tracker,
        is_downstream_gap=True
    )
    print(f"    - Golden Case 2 (Downstream Gap): Signed & Verified offline (Status: {ver_2.overall_status.value}, Errors: {len(ver_2.errors)})")

    # 12. Seal Chain of Custody Ledger
    custody_tracker.record_transition(
        action="SEALED",
        artifact_bytes=manifest.manifest_hash.encode(),
        filename="manifest_seal.sig",
        device_id="AIRGAP_OFFLINE_VERIFIER",
        folder="results",
        notes="Physical validation run completed and sealed."
    )
    custody_tracker.save_and_seal_ledger()

    # Save run chain of custody copy to root
    with open(output_dir / "physical_chain_of_custody.json", "w", encoding="utf-8") as f:
        f.write(custody_tracker.ledger.model_dump_json(indent=2))

    print("[+] 12. All 9 machine-readable JSON artifacts successfully exported to artifacts/physical_validation/")
    print("[*] ==================================================================")
    print("[*] Physical Laboratory Validation Program Complete (Status: NOT_VERIFIED)")
    print("[*] ==================================================================")


if __name__ == "__main__":
    run_master_physical_lab()
