# SIH26237 — Physical Watermark Validation Report

**Status:** REAL PHYSICAL VALIDATION NOT EXECUTED IN CURRENT HEADLESS ENVIRONMENT  
**Hardware Available in Runner:** False (No physical printer or smartphone camera connected)  
**Ingestion Harness & Schema Ready:** True (`scripts/watermark/ingest_physical_capture.py` & `core/watermark/schema.py`)  

---

## 1. Physical Hardware & Validation Status

As required by scientific integrity principles:
> **REAL PHYSICAL VALIDATION NOT EXECUTED**
> Physical printing on laser/inkjet printers and handheld smartphone camera captures must be performed in a physical laboratory environment. All automated numbers reported elsewhere in this repository reflect synthetic optical simulations (`PrintCameraSimulationAttack`).

---

## 2. Laboratory Execution Protocol & Readiness

The physical validation harness is fully implemented and ready for operator execution:

1. **Step 1: Document Generation & Hash Recording**
   ```bash
   py scripts/benchmark_watermark.py
   # Generates printable high-res watermarked artifacts in artifacts/watermark/
   ```

2. **Step 2: Physical Printing**
   - Print on **HP LaserJet Pro M404n** (600 DPI, Monochrome) or **Canon PIXMA TS8320** (300 DPI, Color Inkjet).
   - Use standard 80 g/m^2 A4 copy paper.

3. **Step 3: Smartphone Photography**
   - Capture at angles 0°, 10°, 20°, 30° under normal office light (400 lux) and uneven side-desk lamp lighting.
   - Preserve original camera files (JPEG / HEIC / PNG).

4. **Step 4: Automated Ingestion & Evaluation**
   ```bash
   py scripts/watermark/ingest_physical_capture.py \
       --image path/to/physical_capture.jpg \
       --doc-id DOC_INTEL_01 \
       --release-id REL_2026_01 \
       --printer "HP LaserJet Pro M404n" \
       --printer-type Laser \
       --camera-model "iPhone 15 Pro" \
       --angle "~15 deg tilt" \
       --output-json artifacts/watermark/physical_results.json
   ```

5. **Step 5: Output Verification**
   The CLI automatically appends records conforming to `PhysicalExperimentRecord` into `artifacts/watermark/physical_results.json`.
