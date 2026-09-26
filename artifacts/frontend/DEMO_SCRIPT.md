# SIH26237 — Live Hackathon Demo Presenter Script & Choreography

**For:** SIH26237 Project Presenters & Live Demonstrators  
**App Location:** `apps/web/` (Running on `http://localhost:3000` or offline bundle)

---

## Pre-Flight Checklist
- [ ] Open web interface at `http://localhost:3000` in full screen (F11).
- [ ] Confirm Backend connection indicator is green (`LIVE BACKEND (:8000)`) or offline mode is active (`OFFLINE SIMULATION (LOCAL DEMO)`).
- [ ] Ensure zoom is set to 100% or 110% for clear projection readability.

---

## Demo Script

### 1. Introduction & Problem Statement (30 seconds)
> "Respected judges, in government and enterprise environments, sharing sensitive documents with multiple external recipients is high risk. The moment a recipient opens or prints a file, traditional perimeter access controls end. If a leak happens, traditional systems cannot prove who decrypted and leaked the document without risking false accusations.
> 
> SIH26237 solves this with post-quantum envelope encryption, immutable decryption provenance, and fail-closed multi-channel attribution."

### 2. Recipient Identities & Post-Quantum Key Isolation (45 seconds)
> *(Action: Click 'Recipients' tab or open 'Judge Walkthrough' Stage 1)*
> 
> "Here in our Recipient Registry, each party—Alice, Bob, and Charlie—holds isolated post-quantum keypairs.
> - For key exchange, we implement **ML-KEM-768** (FIPS 203), standardizing post-quantum security against quantum attackers.
> - For provenance signatures, we implement **ML-DSA-65** (FIPS 204).
> 
> Notice that each recipient’s private keys never leave their secure boundary."

### 3. Encrypted Multi-Recipient Document Release (45 seconds)
> *(Action: Click 'Release' tab or Stage 2 in Walkthrough)*
> 
> "When publishing a confidential document, we do NOT re-encrypt the entire payload multiple times. Instead, we use hybrid envelope encryption:
> 1. The document is encrypted once with high-speed **AES-256-GCM** using an ephemeral 256-bit symmetric key.
> 2. That symmetric key is encapsulated individually for Alice, Bob, and Charlie using their respective ML-KEM-768 public keys.
> 3. Each recipient package contains only their specific key capsule and the shared ciphertext. Notice the explicit isolation between the Data Plane `ORIGINAL_DOCUMENT_HASH` and the Envelope `RELEASE_ARTIFACT_HASH`."

### 4. Decryption & Non-Repudiation Provenance (45 seconds)
> *(Action: Click 'Decrypt' tab or Stage 3 in Walkthrough)*
> 
> "Now, let’s demonstrate Bob decrypting his package.
> When Bob initiates decryption, his client decapsulates the key, verifies the AES-GCM authentication tag, and embeds an authenticated attribution marker.
> 
> Crucially, before granting document access, Bob’s client cryptographically signs a **Decryption Provenance Event** using his ML-DSA-65 private key and submits it to the audit ledger."

### 5. Tamper-Evident Hash-Chained Audit Ledger (60 seconds)
> *(Action: Click 'Ledger' tab or Stage 4 in Walkthrough)*
> 
> "Here is the Tamper-Evident Ledger. Every release and decryption event is linked through a SHA-256 hash chain:
> `Event Hash = SHA256(previous_event_hash || event_id || artifact_hash || evidence_hash || signature)`
> 
> Let's test the ledger's integrity: click **'Verify Chain'** — all blocks verify intact with the root tip.
> Now watch what happens if an internal adversary attempts to modify a historical record: click **'Simulate Local Ledger Tamper'**.
> Instantly, the hash chain breaks, the status turns RED (`TAMPER DETECTED`), and the exact corrupted block is localized. Historical logs cannot be altered without cryptographic detection."

### 6. Leak Analysis & Multi-Channel Bayesian Evidence Fusion (60 seconds)
> *(Action: Click 'Leak Analysis' tab or Stage 5 in Walkthrough)*
> 
> "Now, suppose a leak occurs. We feed the exfiltrated artifact into our Attribution Engine.
> 
> Rather than relying on a single fragile watermark, our engine performs **Bayesian Multi-Channel Evidence Fusion**:
> - Decodes the spatial/frequency watermark with Reed-Solomon error correction
> - Computes continuous Tardos correlation scores ($Z_i$) with bounded false alarm ($\epsilon_1 \le 10^{-4}$)
> - Verifies the recipient cryptographic signature and ledger provenance
> - Calibrates channel reliability ($\rho_i$) against measured distortion
> 
> The result: **Bob is attributed with HIGH confidence (Bayesian LLR: 18.08, Separation Margin $\Delta$: 18.08, Tardos $Z = 14.82$)**."

### 7. Adversarial Attack Lab & The Fail-Closed Guarantee (60 seconds)
> *(Action: Click 'Attack Lab' tab or Stage 6 in Walkthrough)*
> 
> "The defining hallmark of our system is our strict **Fail-Closed Axiom: Abstention is strictly preferred over false accusations**.
> 
> Let’s run our adversarial test matrix:
> 1. **Unwatermarked Raw Document:** Returns `NO_SIGNAL` $\rightarrow$ `ABSTAIN`.
> 2. **Forged HMAC Marker:** Cryptographic signature verification fails $\rightarrow$ `INSUFFICIENT_EVIDENCE` $\rightarrow$ `ABSTAIN`.
> 3. **Tampered Recipient Frame (framing Alice):** Signature mismatch detected $\rightarrow$ `ABSTAIN`.
> 4. **Print-Scan-Camera Distortion:** OpenCV homography corrects geometric skew and recovers the signal cleanly.
> 5. **Cross-Document Transplantation:** Document hash mismatch $\rightarrow$ `CONFLICT` $\rightarrow$ `ABSTAIN`.
> 
> In all adversarial cases, innocent users are strictly protected from false accusations."

### 8. Conclusion & Technical Evidence Dossier (15 seconds)
> *(Action: Click 'Export Technical Report')*
> 
> "Finally, we can export a complete Technical Evidence & Provenance Dossier containing the mathematical fusion breakdown, raw SHA-256 hashes, and verifiable PQC signatures. Thank you, and we welcome your questions!"
