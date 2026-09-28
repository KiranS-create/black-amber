# AegisTrace Hosted Demo Runbook (SIH26237)

> **Platform Designation**: AegisTrace (Black Amber)  
> **Evaluation Mode**: Smart India Hackathon 2026 Jury Demonstration  
> **Platform Status**: Web Workstation & Independent Offline Auditor. Standalone desktop packaging (Windows `.exe`, macOS `.dmg`) and Android mobile packaging are **DEFERRED TO FUTURE WORKSTREAM**.

---

## 1. Quick Access & Credentials

| Parameter | Details |
|---|---|
| **Public URL** | [Render Web Service](https://aegistrace.onrender.com) / [Live Quick Tunnel](https://joan-enforcement-whatever-looks.trycloudflare.com) |
| **Demo Username** | `admin` |
| **Demo Password** | `admin` |
| **Tenant Isolation** | `demo_tenant` (Strictly segregated from production state) |
| **Autofill Helper** | Dedicated **Autofill** button on login screen |
| **Offline Auditor** | Accessible via bottom link: **Open AegisTrace Verify (Zero-Server) →** |

---

## 2. End-to-End Evaluation Workflow (Under 3 Minutes)

The demonstration allows evaluators to execute the complete post-quantum document security and forensic leak attribution lifecycle:

```
           1. Authenticate (admin / admin)
                         │
                         ▼
        2. View Isolated Demo Workspace (DEMO DATA)
                         │
                         ▼
    ┌────────────────────┴────────────────────┐
    │                                         │
    ▼                                         ▼
3. Investigate Leak Benchmark          4. Standalone Verification
   (Clean Digital Leak - Bob)             (AegisTrace Verify)
   • 4 Detection Channels                 • Ingest Golden Package -> VERIFIED
   • Bayesian Posterior LLR +18.08        • Ingest Tampered Package -> FAILED
   • Dirichlet Priors [Details]           • 12 Forensic Cryptographic Pillars
    │                                         │
    └────────────────────┬────────────────────┘
                         │
                         ▼
           5. Audit Ledger & Provenance Chain
                         │
                         ▼
           6. Sign Out / Reset Demonstration
```

### Step 1: Sign In
1. Navigate to the public URL.
2. In the **DEMO ACCESS** card, click **Autofill** (or enter `admin` / `admin`).
3. Click **Sign in**. Notice the amber **DEMO DATA** badge confirming you are inside `demo_tenant`.

### Step 2: Investigate Pre-Loaded Adversarial Leak
1. In the sidebar, click **Investigations**.
2. Select benchmark scenario: **Clean Digital Leak (Bob Martinez)**.
3. Observe real-time multi-channel evidence fusion:
   - **Spatial DSSS Demodulation**: Carrier match detected ($z = 4.82$).
   - **Tardos Fingerprint**: Recipient codeword correlation ($\Delta = 18.08$).
   - **Digital Signature**: Valid ML-DSA-65 post-quantum signing identity.
   - **Immutable Ledger**: Matching decryption provenance block verified.
4. **Bayesian Verdict**: Leak attributed to **Bob Martinez** (`bob`) with log-likelihood ratio $+18.08$ (threshold $\Delta \ge 2.50$).
5. Click **[ Technical details ]** to view the Dirichlet priors, LLR breakdown, and Merkle tree root hash.

### Step 3: Verify Offline Evidence Package
1. In the sidebar, click **AegisTrace Verify** (or open it unauthenticated from the login footer).
2. Drag & drop the golden evidence package: `artifacts/demo/golden_case/golden_evidence_package.zip`.
3. **Verdict**: **PACKAGE VERIFIED** (Emerald banner).
   - All 12 forensic pillars confirmed valid (Manifest signature, Merkle root RFC-6962, Object hashes SHA-256, DAG acyclicity, Chain of custody, Temporal keys).
4. Click **[ Technical details ]** to inspect individual commitment checks.

### Step 4: Tamper Demonstration
1. Upload a corrupted or tampered zip package (`artifacts/demo/tampered_evidence_package.zip`).
2. **Verdict**: **VERIFICATION FAILED** (Crimson banner).
3. The cryptographic verifier immediately detects the anomaly (*"Package corruption or tamper detected"*), setting all 6 pillar indicators to `INVALID`. Zero false-positive acceptances.

### Step 5: Sign Out & Tenant Reset
1. Click the user profile icon in the top right -> click **Sign out of workstation**.
2. To reset synthetic demo records, click **[ Clear demo data ]** in the top bar before signing out.

---

## 3. Free Hosting Characteristics & Cold-Start Behavior

Render free tier instances operate under specific operational constraints:

| Behavior | Characteristic | Operational Impact | Mitigation |
|---|---|---|---|
| **Idle Timeout** | 15 minutes of inactivity | Container enters sleep mode to conserve free-tier compute | Normal behavior on free tier |
| **Cold Start** | ~30 to 50 seconds | First HTTP request after idle initiates container boot | Wait ~40s on first load or use keepalive ping |
| **Warmed Latency** | `< 600 ms` | Once warmed, all API requests and verification execute sub-second | Warmed container responds immediately |
| **Filesystem** | Ephemeral container storage | Local SQLite and upload scratch spaces reset on redeploy | Demo fixtures are pre-baked in container image |
| **Keepalive** | Free HTTP monitor | Ping `GET /ready` every 10 min (e.g., via Cron-Job.org) | Prevents container sleeping during evaluation |

---

## 4. Reset & Recovery Procedures

### Resetting Demonstration State
- **UI Reset**: Click **[ Clear demo data ]** in the dashboard banner or click **Reset State** in the top header.
- **API Reset**: Issue an authenticated POST request to reset the demo tenant:
  ```bash
  curl -X POST https://<your-service>.onrender.com/demo/reset \
    -H "Authorization: Bearer token_demo_admin"
  ```

### Redeployment & Rollback
- If a build fails or container requires a clean restart, trigger manual deploy in Render Dashboard:
  **Manual Deploy** -> **Clear build cache & deploy**.
- Container uses multi-stage Docker build guaranteeing deterministic compilation of Node 20 frontend and Python 3.11 backend.
