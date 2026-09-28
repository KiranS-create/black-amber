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
# Verify air-gapped isolation (no network calls)
pytest tests/physical/ -v
```

---

## 3. Step-by-Step Laboratory Execution Protocol

### Step 1: Autonomous Hardware Discovery & Calibration
Run the master laboratory execution script:
```bash
python scripts/physical/run_physical_lab.py
```

Expected Output Flow:
1. Probing OpenCV VideoCapture devices (Index 0..3)
2. Querying Windows Print Spooler / CUPS (`Get-Printer` filtering virtual queues)
3. Probing WIA / TWAIN scanners
4. Generating deterministic Run Manifest with canonical SHA-256 hash
5. Executing volatile decryption-time dynamic watermark embedding (Alice, Bob, Charlie)
6. Executing 108 screen photograph trials, 6 print trials, and 9 multi-stage transformation chains
7. Evaluating 40 negative/adversarial corpus samples
8. Measuring cross-recipient separation matrix and visual equivalence
9. Calculating exact Clopper-Pearson 95% confidence intervals
10. Assembling and verifying ML-DSA-65 post-quantum Evidence Packages offline

---

## 4. Attaching Real Physical Hardware
To perform physical hardware-grounded validation:
1. Connect a USB UVC Camera or smartphone running standard webcam drivers (e.g., Camo / DroidCam / OBS Virtual Cam).
2. Connect a physical USB or Network Laser Printer (HP, Canon, Epson).
3. Connect a physical flatbed scanner (WIA / TWAIN driver installed).
4. Re-run `python scripts/physical/run_physical_lab.py`.
5. The system will automatically detect the devices, update `hardware_inventory.json` with `is_physical: true`, and transition the epistemic status from `NOT_VERIFIED` to `GENUINE_HARDWARE_GROUNDED`.
