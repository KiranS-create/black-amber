# SIH26237 — Master Presentation & Competition Defense Runbook

**Title:** Post-Quantum Leak Attribution for Documents: From Encrypted Release to Physical-Capture Traceability  
**Project:** SIH26237 — Secure Document Distribution, Post-Quantum Provenance & Robust Leak Attribution  
**Classification:** Competition Presentation & Live Demonstration Standard  
**Version:** 1.0.0  
**Status:** GREEN & Competition Ready  

---

## 1. Executive Summary

This runbook defines the master presentation, speaker delivery guidelines, live demonstration scripts, technical judge defense strategies, and empirical benchmarks for **SIH26237**.

The presentation is built around a single, coherent technical story:
```
PROTECT (ML-KEM-768 Envelope)
   ↓
RECIPIENT-SPECIFIC RELEASE (Alice, Bob, Charlie)
   ↓
AUTHORIZED DECRYPTION (ML-DSA-65 Signed Provenance)
   ↓
RECIPIENT-SPECIFIC FINGERPRINT (Symmetric Tardos Code)
   ↓
WATERMARK / PHYSICAL CARRIER (ArUco Fiducials + DSSS + Reed-Solomon)
   ↓
LEAK OCCURS (Smartphone Photo / Screen Capture)
   ↓
ATTACK / DEGRADATION (Blur, Tilt, Compression, Cropping)
   ↓
SIGNAL RECOVERY (Perspective Homography Rectification + Demodulation)
   ↓
TARDOS TRACEABILITY (Continuous Likelihood Scoring)
   ↓
MULTI-CHANNEL EVIDENCE FUSION (Transitive Derivation Lineage Anti-Double-Counting)
   ↓
FAIL-CLOSED VERDICT (ATTRIBUTED / CONFLICT / ABSTAIN)
```

---

## 2. Presentation Package Structure

The presentation suite consists of five coordinated deliverables:

