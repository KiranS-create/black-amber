# AegisTrace Physical Laboratory Validation Reproducibility Guide

## 1. Overview
This runbook enables third-party forensic evaluators, certifiers, and laboratory personnel to reproduce the physical/optical validation suite either under simulated optical channel models or directly with live physical hardware (cameras, printers, scanners).

---

## 2. Prerequisites & Environment Setup

### System Requirements
- Python 3.9+
- OpenCV (`cv2`) 4.8+
- NumPy 1.24+
- PyTest 8.0+

### Air-Gapped Clean Environment Check
```bash
# Verify air-gapped isolation and test passing
pytest tests/physical/ tests/watermark/ -v
```

---

## 3. Step-by-Step Laboratory Execution Protocol

### Step 1: Autonomous Hardware Discovery & Calibration
Run the master laboratory execution script:
```bash
python scripts/watermark/run_physical_laboratory_execution.py
```

Expected Output Flow:
1. Probing OpenCV VideoCapture devices (Index 0..3)
2. Querying Windows Print Spooler / CUPS (`Get-Printer` filtering virtual queues)
3. Probing WIA / TWAIN scanners
4. Generating deterministic Run Manifest (`PHYSICAL_RUN_ID`) with canonical SHA-256 hash
5. Executing volatile decryption-time dynamic watermark embedding (Alice, Bob, Charlie)
6. Running scientific audit trials & evaluation
7. Evaluating physical negative corpus (unwatermarked, noise, transplant)
8. Measuring cross-recipient separation matrix and visual equivalence
9. Calculating exact 95% Wilson confidence intervals
10. Exporting all 9 machine-readable JSON artifacts to `artifacts/physical_validation/`

---

## 4. Attaching Real Physical Hardware
To perform physical hardware-grounded validation:
1. Connect a USB UVC Camera or smartphone running standard webcam drivers.
2. Connect a physical USB or Network Laser Printer (HP, Canon, Brother).
3. Connect a physical flatbed scanner (WIA / TWAIN driver installed).
4. Re-run `python scripts/watermark/run_physical_laboratory_execution.py`.
5. The system will automatically detect the devices, update `hardware_inventory.json` with `is_physical: true`, and transition the epistemic status from `NOT_VERIFIED` to `MEASURED_PHYSICAL`.
