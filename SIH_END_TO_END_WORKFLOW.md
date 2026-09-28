# AegisTrace End-to-End Workflow Guide

**Workflow:** SIH26237 Standard Operating Procedure & Forensic Workflow  
**Environment:** Air-Gapped High-Security Enterprise & Sovereign Defense Deployments  

---

## 1. Document Release & Broadcast Encryption

### Step-by-Step Flow:
1. **Document Ingestion:** The sender uploads or provides a sensitive document (PDF, binary, or structured data). The system computes the pristine document digest:
   $$\text{doc\_hash} = \text{SHA-256}(\text{document\_bytes})$$
2. **Recipient Targeting:** The sender designates authorized recipient identities ($R_1, R_2, \dots, R_N$). The system verifies that each recipient has an active, non-revoked ML-KEM-768 public key.
3. **Payload Encryption:** The sender generates a random 256-bit symmetric key $K_{\text{doc}}$ and encrypts the document once:
   $$C_{\text{doc}} = \text{AES-256-GCM}(K_{\text{doc}}, \text{doc\_bytes}, \text{AD}=\text{"DOC-RELEASE:rel\_id:doc\_id"})$$
4. **KEM Encapsulation:** For each recipient $R_i$, the sender executes:
   $$(c_{\text{kem}, i}, ss_i) = \text{ML-KEM-768.Encapsulate}(pk_{\text{kem}, i})$$
   $$K_{\text{wrap}, i} = \text{HKDF-SHA256}(ss_i, \text{salt}=\text{"AEGIS-KEM-WRAP:v1"}, \text{info}=\text{"rel\_id:doc\_id:rec\_id"})$$
   $$W_i = \text{AES-KW}(K_{\text{wrap}, i}, K_{\text{doc}}, \text{AD}=\text{"KEY-WRAP-AUTH:rel\_id:rec\_id"})$$
5. **Distribution:** The broadcast package containing $C_{\text{doc}}$ and recipient-specific tuples $(c_{\text{kem}, i}, W_i)$ is distributed.

---

## 2. Recipient Decryption, Watermarking & DLT Commitment

### Client-Side Decryption Boundary:
1. **Private Decapsulation:** Recipient $R_i$ executes ML-KEM-768 decapsulation with private key $sk_{\text{kem}, i}$ to recover $ss_i$.
2. **Key Unwrapping & Decryption:** The client derives $K_{\text{wrap}, i}$, unwraps $K_{\text{doc}}$, decrypts $C_{\text{doc}}$, and verifies $\text{SHA-256}(\text{plaintext}) == \text{doc\_hash}$.
3. **Dynamic Watermark Identity:** The client derives an opaque dynamic identity:
   $$\text{token} = \text{HMAC-SHA256}(K_{\text{epoch}}, \text{"AEGIS-DYNAMIC-WM:v1:doc:rec:ses:evt:cpy:epoch:nonce"})$$
   $$\text{commitment} = \text{SHA-256}(\text{"AEGIS-WM-COMMIT:v1:"} \parallel \text{token} \parallel \text{salt})$$
   $$\text{codeword} = \text{HKDF-Expand}(\text{token}, 128)$$
4. **Watermark Embedding:** The dynamic watermark codeword is imperceptibly modulated into the document canvas via DSSS carrier modulation and Reed-Solomon ECC.
5. **Canonical Receipt Signing:** The client constructs a canonical `DecryptionReceipt` committing to $\text{doc\_hash}$, $\text{recipient\_id}$, $\text{session\_id}$, $\text{commitment}$, and $\text{timestamp}$, and signs it with the recipient's ML-DSA-65 private key:
   $$\sigma_{\text{rec}} = \text{ML-DSA-65.Sign}(sk_{\text{dsa}, i}, \text{canonical\_receipt\_payload})$$
6. **DLT Quorum Consensus:** The signed receipt is submitted to the permissioned DLT ledger, verified by validator nodes, bundled into an RFC 6962 Merkle tree, and sealed into a block with threshold quorum endorsements.
7. **Lineage Node Insertion:** The client records a new node in the `SparseLineageIndex` linking the new copy instance to its parent release root.

---

## 3. Leak Incident Investigation & Attribution

### Forensic Analysis Workflow:
1. **Leak Ingestion:** When an unauthorized copy or photograph leaks, investigators ingest the digital or scanned leak artifact into forensic custody, generating an initial `ChainOfCustodyEvent`.
2. **Watermark Decoding:** The `PrintCameraWatermarkDecoder` performs geometric corner detection, perspective rectification, and carrier demodulation to extract the 128-symbol codeword.
3. **DLT Correlation:** The extracted codeword and token are cross-referenced against the permissioned DLT ledger's indexed commitments to identify the corresponding `DecryptionReceipt`.
4. **Cryptographic Verification:**
   - Verify recipient ML-DSA-65 signature on the canonical receipt.
   - Verify DLT Merkle inclusion path from receipt to block header.
   - Verify validator quorum signatures on the block header.
   - Verify key lifecycle validity ($t_{\text{act}} \le t_{\text{dec}} \le t_{\text{rev}}$).
5. **Lineage & Telemetry Fusion:** The Bayesian attribution engine checks the `SparseLineageIndex` for downstream export chains and queries hardware TPM telemetry.
6. **Forensic Decision:** If all cryptographic proofs hold, the engine issues an `ATTRIBUTED` decision identifying the responsible recipient. If signal is corrupted or missing, it fails closed to `ABSTAINED` / `NO_SIGNAL`.

---

## 4. Evidence Package Export & Offline Independent Verification

1. **Assembly & Post-Quantum Signing:** The `EvidencePackageBuilder` aggregates the Case, Artifacts, Watermark Evidence, Decryption Receipt, Identity Proof, Device Evidence, Lineage, Ledger Proof, Telemetry, and Chain of Custody. It builds an RFC 6962 Merkle tree over all object digests, generates a `PackageManifest`, and signs it with the lead investigator's ML-DSA-65 key.
2. **Air-Gapped Audit:** The evidence package (.zip or folder) is transferred across an air-gap to an independent judicial terminal.
3. **Execution:** The standalone verifier runs:
   ```bash
   python aegistrace_verify.py /path/to/evidence_package.zip --tenant tenant_id --json
   ```
4. **12-Pillar Verdict:** The verifier executes all 12 validation checks in memory without network or server access, outputting an authoritative `VERIFIED` report.