| File / Component | Purpose | Primary Target Audience |
| :--- | :--- | :--- |
| [`presentation/slides.md`](file:///C:/Projects/SIH26237/presentation/slides.md) | 11-Slide Master Markdown Presentation Deck | Competition Judges & Panelists |
| [`presentation/index.html`](file:///C:/Projects/SIH26237/presentation/index.html) | Standalone Interactive Cyber-Defense HTML Presentation Deck | Live Presenter on Local Laptop |
| [`presentation/SPEAKER_NOTES.md`](file:///C:/Projects/SIH26237/presentation/SPEAKER_NOTES.md) | Slide-by-slide speaker delivery script and timing cues | Presenter & Backup Speaker |
| [`presentation/architecture_diagram.mermaid`](file:///C:/Projects/SIH26237/presentation/architecture_diagram.mermaid) | Complete Mermaid syntax architecture flowchart | Architecture Evaluators |
| [`artifacts/presentation/DEMO_SCRIPT.md`](file:///C:/Projects/SIH26237/artifacts/presentation/DEMO_SCRIPT.md) | 30-sec, 2-min, 5-min, and Deep-Dive demo scripts | Live Demonstration Lead |
| [`artifacts/presentation/PRESENTER_CHECKLIST.md`](file:///C:/Projects/SIH26237/artifacts/presentation/PRESENTER_CHECKLIST.md) | Pre-flight verification checklist and failsafe playbook | Presenter (T-15 mins) |
| [`artifacts/presentation/JUDGE_QA.md`](file:///C:/Projects/SIH26237/artifacts/presentation/JUDGE_QA.md) | 15+ rigorous, technically honest judge defense answers | Team Q&A Responders |
| [`research/presentation/NOVELTY_STATEMENT.md`](file:///C:/Projects/SIH26237/research/presentation/NOVELTY_STATEMENT.md) | Defensible prior art and systems novelty analysis | Intellectual Property / Academic Judges |
| [`scripts/demo/run_live_demo.py`](file:///C:/Projects/SIH26237/scripts/demo/run_live_demo.py) | Automated interactive multi-scenario CLI live demonstration | Live Demo Operator |

---

## 3. Slide-by-Slide Outline & Visual Structure

```
+--------------------------------------------------------------------------------------------------+
| SLIDE 1: Title & Value Proposition      | SLIDE 2: The Physical Leakage Boundary Problem        |
| - NIST ML-KEM / ML-DSA Trust Layer      | - DRM fails when authorized user renders pixels       |
| - Tardos Traitor-Tracing + DSSS         | - The Analog Hole & smartphone camera capture         |
| - Fail-Closed Zero-Trust Decision       | - Shared symmetric keys vs individualized releases    |
+-----------------------------------------+--------------------------------------------------------+
| SLIDE 3: Threat Model Matrix            | SLIDE 4: End-to-End System Architecture                |
| - 6 Attacker Personas & Defense Layers  | - Complete workflow: Protect -> Release -> Provenance  |
| - Collusion, Tampering, Replay defense  |   -> Tardos -> Watermark -> Recovery -> Fusion -> Exit |
+-----------------------------------------+--------------------------------------------------------+
| SLIDE 5: Cryptographic Trust Layer      | SLIDE 6: Tardos Traitor-Tracing & Physical Carrier     |
| - NIST FIPS 203 (ML-KEM-768): 11.6ms    | - Tardos (WHO): Capacity-planned collusion resistance  |
| - NIST FIPS 204 (ML-DSA-65): 20.9ms     | - Watermark (HOW): ArUco homography + DSSS + RS ECC    |
| - Sovereign Recipient Key Custody       | - Simulated vs Physical validation status              |
+-----------------------------------------+--------------------------------------------------------+
| SLIDE 7: Adversarial Attack Laboratory  | SLIDE 8: Evidence Fusion & Anti-Double-Counting        |
| - Digital, geometric, PDF, optical tests| - The forensic trap of naively summing derived scores  |
| - Destruction triggers clean abstention | - Transitive lineage bounding: max(Score_WM, Tardos)   |
|                                         | - 5 Explicit Courtroom-Defensible Decision States      |
+-----------------------------------------+--------------------------------------------------------+
| SLIDE 9: Turnkey Live Demo Workflow     | SLIDE 10: Measured Benchmarks & Telemetry              |
| - 8-step live walkthrough sequence      | - Real numbers from benchmark scripts                  |
| - Live UI vs Deterministic vs Fallback  | - Scientific explanation of 74% held-out eval rate     |
+-----------------------------------------+--------------------------------------------------------+
| SLIDE 11: Boundaries & Conclusion                                                                |
| - Honest boundaries: physical printing validation, heuristic parameter scaling                   |
| - Closing axiom: "Designed to attribute when strong — and fail-closed when it is not."           |
+--------------------------------------------------------------------------------------------------+
```

---

## 4. Live Demonstration Execution Tiers

### **Tier 1: Live Interactive Web UI (`http://127.0.0.1:5173`)**
- Start with `.\deployment\start_demo.ps1` (or `deployment\start_demo.bat`).
- Shows full visual dashboard, real-time leak uploads, evidence graph breakdowns, and ledger verification.

### **Tier 2: Interactive Terminal Demonstration (`python scripts/demo/run_live_demo.py`)**
- Step-by-step interactive CLI runner with color-coded log stages, latency telemetry, and explicit decision breakdowns.

### **Tier 3: Rapid Automated Headless Test (`python scripts/demo/run_quick_demo.py`)**
- 30-second automated execution verifying all three baseline scenarios:
  1. Ground-truth leak $\to$ `ATTRIBUTED` (Bob).
  2. Severely tampered leak $\to$ `INSUFFICIENT_EVIDENCE` / `CONFLICT`.
  3. Untracked clean document $\to$ `NO_SIGNAL`.

---

## 5. Summary of Key Repository Telemetry

All metrics presented to judges are grounded in real automated benchmark artifacts:

| Domain | Benchmark Metric | Measured Performance | Primary Source File |
| :--- | :--- | :--- | :--- |
| **Cryptography** | `ML-KEM-768` Encapsulation | **11.61 ms** | [`artifacts/integration/latency_benchmark.json`](file:///C:/Projects/SIH26237/artifacts/integration/latency_benchmark.json) |
| **Cryptography** | `ML-DSA-65` Signature Verify | **20.97 ms** | [`artifacts/integration/latency_benchmark.json`](file:///C:/Projects/SIH26237/artifacts/integration/latency_benchmark.json) |
| **Watermarking** | Geometric Sync + Demodulation | **62.81 ms** | [`research/physical/SIMULATED_RESULTS.md`](file:///C:/Projects/SIH26237/research/physical/SIMULATED_RESULTS.md) |
| **Watermarking** | False Accusation on Negatives | **0.0% (0 / 50)** | [`research/physical/SIMULATED_RESULTS.md`](file:///C:/Projects/SIH26237/research/physical/SIMULATED_RESULTS.md) |
| **Fusion Evaluation** | Held-Out Evaluation Match Rate | **74.0%** (74 / 100) | [`artifacts/evidence-fusion/calibration_vs_evaluation.json`](file:///C:/Projects/SIH26237/artifacts/evidence-fusion/calibration_vs_evaluation.json) |
| **Fusion Evaluation** | False Accusations on Negatives | **0.0% (0 / 35)** | [`artifacts/evidence-fusion/confusion_matrix.json`](file:///C:/Projects/SIH26237/artifacts/evidence-fusion/confusion_matrix.json) |
| **Deployment** | Turnkey Demo Reset Latency | **349.11 ms** | [`artifacts/deployment/startup_benchmark.json`](file:///C:/Projects/SIH26237/artifacts/deployment/startup_benchmark.json) |
| **Deployment** | Integration Test Suite Pass Rate | **39 / 39 (100%)** | `pytest tests/` |
