# AegisTrace (Black Amber) — Official Evaluator Runbook
**Smart India Hackathon 2026** | **Problem Statement ID:** SIH26237  
**Version:** 1.0.0-rc1 | **Date:** September 28, 2026  
**Auditor Classification:** Clean-Room Evaluator / Judge Guide  

---

## 1. System Requirements & Environment Prerequisites

AegisTrace is designed to run self-contained on any standard workstation (Windows 10/11, Ubuntu 20.04+, or macOS 12+):

- **Python Runtime:** Python 3.9, 3.10, 3.11, or 3.12 (64-bit).
- **Node.js Runtime (for Web Frontend):** Node.js 18.x or 20.x with npm.
- **Network Requirement:** **100% Offline Capable.** Zero internet access required after dependencies are installed.
- **Hardware Prerequisites:** Any modern x86_64 or ARM64 multi-core processor with $\ge 4\text{ GB}$ RAM.

---

## 2. Installation & Quick Setup

```bash
# Clone repository (or extract offline bundle)
git clone https://github.com/Kirans-create/black-amber.git
cd black-amber

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. (Optional) Install Frontend dependencies
cd apps/web
npm install
cd ../..
```

---

## 3. Operational Command Reference

### Command 1: Inspect System Runtime & Hardware Baseline
```bash
python aegistrace.py info
```
- **What it does:** Displays system architecture, detected post-quantum algorithms (ML-KEM-768, ML-DSA-65), hardware endpoint discovery, and epistemic boundaries.

### Command 2: Execute Startup Cryptographic & Runtime Self-Tests
```bash
python aegistrace.py selftest
```
- **What it does:** Validates runtime environment, executes KAT (Known Answer Tests) for ML-KEM-768 and ML-DSA-65, verifies AES-256-GCM symmetric ciphers, and checks air-gap socket guards.

### Command 3: Execute Automated Clean-Room Reproduction (< 5.0 Seconds)
```bash
python scripts/reproduce_clean_environment.py
```
- **What it does:** Runs the 6-stage independent reproduction sequence:
  1. Source Tree Integrity (608 files SHA-256 checked)
  2. Startup Self-Tests
  3. 24-Step Multi-Recipient Golden Pipeline
  4. Offline Evidence Package Invariants
  5. Blind Signal Separation & Negative Testing
  6. Composed Red-Team Attack Chains (Chains A–G)

### Command 4: Verify Forensic Evidence Package Completely Offline
```bash
python aegistrace_verify.py artifacts/demo/golden_case/golden_evidence_package.zip
```
- **What it does:** Runs the independent offline verifier. Verifies all 11 cryptographic pillars (Manifest signature, RFC-6962 Merkle commitment, content-addressed digests, dependency DAG, recipient provenance signature, temporal key bound, DLT quorum consensus, watermark binding, lineage integrity, custody chain, attribution decision). Requires zero network access.

### Command 5: Run Full Automated Test Suite (1,098 Tests)
```bash
pytest -q
```
- **What it does:** Executes the complete 1,098-test automated test suite across all crypto, watermark, ledger, format, device, attack, and API modules.

### Command 6: Run Static Secret & Credential Scanner
```bash
python scripts/deployment/scan_secrets.py --strict
```
- **What it does:** Scans all repository source files for accidentally committed credentials, private keys, or API tokens. Exits with 0 when clean.

---

## 4. Launching the Interactive Web Application

### Step 1: Start the Zero-Trust API Server
```bash
# Terminal 1
python aegistrace.py serve --port 8000
```
- API Swagger Documentation available at: `http://localhost:8000/docs`

### Step 2: Build & Start the React Web Dashboard
```bash
# Terminal 2
cd apps/web
npm run build
npm run dev
```
- Access application in browser: `http://localhost:5173`

---

## 5. Clean Demo State Reset

To purge all ephemeral demonstration and runtime data back to a pristine zero-state:

```bash
python scripts/deployment/reset_demo.py
```
- Cleans ephemeral database records in `data/`
- Preserves pre-computed golden demonstration artifacts in `artifacts/demo/`
- Guarantees immediate zero-state compliance
