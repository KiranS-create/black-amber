# Getting Started with AegisTrace

> **System Designation**: AegisTrace (Code Name: Black Amber)  
> **Smart India Hackathon 2026**: SIH26237 — Cryptographic Attribution and Immutable Decryption Provenance for Multi-Recipient Encrypted Document Distribution  
> **Platform Status**: Production Web Workstation & Standalone Offline Auditor. Standalone desktop applications (Windows `.exe`, macOS `.dmg`) and Android mobile applications are **DEFERRED TO FUTURE WORKSTREAM**.

---

## 1. Quickstart (Under 3 Minutes)

You can launch and evaluate AegisTrace on any workstation in three minutes:

```bash
# 1. Clone repository and navigate to root
git clone <repository_url>
cd SIH26237

# 2. Launch containerized workstation
docker compose up -d

# 3. Open workstation in your web browser
# Navigate to: http://localhost:8000
```

Alternatively, if running directly with Python and Node:
```bash
# Terminal 1: Backend
pip install -r deployment/requirements-lock.txt
python -m uvicorn apps.api.main:app --port 8000

# Terminal 2: Frontend
cd apps/web && npm install && npm run dev
# Navigate to: http://localhost:5173
```

---

## 2. Authentication & SIH Judge Evaluation

AegisTrace provides two operational modes:

### 2.1 Demonstration Evaluation (SIH Judges)
When `DEMO_AUTH_ENABLED=true` in your `.env`:
- **Username**: `admin`
- **Password**: `admin`
- Click the single-click **Autofill** button on the login screen.
- A prominent yellow **DEMO DATA** badge confirms you are operating in an isolated demonstration sandbox.
- Click **[ Clear demo data ]** at any time to purge synthetic records.

### 2.2 Production Forensic Workspace
When `DEMO_AUTH_ENABLED=false`:
- The workspace initializes **completely empty** (Zero Fake Data).
- Default administrative credentials (`admin/admin`) are strictly rejected with HTTP 401.
- Authentication enforces rate limiting and cryptographic session tokens.
- User accounts are provisioned via administrative identity federation.

---

## 3. Product Intuition: The Forensic Car Analogy

AegisTrace hides military-grade post-quantum cryptography, traitor tracing, and Bayesian inference behind simple, intuitive operational controls:

| Human Action (Steering Wheel) | Deep Cryptographic Implementation (Engine) |
|---|---|
| **Import artifact** | Canonical SHA-256 digest computation, content addressing, classification tagging |
| **Protect & Distribute** | NIST FIPS 203 (ML-KEM-768) encapsulation, AES-256-GCM AEAD payload encryption, Tardos fingerprinting code matrix generation |
| **Recipient Decrypts** | Kyber decapsulation, recipient-bound spatial DSSS watermarking, ML-DSA-65 signed provenance event appended to immutable Merkle hash chain |
| **Investigate leak** | Signal demodulation, Bayesian Log-Likelihood Ratio (LLR) multi-channel fusion, anti-double-counting DAG |
| **Verify package** | Standalone zero-server audit of ML-DSA-65 signatures, RFC 6962 Merkle tree consistency, and custody chain |
| **Export dossier** | Sealed `.zip` evidence archive with canonical `manifest.json` and verification telemetry |

---

## 4. Standalone AegisTrace Verify (Zero-Server)

If you are a judicial examiner, external auditor, or defense counsel receiving an evidence package:
1. You do **not** need an AegisTrace account or running server.
2. From the login screen, click **"Open AegisTrace Verify (Zero-Server) →"**.
3. Drag and drop any sealed `.zip` package or `manifest.json`.
4. The offline engine performs a comprehensive mathematical audit and reports **PACKAGE VERIFIED** or **VERIFICATION FAILED** with verifiable cryptographic telemetry.
