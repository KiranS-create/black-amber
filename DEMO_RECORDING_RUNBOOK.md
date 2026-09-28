# AegisTrace — Official Demo Recording Runbook
**Product:** AegisTrace (Internal Code Name: *Black Amber*)  
**Problem Statement ID:** SIH26237  
**Version:** 1.0.0-production  
**Purpose:** Standardized scene-by-scene script for recording a high-fidelity, glitch-free demonstration video for Hackathon evaluation.  

---

## Pre-Recording Checklist

1. **Resolution & Scaling:** Set display to 1920x1080 (100% DPI scaling).
2. **Browser:** Use Google Chrome or Chromium in Fullscreen (`F11`) with bookmarks and extension icons hidden.
3. **Audio:** High-quality microphone with noise suppression enabled.
4. **Environment Reset:** Before recording, execute a clean reset so the database starts in authentic zero-state:
   ```bash
   python aegistrace.py demo reset
   ```
5. **Services Running:**
   * Backend: `python aegistrace.py serve`
   * Frontend: `cd apps/web && npm run dev`

---

## Scene-by-Scene Recording Script

### Scene 1: Sovereign Cold-Start & Authentication (0:00 – 0:35)
* **Visual:** Browser opens to `http://localhost:5173`. The clean "Forensic Luxury" login screen appears.
* **Narration:**
  > "Welcome to AegisTrace, built for Smart India Hackathon problem statement SIH26237. AegisTrace is an air-gapped, post-quantum cryptographic platform designed for sovereign defense networks to solve traitor tracing and verifiable decryption provenance."
* **Action:**
  1. Highlight the algorithm tags: **NIST FIPS 203 ML-KEM-768** and **NIST FIPS 204 ML-DSA-65**.
  2. Click **"Use Demo Credentials"** (populates `admin` / `admin`).
  3. Click **"Sign In"**.

---

### Scene 2: Production Clean State & Subsystem Diagnostics (0:35 – 1:15)
* **Visual:** Dashboard loads. Point out that all data collections start in an authentic empty state.
* **Narration:**
  > "Unlike traditional demonstration dashboards that pre-populate fake data, AegisTrace enforces strict production-vs-demo separation. Notice that initial cold-start contains zero fictional documents, zero fake recipients, and zero synthetic ledger blocks."
* **Action:**
  1. Click the **Diagnostics / System Health** tab.
  2. Highlight the KPI card: **1,098 Passing Tests** verified across PQC, Watermarking, Ledger, Attribution, and Web layers.
  3. Point out operational latencies: KEM decapsulation under 4.2ms, digital signature generation under 8.6ms.

---

### Scene 3: Master Document Registration & Recipient Enrollment (1:15 – 2:00)
* **Visual:** Switch to **Documents** tab, then **Recipients** tab.
* **Narration:**
  > "Let's load the isolated demo scenario. In the top bar, we click 'Load Demo Fixtures'. Instantly, authorized defense officers Alice, Bob, and Charlie are enrolled into our cryptographic key registry."
* **Action:**
  1. Click **"Load Demo Fixtures"** in the top bar.
  2. Show Bob's recipient card: display the enrolled **1,184-byte ML-KEM-768 public key** and **1,952-byte ML-DSA-65 public key**.
  3. Explain that key pairs are stored locally on the client's sovereign device, never centralized in a vulnerable server database.

---

### Scene 4: Broadcast Release with Post-Quantum Key Encapsulation (2:00 – 2:45)
* **Visual:** Switch to **Release** tab.
* **Narration:**
  > "When Headquarters issues a classified directive, we do not perform inefficient pairwise encryption. Instead, AegisTrace generates an ephemeral 256-bit document key, encrypts the payload once via AES-256-GCM, and encapsulates the key under each recipient's ML-KEM-768 public key using RFC 3394 key wrapping."
* **Action:**
  1. Point out the active release for **Strategic Defense Directive**.
  2. Highlight the 3 isolated cryptographic capsules bound to Alice, Bob, and Charlie.
  3. Note that zero plaintext leaks occur during broadcast distribution.

---

