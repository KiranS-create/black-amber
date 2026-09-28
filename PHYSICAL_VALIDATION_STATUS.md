# AegisTrace: Physical Laboratory & Device Validation Status

**Document ID:** `SIH26237-PHYSICAL-STATUS-V2`  
**Classification:** RESTRICTED / SCIENTIFIC AUDIT  
**Audit Timestamp:** 2026-09-27T23:15:00Z  
**Host Architecture:** Windows 11 Enterprise x64 (Host: `MSI`)  
**Overall Physical Epistemic Verdict:** **`HYBRID_VALIDATION`**  
**Hardware Inventory Artifact:** [`artifacts/device_validation/hardware_inventory.json`](file:///C:/Projects/SIH26237/artifacts/device_validation/hardware_inventory.json)  

---

## 1. Scientific Audit & Epistemic Declaration

AegisTrace strictly adheres to scientific integrity: **A forensic system must never misreport simulated processes as real physical sensor measurements, nor claim device capabilities that do not physically exist.**

During the formal audit of the execution host environment, the autonomous hardware inspection harness ([`core/physical/device_discovery.py`](file:///C:/Projects/SIH26237/core/physical/device_discovery.py)) interrogated the operating system for connected physical capture, print, display, network, and computing devices.

### Live Hardware Probe Results

| Modality / Subsystem | Detection Method | Devices Detected | Epistemic Status | Scientific Claim / Boundary |
| :--- | :--- | :---: | :--- | :--- |
| **Phone A (Recipient)** | USB Composite / PnP / ADB probe | 1 Device (`SM-N770F`, `RF8N927PM9N`) | **`DEVICE_IN_LOOP`** | Authenticated recipient session & transfer endpoint. |
| **Phone B (Isolated)** | USB Composite / PnP probe | 1 Device (`SM-A556B`, `RZCY9396AGX`) | **`DEVICE_IN_LOOP`** | Independent isolated secondary endpoint. |
| **Laptop Display** | Windows EnumDisplayDevices API | 1 Monitor (AMD Radeon 1080p@144Hz) | **`DEVICE_IN_LOOP`** | Physical pixel presentation verified to framebuffer. |
| **Local Network** | Windows Get-NetIPAddress | 6 Interfaces (Active Wi-Fi: `10.114.31.4`) | **`DEVICE_IN_LOOP`** | Real socket delivery across local subnet. |
| **Document Cameras** | OpenCV `VideoCapture` indices 0–3 | None (`0`) | **`NOT_VERIFIED`** | Camera capture is NOT claimed or fabricated. |
| **Physical Printers** | PowerShell Get-Printer (Physical only) | None (`0`) | **`UNAVAILABLE`** | Laser/inkjet printing is NOT claimed. |
| **Document Scanners** | Windows Image Acquisition (WIA) | None (`0`) | **`UNAVAILABLE`** | Flatbed optical scanning is NOT claimed. |
| **Optical Channel Model**| Mathematical PSF / homography | Computational | **`SIMULATION_CALIBRATION`** | Explicitly labeled calibrated computational model. |
| **Composite Validation** | Unified Hardware & Device Pipeline | Multi-Subsystem | **`HYBRID_VALIDATION`** | Transparent, non-fabricated hybrid validation. |

---

## 2. Strict Epistemic Invariants & Anti-Fabrication Guarantees

1. **Non-Fabrication Invariant:**
   - 0 physical cameras detected $\implies$ Camera capability is truthfully and permanently marked **`NOT_VERIFIED`**.
   - 0 physical printers detected $\implies$ Print capability is truthfully and permanently marked **`UNAVAILABLE`**.
   - 0 physical scanners detected $\implies$ Scan capability is truthfully and permanently marked **`UNAVAILABLE`**.
2. **Separation Invariants:**
   - `USB_CONNECTED != CAMERA_AVAILABLE`: Connecting a phone via USB never constitutes camera availability.
   - `IMAGE_TRANSFERRED != OPTICAL_CAPTURE_VERIFIED`: Transferring an image file to a phone is strictly `TRANSFERRED`, not `CAPTURED`.
   - `PDF_RENDERED_ON_PHONE != PDF_PHYSICALLY_VALIDATED`: Screen rendering does not validate paper printout resilience.
3. **Fail-Closed Custody Ledger:**
   - The [`DeviceCustodyLedger`](file:///C:/Projects/SIH26237/core/physical/device_custody.py) strictly rejects recording any event with action `CAPTURED` unless backed by a real optical sensor stream. Digital transfers must use `TRANSFERRED`.

---

## 3. Golden Experiment & Multi-Format Results Summary

The 13-step Device-in-the-Loop golden experiment was executed by [`core/physical/device_in_loop.py`](file:///C:/Projects/SIH26237/core/physical/device_in_loop.py):
- **13 Steps Executed:** 13/13 Passed (`PASS`).
- **Multi-Format Coverage:** PDF, DOCX, PPTX, XLSX, PNG, JPEG all successfully watermarked, transferred, bit-audited, and recovered.
- **Sparse Merkle Lineage Root:** `db432ae32a9528a582910906ca24a3c1abd10472ab6fc127085f1638d2ec8169`
- **Custody Root Hash:** `c7c90220f44678b30fcc3ad0436950351ab80f1f1e59531781094c0be7027e55`
- **Offline Evidence Verifier:** **`VERIFIED`** (Package: `pkg_CASE-DITL-20260927_230539_20260927230545`).

---

## 4. Hardware Acquisition Runbook for Future Physical Upgrades

To transition from `HYBRID_VALIDATION` to full `MEASURED_PHYSICAL` when laboratory optical capture equipment becomes available:

1. **Camera Sensor Acquisition:**
   - Connect a dedicated UVC document camera or mirrorless camera (e.g. Sony Alpha A6400 with Cam Link 4K).
   - Ensure camera appears on index `0` or `1` under DirectShow.
2. **Copy Stand & Calibrated Lighting:**
   - Mount camera on a rigid vertical copy stand directly above the display bed.
   - Use dual 5000K CRI 95+ light panels at 45° angles to prevent glare.
3. **Execution Command:**
   - Run `python aegistrace.py device validate` or `python aegistrace.py physical validate`.
   - The discovery engine will automatically detect the camera sensor, perform live optical stream validation, and transition the camera subsystem claim to `MEASURED_PHYSICAL`.
