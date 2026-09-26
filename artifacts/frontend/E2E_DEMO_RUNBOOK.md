# SIH26237 — Live Judge Demonstration Runbook & E2E Verification Protocol

**Workstream:** `artifacts/frontend/`  
**Target:** Smart India Hackathon 2026 Evaluation Panel  
**Document Classification:** Interactive Presenter Guide & Protocol  

---

## 1. Pre-Flight Verification Checklist

Before walking up to the judging table:
1. **Screen Resolution:** Verify viewport renders cleanly at 1366x768 (standard laptop) or 1920x1080 (presentation monitor).
2. **Connectivity Status:**
   - If FastAPI server is running on `http://localhost:8000`: Header shows `LIVE BACKEND (:8000)` (Emerald Green).
   - If air-gapped / standalone: Click `Force Offline Mode` in header. Header explicitly shows `OFFLINE SIMULATION (LOCAL DEMO)` (Amber).
3. **Data Plane Ready:** Click `Reset State` to clear any residual test data and restore pristine default demo records.
4. **Browser Fullscreen:** Press `F11` to enter clean kiosk/fullscreen mode.

---

## 2. Fast-Paced Demonstration Tracks

### Track A: The 30-Second Elevator Pitch

| Time | Presenter Action | What Judge Sees | Live vs. Simulated | Expected Backend State |
| :--- | :--- | :--- | :--- | :--- |
| **0:00 - 0:10** | Open Dashboard & point to Post-Quantum Envelope flowchart. | High-level 4-step pipeline: Enrolment (ML-KEM/DSA) $\rightarrow$ Envelope Release $\rightarrow$ Signed Decryption Provenance $\rightarrow$ Bayesian Leak Attribution. | Live UI | `GET /health` returns 200 OK with registered document and ledger counts. |
| **0:10 - 0:20** | Click **"Start Judge Walkthrough"** $\rightarrow$ Step 5 ("Multi-Channel Leak Attribution"). | Ingests leaked document; computes Bayesian Log-Likelihood Ratio ($\text{LLR} = 18.08$); attributes Bob Martinez with high confidence and separation margin $\Delta = 18.08$. | Live / Sim | `POST /analyze` returns candidate attribution and multi-channel breakdown. |
| **0:20 - 0:30** | Advance to Walkthrough Step 6 ("Adversarial Robustness"). | Shows adversarial tests (forged HMAC tokens, frame attacks, raw unwatermarked files). Highlights that system strictly returns `ABSTAIN` rather than falsely accusing innocent recipients. | Live / Sim | Engine returns fail-closed state (`NO_SIGNAL`, `INSUFFICIENT_EVIDENCE`). |

---

### Track B: The 2-Minute Live Demo

| Time | Stage / Tab | Presenter Click Action | What Judge Sees | Live vs. Simulated | Backend Contract |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0:00 - 0:20** | **1. Enrolment** (`Recipients` tab) | Click on Alice, Bob, and Charlie in the registry. | Isolated Post-Quantum keypairs (`ML-KEM-768` for encapsulation, `ML-DSA-65` for provenance signatures). Key isolation boundary highlighted. | Live / Sim | `GET /recipients` or `POST /recipients` |
| **0:20 - 0:45** | **2. Release** (`Release` tab) | Select "National Defense Protocol 2026.pdf", select Alice, Bob, and Charlie, click **"Create Release Package"**. | Single AES-256-GCM encryption with 3 recipient-specific ML-KEM-768 capsules. Distinct `ORIGINAL_DOCUMENT_HASH` vs `RELEASE_ARTIFACT_HASH`. | Live / Sim | `POST /releases` |
| **0:45 - 1:10** | **3. Decryption** (`Decrypt` tab) | Select Bob Martinez, click **"Decrypt as Bob"**. | Client decapsulates key, verifies AES-GCM tag, embeds watermark marker, and signs an immutable `DECRYPTION_EVENT` using Bob's ML-DSA-65 key. Provenance badge turns GREEN (`RECIPIENT-SIGNED / VERIFIED`). | Live / Sim | `POST /releases/{id}/decrypt` + `POST /releases/{id}/provenance` |
| **1:10 - 1:35** | **4. Ledger** (`Ledger` tab) | Click **"Verify Chain"**, then click **"Simulate Local Ledger Tamper"** on Block #2. | Live chain verifies 100% valid. Upon tampering, SHA-256 hash-chain breaks immediately, turns RED (`TAMPER DETECTED`), and localizes corrupted block. | Real Computation | `GET /ledger/verify` or Client SHA-256 recalculation |
| **1:35 - 2:00** | **5. Leak Attribution** (`Leak Analysis` tab) | Click **"Clean Digital Leak (Bob)"**, then **"Execute Bayesian Evidence Fusion"**. | Multi-channel breakdown: Watermark ($RS(42,26)$), Tardos ($Z_i = 8.42$), Signature (ML-DSA-65), and Ledger link. Positive match for Bob Martinez. | Live / Sim | `POST /analyze` |

