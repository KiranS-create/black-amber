# AegisTrace Physical Channel Forensic Limitations & Operational Boundaries

## 1. Scope & Purpose
Forensic attribution from physical and optical leak artifacts (screen photographs, prints, scans) is subject to fundamental physical and information-theoretic boundaries. This document articulates the verified operational envelope, safe boundary limits, and fail-closed security guarantees enforced by AegisTrace.

---

## 2. Safe Operational Envelope vs. Failure Boundaries

| Physical Parameter | Recommended Safe Envelope | Empirical Failure Boundary | Beyond Boundary Behavior |
| :--- | :--- | :--- | :--- |
| **Perspective Capture Angle** | $0^\circ \text{ to } 20^\circ$ | $> 25^\circ \text{ to } 35^\circ$ | Geometric synchronizer fails closed (`NO_SIGNAL`). Zero false attribution. |
| **Capture Distance** | $25\text{ cm to } 45\text{ cm}$ | $> 50\text{ cm to } 80\text{ cm}$ | High-frequency carrier detail lost (`NO_SIGNAL`). Zero false attribution. |
| **Optical Defocus / Motion Blur** | $\sigma \le 1.0$ (Gaussian) | $\sigma > 1.4$ | ArUco detection failure or uncorrectable RS errors (`INSUFFICIENT_EVIDENCE`). |
| **Ambient Lighting Variations** | $-20\% \text{ to } +30\%$ | $< -50\% \text{ or } > +80\%$ | Extreme clipping destroys carrier modulation (`NO_SIGNAL`). |
| **Fiducial Occlusion** | 4 of 4 corners intact | $< 3 \text{ corners intact}$ | Homography estimation impossible (`INSUFFICIENT_EVIDENCE`). |
| **JPEG Recompression Quality** | $Q \ge 60$ | $Q < 30$ | High-frequency spatial carrier quantized to zero (`NO_SIGNAL`). |

---

## 3. Epistemic Invariants & Courtroom Defensibility

### A. Strict Anti-False-Attribution Invariant
When optical degradation exceeds the operational envelope, the system **MUST FAIL CLOSED**:
$$\text{Decision} \in \{\text{NO\_SIGNAL}, \text{INSUFFICIENT\_EVIDENCE}, \text{CONFLICT}, \text{UNATTRIBUTED}\}$$
Under no circumstances will degraded or random noise produce a false positive attribution.

### B. Downstream Leak Transition Honesty (`LAST_KNOWN_HOLDER`)
When physical documents are leaked to an unmonitored downstream recipient (e.g., physical handover from Alice to an uncredentialed accomplice), the system refrains from fabricating downstream identities:
$$\text{DecisionState} = \text{INSUFFICIENT\_EVIDENCE}, \quad \text{last\_known\_holder} = \text{rec\_alice}, \quad \text{attributed\_principal} = \text{None}$$
This boundary preservation is vital for courtroom cross-examination and strict scientific defensibility.
