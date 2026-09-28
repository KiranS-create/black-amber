# AegisTrace (Black Amber) — Submission-Ready Release Candidate Bundle
**Smart India Hackathon 2026** | **Problem Statement ID:** SIH26237  
**Product:** AegisTrace | **Release Version:** 1.0.0-rc1  
**Release Gate Determination:** `READY_WITH_DOCUMENTED_LIMITATIONS`  
**Date:** September 28, 2026  

---

## 1. Overview of Release Candidate Package

This directory (`release_candidate/`) contains the complete evaluator package, operational runbooks, security summaries, and machine-readable manifests for **AegisTrace (Black Amber)**.

All code, cryptographic implementations, and forensic verification tools are self-contained and require zero external cloud or vendor services to evaluate.

---

## 2. Release Candidate Directory Index

| Document / Asset | Purpose & Scope |
| :--- | :--- |
| [`RUNBOOK.md`](file:///C:/Projects/SIH26237/release_candidate/RUNBOOK.md) | Step-by-step evaluator runbook covering environment setup, CLI tools, tests, and API servers. |
| [`DEMO_RUNBOOK.md`](file:///C:/Projects/SIH26237/release_candidate/DEMO_RUNBOOK.md) | Structured 14-step golden forensic demonstration script with expected visual and cryptographic outputs. |
| [`SYSTEM_STATUS.md`](file:///C:/Projects/SIH26237/release_candidate/SYSTEM_STATUS.md) | Current operational, hardware, and epistemic state of all platform subsystems. |
| [`SECURITY_SUMMARY.md`](file:///C:/Projects/SIH26237/release_candidate/SECURITY_SUMMARY.md) | Cryptographic standards inventory, zero-trust boundary architecture, and attack defenses. |
| [`VALIDATION_STATUS.md`](file:///C:/Projects/SIH26237/release_candidate/VALIDATION_STATUS.md) | Authoritative metrics across 1,098 automated tests, frontend builds, and offline verifiers. |
| [`REPRODUCTION.md`](file:///C:/Projects/SIH26237/release_candidate/REPRODUCTION.md) | Independent reproduction instructions for clean-room evaluation environments. |
| [`MANIFEST.json`](file:///C:/Projects/SIH26237/release_candidate/MANIFEST.json) | Cryptographically bound machine-readable release metadata, hashes, and sign-offs. |

---

## 3. Quick Verification Commands

```bash
# 1. Automated Clean-Room Reproduction Suite (< 5.0 seconds)
python scripts/reproduce_clean_environment.py

# 2. Standalone Offline Evidence Verifier (Zero Network Egress)
python aegistrace_verify.py artifacts/demo/golden_case/golden_evidence_package.zip

# 3. Master Test Regression (1,098 Tests, 100% Green)
pytest -q

# 4. Master CLI Demonstration
python aegistrace.py demo
```