---

### Track C: The 5-Minute Technical Deep-Dive

| Time | Topic / Module | Presenter Choreography | Technical Nuances to Highlight |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:45** | **Post-Quantum Cryptography** (`Recipients` & `Release`) | Walk through ML-KEM-768 key exchange (1184-byte public key) and AES-256-GCM envelope encryption with HKDF domain separation. | Explain why we encrypt once and encapsulate per-recipient rather than creating 3 duplicate ciphertext blobs. Show hash isolation. |
| **0:45 - 1:30** | **Decentralized Provenance Model** (`Decrypt` & `Ledger`) | Decrypt as Bob. Point out that the client signs the provenance event, and the server verifies the ML-DSA-65 signature before ledger ingestion. | Explain non-repudiation: Server cannot forge recipient signatures; recipient cannot deny decryption once signed event is chained on the ledger. |
| **1:30 - 2:30** | **Cryptographic Tamper-Evidence** (`Ledger` tab) | Inspect the SHA-256 chaining formula: $\text{Event Hash} = \text{SHA256}(\text{prev\_hash} \parallel \text{event\_id} \parallel \text{art\_hash} \parallel \text{sig})$. Run the tamper simulator. | Show that retroactively modifying historical access logs breaks the mathematical chain tip immediately. |
| **2:30 - 3:30** | **Tardos Traitor-Tracing ($m=128$)** (`Tardos` tab) | Toggle users in and out of the collusion coalition ($c \le 3$). Show continuous correlation scores $Z_i$ and the Gaussian accusation threshold $\tau_Z = 6.50$. | Emphasize statistical honesty: $Z_i$ is a continuous Gaussian correlation score with Blayer-Tassa bounded false alarm ($\epsilon_1 \le 10^{-4}$), not a generic percentage. |
| **3:30 - 4:15** | **Adversarial Attack Lab** (`Attack Lab` tab) | Run "Physical Print-Camera Smartphone Photograph". Show OpenCV homography rectification with Barker-13 sync and RS error correction. | Show physical vs simulated telemetry badges. Highlight PSNR, SSIM, and Bit Error Rate (BER) recovery. |
| **4:15 - 4:45** | **Multi-Channel Contradiction & Fail-Closed** (`Leak Analysis` tab) | Select "Multi-Channel Contradiction (Tardos: Bob, Watermark: Charlie)". Run analysis $\rightarrow$ Result is `CONFLICT` ($\text{ABSTAIN}$). | Show that when independent channels contradict, the system strictly refuses to pick the highest score and enforces fail-closed abstention. |
| **4:45 - 5:00** | **Technical Dossier Export** | Click **"Export Technical Evidence Dossier"**. | Review the complete cryptographic chain of custody, raw SHA-256 hashes, and verifiable PQC signatures ready for audit. |

---

## 3. Failure Modes & Instant Recovery Runbook

| Failure Mode | Symptom | Immediate Presenter Action (No Rebuild Required) |
| :--- | :--- | :--- |
| **Backend Unreachable** | Header shows `BACKEND UNREACHABLE` or red offline status. | Toggle **"Force Offline Mode"** in the top header. The app immediately shifts into deterministic offline simulation without reloading or dropping state. |
| **Stale Demo Database / Corrupted State** | Unexpected documents or duplicate recipients appear. | Click the **"Reset State"** button (RotateCcw icon) in the header. Restores standard Alice/Bob/Charlie state and clean mock ledger. |
| **Port Collision / 3000 Occupied** | Vite dev server runs on another port (e.g. 5173). | Access `http://localhost:5173`. Frontend is completely port-agnostic. |
| **Malformed Uploaded File** | Uploading an unsupported file type or corrupted binary. | System gracefully catches error and displays inline notification; simply select one of the built-in deterministic scenarios on the left. |
| **Ledger Tampered State Persistent** | Ledger shows `TAMPER DETECTED` after demonstration. | Click **"Reset Tamper Simulation"** in the Ledger tab to restore chain integrity. |
| **Contradictory Evidence Demonstration** | Judge asks "what if one marker says Bob and another says Charlie?" | Select scenario **`Multi-Channel Contradiction (Tardos: Bob, Watermark: Charlie)`** in Leak Analysis. Demonstrates immediate `CONFLICT` abstention. |
