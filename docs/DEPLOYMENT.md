# SIH26237 — Offline Deployment, Reproducibility & Operator Guide

**Document Version**: 1.0.0  
**Status**: Production Deployment & Evaluation Standard  
**Author**: Agent 6: Principal Backend + Systems Integration Engineer  
**Classification**: Offline Systems Architecture & Operational Runbook  

---

## 1. System Overview & Offline Guarantee

SIH26237 is a quantum-resistant cryptographic provenance, traitor-tracing, and fail-closed leak attribution platform. It is engineered to be **100% self-contained and air-gap capable**.

### Offline Invariants:
* **Zero Internet Calls**: Cryptographic key encapsulation (ML-KEM-768), digital signatures (ML-DSA-65), symmetric encryption (AES-256-GCM), and Tardos traitor-tracing run purely in local native code.
* **No Remote Cloud Dependencies**: No cloud inference, SaaS authentication, or remote key-vault connections.
* **No External Database / Message Brokers**: Local SQLite and content-addressed filesystem storage replace PostgreSQL/Redis/Celery.
* **Static Asset Bundling**: All web dashboard styles, fonts, and icons are embedded locally in `apps/web/dist`.

---

## 2. Environment Prerequisites

### 2.1 Hardware Requirements
* **Architecture**: x86_64 / AMD64 or ARM64 (Apple Silicon / Snapdragon).
* **RAM**: Minimum 4 GB (8 GB recommended).
* **Disk Space**: 1 GB free space for repository, virtual environment, and demo data.
* **Operating System**: Windows 10/11 (Native PowerShell / CMD), macOS (12+), or Linux (Ubuntu 20.04+, Debian 11+).

### 2.2 Software Prerequisites
* **Python**: `3.9.0` or newer (Tested on Python 3.9.0 and 3.11).
* **Node.js & npm** *(Optional for UI preview)*: Node.js `>= 18.0.0`, npm `>= 9.0.0` (Tested on Node.js v24.11.0).
* **Git**: `>= 2.30.0`.

---

## 3. Quick Start: One-Command Demo

For evaluators and judges on a clean Windows laptop:

### Windows PowerShell (Recommended)
```powershell
# Open PowerShell in repository root and run:
powershell -ExecutionPolicy Bypass -File .\deployment\start_demo.ps1
```

### Windows Command Prompt (CMD)
```cmd
# Double click or execute:
.\deployment\start_demo.bat
```

### Cross-Platform Python Launcher (Windows / macOS / Linux)
```bash
python scripts/deployment/start_demo.py
```

### What Happens Automatically:
1. Validates Python runtime ($\ge 3.9$) and storage directories.
2. Purges transient artifacts and generates baseline demo fixtures.
3. Spawns FastAPI backend on `http://127.0.0.1:8000`.
4. Spawns React Web Dashboard preview on `http://127.0.0.1:5173`.
5. Executes automated health check and verifies all cryptographic subsystems.
6. Displays interactive service URLs and readiness summary.

---

## 4. Step-by-Step Manual Setup

If you prefer to configure each component step-by-step:

### Step 1: Create and Activate Python Virtual Environment
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS Bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Pinned Dependencies
```bash
pip install --upgrade pip
pip install -r deployment/requirements.txt
```

### Step 3: Initialize Storage & Generate Demo Fixtures
```bash
python scripts/deployment/generate_demo_fixtures.py
```
This generates:
* `data/demo_fixtures/source_document.pdf`: Master classified specification.
* `data/demo_fixtures/recipients.json`: Alice, Bob, Charlie PQC key identities.
* `data/demo_fixtures/release.json`: Multi-recipient encrypted release package.
* `data/demo_fixtures/bob_traceable.pdf`: Bob's decrypted traceable document with ML-DSA-65 signed provenance event.
* `data/demo_fixtures/bob_leak.pdf`: Intercepted leak artifact (100% attributed to Bob).
* `data/demo_fixtures/tampered_leak.pdf`: Corrupted marker carrier (abstains / insufficient evidence).
* `data/demo_fixtures/clean_document.pdf`: Unmarked document (abstains / no signal).
* `data/demo_fixtures/manifest.json`: Cryptographic hash registry and test assertions.

### Step 4: Run Deployment Health Check
```bash
python scripts/deployment/health_check.py
```

