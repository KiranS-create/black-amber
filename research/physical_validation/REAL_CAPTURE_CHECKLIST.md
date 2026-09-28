# AegisTrace (SIH26237) — Real Hardware Capture Execution Checklist

**Document Purpose:** Operational runbook for laboratory operators conducting physical print and smartphone capture validation of watermarked documents.

---

## Pre-Flight Setup

- [ ] **1. Clean Environment:** Ensure flat, non-reflective desk surface (matte gray or black background recommended).
- [ ] **2. Lighting Verification:**
  - Verify lux meter reading: $400\text{--}600\text{ lux}$ for standard diffuse tests (Condition L1).
  - Verify lamp positioning for gradient tests (Condition L2).
- [ ] **3. Printer Preparation:**
  - Check toner/ink levels ($> 50\%$).
  - Clean printer glass/rollers to avoid stray physical artifacts.
  - Load fresh 80 gsm A4 white multi-purpose copy paper.
- [ ] **4. Camera Configuration:**
  - Clean smartphone camera lens with microfiber cloth.
  - Set camera app to standard photo mode (disable portrait mode, filters, or heavy beauty smoothing).
  - Set image resolution to native 12MP JPEG/HEIC.
  - Set exposure mode to auto with center-weighted metering.

---

## Step-by-Step Capture Procedure

### Phase 1: Document Generation & Export
```bash
py scripts/benchmark_watermark.py
# Generates high-resolution watermarked document in artifacts/watermark/sample_watermarked_document.png
```
- Verify all 4 ArUco fiducial markers (IDs 10, 11, 12, 13) are clearly visible at canvas corners with $\ge 40\text{ px}$ margin.
- Verify SHA-256 hash of output digital image is logged.

### Phase 2: Physical Printing
- Print image at $100\%$ scaling (disable "Fit to Printable Area" or "Shrink to Fit").
- Inspect printed page for severe smudging or paper jams.
- Record printer model, toner/cartridge batch, and paper substrate.

### Phase 3: Handheld Photograph Capture Matrix
Execute 6 captures per printed document:

| Shot ID | Angle / Orientation | Distance | Lighting | Framing |
| :--- | :--- | :--- | :--- | :--- |
| `SHOT_01` | $0^\circ$ (Directly Overhead / Normal) | $\approx 35\text{ cm}$ | L1 (Office Diffuse) | Full Page Frame (All 4 markers visible) |
| `SHOT_02` | $15^\circ$ Tilt (Top-to-Bottom Pitch) | $\approx 35\text{ cm}$ | L1 (Office Diffuse) | Full Page Frame |
| `SHOT_03` | $30^\circ$ Skew (Oblique Perspective) | $\approx 30\text{ cm}$ | L1 (Office Diffuse) | Full Page Frame |
| `SHOT_04` | $0^\circ$ (Overhead) | $\approx 35\text{ cm}$ | L2 (Directional Gradient) | Full Page Frame |
| `SHOT_05` | $15^\circ$ Tilt | $\approx 35\text{ cm}$ | L2 (Directional Gradient) | Full Page Frame |
| `SHOT_06` | $0^\circ$ (Overhead) | $\approx 25\text{ cm}$ | L3 (Low Light + Flash) | Slight Marginal Crop ($\ge 3$ markers visible) |

### Phase 4: File Transfer & Ingestion
- Copy raw capture files from smartphone to `artifacts/physical_validation/captures/`.
- Run the ingestion CLI for each capture:
```bash
py scripts/watermark/ingest_physical_capture.py \
    --image artifacts/physical_validation/captures/iphone15_shot01.jpg \
    --doc-id DOC_CONFIDENTIAL_2026 \
    --release-id REL_01 \
    --codeword-len 128 \
    --printer "HP LaserJet Pro M404n" \
    --printer-type Laser \
    --paper "80gsm standard copy paper" \
    --camera-model "iPhone 15 Pro" \
    --lighting "450 lux diffuse office" \
    --angle "0 deg normal" \
    --distance "~35cm" \
    --output-json artifacts/physical_validation/validation_results.json \
    --debug-dir artifacts/physical_validation/debug/
```

### Phase 5: Result Inspection & Pass Criteria
- [ ] Confirm `sync_status == "OK"` and `marker_count >= 3`.
- [ ] Confirm `reprojection_error < 1.0 px`.
- [ ] Confirm `pre_ecc_ber < 0.15` and `post_ecc_ber == 0.0`.
- [ ] Confirm `watermark_status == "RECOVERED"`.
- [ ] Confirm `tardos_state == "ATTRIBUTED"` with expected recipient ID accused.
