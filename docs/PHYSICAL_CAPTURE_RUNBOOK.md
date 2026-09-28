# AegisTrace: Physical Document Capture & Forensic Ingestion Runbook

**Document Version:** 2.0.0  
**Target Audience:** Forensic Investigators, Laboratory Technicians, Security Compliance Officers  
**Security Classification:** RESTRICTED FORENSIC PROCEDURE  

---

## 1. Scope & Objective

This runbook establishes standard operating procedures for generating, physically handling, optically capturing, and ingesting physical document artifacts into the AegisTrace Forensic Watermark Recovery System.

Strict adherence ensures evidentiary chain-of-custody, reproducibility, and compliance with the zero false accusation standard ($FPR = 0.0000$).

---

## 2. Operator Pre-Flight Checklist

Before conducting any printing or optical document acquisition, the laboratory operator must verify the following physical testbed conditions:

- [ ] **Camera Optics Inspection:** Inspect the smartphone or camera objective lens. Clean using optical-grade microfiber cloth and lens fluid to eliminate fingerprint oils and diffuse smudges.
- [ ] **Illumination Verification:**
  - Activate diffuse overhead LED lamps ($5000\text{K}$ neutral spectrum).
  - Measure incident lux at the copyboard using a calibrated illuminance meter: verify $500 \pm 50 \text{ lux}$.
  - Confirm absence of direct specular highlights or harsh shadows across the document page.
- [ ] **Substrate Planarity:** Ensure the test document lies perfectly flat against a non-reflective matte gray copyboard. If necessary, use low-tack magnetic edge weights outside the active document boundary.
- [ ] **Fiducial Clearance:** Verify that all four corner ArUco fiducials are fully visible and not obstructed by fingers, clips, or staples.

---

## 3. Physical Document Printing Protocol

To preserve high-frequency DSSS chip modulation during printing:

1. **Document Export:**
   - Always export the watermarked PDF or PNG from AegisTrace at $100\%$ scale ($1:1$ physical mapping).
   - **CRITICAL WARNING:** Disable printer driver settings such as *"Fit to Printable Area"*, *"Shrink Oversized Pages"*, or *"Page Scaling"*. Scaling the canvas alters the canonical chip grid geometry and degrades demodulation SNR.
2. **Printer Configuration:**
   - **Recommended Modality:** Monochrome Laser Printer ($600 \text{ DPI}$ or $1200 \text{ DPI}$) with genuine high-density carbon toner.
   - **Print Quality Setting:** Set to *"High / Presentation"* (disable toner-saving / draft modes).
3. **Paper Handling:**
   - Use clean, uncreased $80 \text{ gsm}$ or $100 \text{ gsm}$ white bond paper.
   - Allow toner to cool and fuse for $\ge 30 \text{ seconds}$ before handling to prevent toner smearing.
4. **Physical Labeling & Chain of Custody:**
   - Assign a unique physical accession number (e.g. `PHYS-2026-0042`) written on the reverse side of the page.
   - Record operator identity, printer serial, paper stock, and timestamp in the laboratory logbook.

---

## 4. Optical Camera Capture Protocol

### 4.1 Mounting & Geometry
- **Rigid Mount:** Secure the smartphone or digital camera to an overhead copy stand or rigid articulating arm. Handheld captures are permissible only for handheld mobility sweeps.
- **Working Distance:** Set camera height to $35 \pm 5 \text{ cm}$ above the paper plane, ensuring the document occupies approximately $75\%\text{--}90\%$ of the image frame.
- **Perspective Alignment:** Align the optical axis perpendicular to the document plane ($\theta = 0^\circ$). The four-corner ArUco synchronizer tolerates off-axis tilt up to $15^\circ$, but near-perpendicular alignment maximizes forensic confidence.

### 4.2 Sensor & Exposure Settings
- **Resolution:** Native sensor resolution must be $\ge 12 \text{ MP}$ ($3000 \times 4000 \text{ px}$) or $\ge 800 \times 1000 \text{ px}$ post-rectification.
- **Exposure:** Manual or auto-exposure locked to prevent white blowout ($>240$ digital levels) or underexposed shadows ($<15$ levels).
- **Focus:** Lock autofocus onto the center typography of the document.
- **Flash:** **FLASH OFF.** Camera-mounted specular flashes create localized bright spots that destroy ArUco corner markers and carrier chips.

---

## 5. Ingestion Pipeline & Execution

### 5.1 Autonomous Forensic Capture Importer
The repository provides a dedicated physical artifact capture importer:

```powershell
python -m attacks.physical.capture `
    --input "data/captures/PHYS_2026_0042.jpg" `
    --output "artifacts/forensic_cases/CASE_0042" `
    --expected-doc "DOC_DEFENSE_2026" `
    --expected-release "REL_2026_Q3"
```

### 5.2 Automated Pre-Ingestion Image Quality Assessment (IQA)
Every ingested capture passes through an automated pre-flight quality check:

```python
iqa = compute_physical_iqa(captured_image)
# Metrics checked:
# - Sharpness (Laplacian variance >= 40.0)
# - Exposure (40.0 <= Mean luminance <= 225.0)
# - Dynamic Range Clipping (Overexposed & Underexposed < 25%)
# - Resolution (Width >= 600 px, Height >= 600 px)
```

If `iqa["iqa_usable"] == False`:
- The ingestion pipeline halts immediately and prompts the operator with the specific defect (`DEFOCUS_BLUR`, `UNDEREXPOSED`, `SPECULAR_SATURATION`, `LOW_RESOLUTION`).
- The capture is logged as `INVALID_CAPTURE` and flagged for mandatory retake.

---

## 6. Retake & Troubleshooting Guide

| Observed Defect | Root Cause | Operator Action |
|---|---|---|
| `NO_SIGNAL (ArUco < 3 markers)` | Corner occlusion or extreme tilt ($>20^\circ$) | Reposition camera, remove paper weights from margins, verify all 4 markers are in frame. |
| `INSUFFICIENT_EVIDENCE (RS uncorrectable)` | Severe optical defocus blur ($\sigma > 1.5$) | Clean lens, re-engage autofocus lock on document body, increase ambient lighting. |
| `CONFLICT (Document binding error)` | Wrong document ID supplied or physical transplantation attack | Verify chain-of-custody document accession ID; escalate to forensic security lead if deliberate tampering is suspected. |
| `High Reprojection Error (> 2.5 px)` | Non-planar paper curvature (curled corners) | Flatten paper substrate using glass pressure plate or matte magnetic edge strips. |
| `Specular Glare Blotches` | Direct overhead bulb reflection | Angle diffuse light sources at $45^\circ$ to paper plane. |

---

## 7. Evidence Cataloging & Chain-of-Custody Record

Every accepted physical capture generates an immutable metadata record stored alongside the raw image:

```json
{
  "case_id": "FORENSIC_PHYS_2026_0042",
  "ingested_at": "2026-09-27T16:40:00Z",
  "operator_id": "OP_LAB_FORENSIC_7",
  "sha256_raw_capture": "a8f3b...912e",
  "iqa": {
    "sharpness_laplacian_var": 74.32,
    "mean_luminance": 182.4,
    "is_sharp": true,
    "is_well_exposed": true,
    "iqa_usable": true
  },
  "forensic_decision": "RECOVERED_CORRECT",
  "attributed_recipient_id": "rec_alice_4a12",
  "carrier_strategy": "RENDERED_PAGE_CANVAS",
  "confidence": 0.942,
  "homography_reprojection_error_px": 0.84,
  "hardware_modality": "PHYSICAL_CANON_EOS_12MP",
  "offline_airgap_verified": true
}
```