### Scene 5: Client-Side Decapsulation & Dynamic Watermarking (2:45 – 3:30)
* **Visual:** Switch to **Decryption Provenance** tab.
* **Narration:**
  > "Now, Officer Bob opens his secure terminal to read the directive. Bob decapsulates the ML-KEM ciphertext. At the exact millisecond of decryption, AegisTrace embeds an invisible 2D DSSS watermark into the rendered document, dynamically binding Bob's recipient ID, session context, and hardware device. Simultaneously, Bob's client signs an ML-DSA-65 decapsulation receipt, committing it to our immutable ledger."
* **Action:**
  1. Show Bob's traceable document preview.
  2. Highlight the **Decryption Receipt Event ID** and the **ML-DSA-65 Digital Signature** hash.
  3. Note that Bob cannot deny opening the file—cryptographic non-repudiation is strictly enforced.

---

### Scene 6: Leak Ingestion & Fail-Closed Forensic Attribution (3:30 – 4:30)
* **Visual:** Switch to **Investigations** tab.
* **Narration:**
  > "Suppose this document is photographed or leaked online. In our Investigations console, we ingest the suspect artifact. AegisTrace extracts the watermark carrier through 4-point RANSAC homography rectification and Reed-Solomon error correction, then executes Bayesian multi-channel evidence fusion."
* **Action:**
  1. Click **"Evaluate benchmark: Clean digital leak"**.
  2. Point out the **Presentation State Ribbon**: `VERIFIED` with candidate Bob identified.
  3. Highlight the **Hardware Modality Status Cards**:
     * `Device-in-loop: Verified`
     * `Camera Capture: Not verified` (explaining that headless environment avoids fake camera claims)
     * `Physical Printer: Unavailable`
     * `Flatbed Scanner: Unavailable`
  4. Show the multi-channel score breakdown (+21.4 LLR, exceeding the theoretical cutoff of $Z=11.4$).

---

### Scene 7: Negative Baseline & Fail-Closed Abstention (4:30 – 5:15)
* **Visual:** In Investigations tab, click **"No watermark"** benchmark.
* **Narration:**
  > "What happens if an investigator uploads an unwatermarked document or a document with an obliterated signal? Watch closely: AegisTrace changes state to 'INSUFFICIENT EVIDENCE' and abstains. The system never forces an attribution, guaranteeing that innocent personnel are never falsely accused."
* **Action:**
  1. Point out the `INSUFFICIENT EVIDENCE` badge.
  2. Point out `Candidate: None` and `Should Abstain: True`.

---

### Scene 8: Tamper-Evident Ledger & Live Attack Simulation (5:15 – 6:00)
* **Visual:** Switch to **Audit Ledger** tab.
* **Narration:**
  > "Every provenance event is chained in a permissioned BFT ledger with SHA-256 parent block pinning. What if an adversary attempts to modify historical logs in the database?"
* **Action:**
  1. Click **"Simulate Tamper"** in the top bar.
  2. Show how the ledger instantly detects the broken hash chain at Block #1 with an explicit cryptographic alert.
  3. Click **"Reset Chain"** to restore verifiable continuity.

---

### Scene 9: Cryptographic Evidence Dossier & Offline Verification (6:00 – 6:45)
* **Visual:** Return to Investigations tab and click **"Export evidence dossier"**.
* **Narration:**
  > "For court presentation or air-gapped tribunal audit, AegisTrace compiles the entire case into an immutable, cryptographically sealed evidence package. An offline verifier can audit the package without internet, server, or database access."
* **Action:**
  1. Review the generated Evidence Dossier modal.
  2. Open terminal and run:
     ```bash
     python aegistrace.py demo judge --quick
     ```
  3. Show all 14 steps passing in 5 seconds, including the offline package verification and tamper rejection checks.

---

### Scene 10: Conclusion & Submission Wrap-Up (6:45 – 7:00)
* **Visual:** Return to browser, execute **"Purge Demo Data"** to show instant return to zero-state.
* **Narration:**
  > "AegisTrace proves that post-quantum security, dynamic watermarking, and fail-closed forensic attribution can operate seamlessly together in sovereign defense environments. Thank you."