### Step 5: Start FastAPI Backend
```bash
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```
* API Base: `http://127.0.0.1:8000`
* Interactive OpenAPI Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
* Health Endpoint: `http://127.0.0.1:8000/health`
* Capabilities Registry: `http://127.0.0.1:8000/capabilities`

### Step 6: Serve Frontend Web Dashboard
```bash
cd apps/web
npx vite build
npx vite preview --port 5173 --host 127.0.0.1
```
* Dashboard URL: `http://127.0.0.1:5173`

---

## 5. Interactive CLI Walkthrough for Judges

To demonstrate the full cryptographic lifecycle from the command line without opening a web browser:

```bash
python scripts/deployment/run_demo_cli.py
```

### Walkthrough Sequence:
1. **Query Capabilities**: Inspects active PQC algorithms (ML-KEM-768, ML-DSA-65) and Tardos parameters.
2. **Master Document Registration**: Ingests `source_document.pdf` into Data Plane storage and computes `ORIGINAL_DOCUMENT_HASH`.
3. **Recipient Enrollment**: Verifies Alice, Bob, Charlie with isolated post-quantum keypairs.
4. **Release Creation**: Encrypts document under ephemeral $K_{\text{doc}}$ and wraps individual envelopes via ML-KEM-768.
5. **Decryption Provenance**: Bob decapsulates package, embeds marker, signs provenance event with ML-DSA-65, and commits record to the tamper-evident ledger.
6. **Leak Analysis**: Intercepted leak evaluated by the Bayesian Evidence Fusion engine $\rightarrow$ Verdict: `ATTRIBUTED` to `Bob` (`HIGH` confidence, 99.0%).
7. **Negative Test**: Tampered carrier evaluated $\rightarrow$ Verdict: `NO_SIGNAL` (`should_abstain: true`).
8. **Ledger Audit**: Full hash-chain verification of the tamper-evident audit trail.

---

## 6. Demo Reset & State Hygiene

To restore the demo to a completely pristine initial state between evaluation sessions:

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\deployment\reset_demo.ps1

# Cross-Platform Python
python scripts/deployment/reset_demo.py
```

### Reset Operations:
1. Purges SQLite database (`data/metadata.sqlite3`).
2. Purges transient Data Plane blobs (`data/artifacts/`).
3. Recreates clean directory structure and regenerates baseline demo fixtures.
4. Leaves user source code and configuration completely untouched.

---

## 7. Containerized Deployment (Docker)

For environments preferring container isolation (e.g. Linux evaluation servers):

### Build and Run via Docker Compose
```bash
docker-compose up --build -d
```

### Direct Docker Run
```bash
docker build -t sih26237:latest .
docker run -p 8000:8000 -v $(pwd)/data:/app/data sih26237:latest
```

### Accessing Containerized Endpoints:
* Backend API: `http://localhost:8000`
* OpenAPI Docs: `http://localhost:8000/docs`

---

## 8. Verification & Test Execution

Run the complete automated test suite (39 tests):

```bash
# Run all unit, integration, and deployment tests
pytest tests/test_api.py tests/test_attribution.py tests/integration tests/deployment -v
```

### Test Coverage Breakdown:
* `tests/test_api.py`: Legacy v0.1 API contract compatibility.
* `tests/test_attribution.py`: Core attribution engine and recipient isolation.
* `tests/integration/**`: Master document lifecycle, multi-recipient release orchestration, synchronous/asynchronous leak analysis, and security hardening.
* `tests/deployment/**`: Deployment health checks, reproducibility invariance tests, and demo fixture validation.

---

## 9. Troubleshooting & Common Questions

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `PSSecurityException: File ... cannot be loaded because running scripts is disabled` | Windows PowerShell script execution policy. | Run with bypass: `powershell -ExecutionPolicy Bypass -File .\deployment\start_demo.ps1` or use `start_demo.bat`. |
| `Port 8000 already in use` | Another process is occupying port 8000. | Stop existing process or set custom port: `set SIH_PORT=8080` (CMD) / `$env:SIH_PORT=8080` (PowerShell). |
| `apps/web/dist not found` | Frontend production bundle has not been compiled. | Run `cd apps/web && npx vite build`. |
| `MIME type unsupported (415)` | Uploaded file magic bytes do not match allowed formats. | Verify uploaded file is a valid PDF (`%PDF-`), PNG, or JPEG. |
| `Capacity Insufficient (400)` | Requested coalition size $c$ requires more carrier symbols than budget. | Increase carrier budget or use recommended default $c=3$. |
