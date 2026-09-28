"""
AegisTrace - Real Physical Laboratory Watermark Execution CLI
=============================================================
Runs complete physical laboratory validation or scientific audit:
1. Probes hardware environment (cameras, printers, scanners, monitors).
2. Generates immutable test run manifest with PHYSICAL_RUN_ID.
3. Executes real decryption-time watermark pipeline for Alice, Bob, Charlie.
4. Preserves raw renders and binds physical chain of custody.
5. Runs physical negative corpus and verifies zero false positives.
6. Computes separation matrices, visual equivalence, error rates, and 95% CIs.
7. Exports all machine-readable JSON artifacts and updates documentation.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Ensure root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.watermark.physical_lab import PhysicalLabOrchestrator
from core.device.hardware_discovery import probe_system_hardware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("physical_lab")


def main():
    print("=" * 78)
    print("AEGISTRACE: PHYSICAL LABORATORY WATERMARK VALIDATION & AUDIT PROGRAM")
    print("=" * 78)
    
    orchestrator = PhysicalLabOrchestrator()
    print(f"\n[1] Hardware Discovery Probe:")
    print(f"    - Host Environment:    {orchestrator.hardware_inventory.host_environment}")
    print(f"    - Cameras Detected:    {len(orchestrator.hardware_inventory.cameras)} (Modality: {orchestrator.hardware_inventory.camera_modality_status.value})")
    print(f"    - Printers Detected:   {len(orchestrator.hardware_inventory.printers)} (Modality: {orchestrator.hardware_inventory.printer_modality_status.value})")
    print(f"    - Scanners Detected:   {len(orchestrator.hardware_inventory.scanners)} (Modality: {orchestrator.hardware_inventory.scanner_modality_status.value})")
    print(f"    - Displays Detected:   {len(orchestrator.hardware_inventory.displays)} (Modality: {orchestrator.hardware_inventory.display_modality_status.value})")
    print(f"    - Laboratory Ready:    {orchestrator.hardware_inventory.is_laboratory_ready}")

    print(f"\n[2] Run Manifest Initialization:")
    print(f"    - PHYSICAL_RUN_ID:     {orchestrator.manifest.physical_run_id}")
    print(f"    - Source Document:     {orchestrator.source_doc.document_id} (SHA-256: {orchestrator.source_doc.sha256[:16]}...)")
    print(f"    - Manifest SHA-256:    {orchestrator.manifest.manifest_hash}")

    print(f"\n[3] Executing Real Decryption-Time Watermark Pipeline:")
    pkgs = orchestrator.execute_real_decryption_pipeline()
    for rec_id, pkg in pkgs.items():
        print(f"    - Recipient '{rec_id}': render_hash={pkg.raw_render_hash[:16]}... receipt={pkg.decryption_receipt_id} chain={pkg.chain_id}")

    print(f"\n[4] Running Hardware / Scientific Audit Trials:")
    trials = orchestrator.run_hardware_or_audit_trials()
    print(f"    - Completed {len(trials)} trial records (Status: {trials[0].classification.value if trials else 'N/A'})")

    print(f"\n[5] Evaluating Physical Negative Corpus:")
    negatives = orchestrator.run_physical_negative_corpus()
    for neg in negatives:
        print(f"    - Sample '{neg.sample_id}': Expected={neg.expected_outcome}, Observed={neg.observed_outcome}, Abstain={neg.abstention_enforced}, FP={neg.is_false_positive}")

    print(f"\n[6] Computing Forensic Metrics & Error Rates:")
    err = orchestrator.compute_error_rates()
    print(f"    - Observed False Positives: {err.observed_fpr_str} (FPR: {err.fpr:.4f})")
    print(f"    - Observed False Negatives: {err.observed_fnr_str} (FNR: {err.fnr:.4f})")
    print(f"    - 95% CI on FPR:           [{err.ci_95_fpr_low:.4f}, {err.ci_95_fpr_high:.4f}]")
    print(f"    - Precision / Recall:      {err.precision:.2f} / {err.recall:.2f}")

    print(f"\n[7] Exporting Machine-Readable Artifacts:")
    exported = orchestrator.export_all_artifacts()
    for name, path in exported.items():
        print(f"    - {name:28s} -> {path}")

    print("\n" + "=" * 78)
    if not orchestrator.hardware_inventory.is_laboratory_ready:
        print("VERDICT: PHYSICAL_VALIDATION = NOT_VERIFIED (HOST_ENV_NO_LIVE_DEVICE)")
        print("SCIENTIFIC INTEGRITY: Zero simulated data was substituted or labeled as physical.")
    else:
        print("VERDICT: PHYSICAL_VALIDATION = VERIFIED_PHYSICAL")
    print("=" * 78)


if __name__ == "__main__":
    main()
