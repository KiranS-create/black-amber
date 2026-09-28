# AegisTrace: Security Trust Boundaries & Cryptographic Non-Repudiation
**Smart India Hackathon 2026 — Problem Statement ID: SIH26237**  
**Classification:** Cryptographic Specification & Trust Domain Architecture

---

## 1. Executive Summary & Zero-Trust Architecture

A fundamental flaw in conventional document security systems is misplaced trust in the central server or database administrator. In legacy architectures, a rogue administrator can fabricate logs, alter audit records, or forge decryption events.

AegisTrace establishes a **Zero-Trust Post-Quantum Trust Model** where:
1. No single entity (including the central server) possesses unilateral authority to fabricate forensic evidence.
2. Every decryption event is cryptographically signed by the recipient using **NIST FIPS 204 ML-DSA-65**.
3. All audit records are immutably anchored in a **BFT Replicated Ledger** with **RFC-6962 Merkle Trees**.
4. Forensic packages are verified **statelessly and offline** by independent auditors without database access.

---

## 2. Formal Cryptographic Trust Domains

```mermaid
graph TD
    subgraph Domain 1: Tenant Authority / Central Server
        S1["Document Release Manager"]
        S2["Broadcast Key Encapsulation (ML-KEM-768)"]
        S3["Sparse Lineage Index"]
    end
    subgraph Domain 2: Recipient Sovereign Endpoint
        R1["Recipient Private Key (ML-KEM-768 sk)"]
        R2["Recipient Signing Key (ML-DSA-65 sk)"]
        R3["Decryption-Time DSSS Watermarking"]
        R4["Mandatory DecryptionReceipt Signing"]
    end
    subgraph Domain 3: Distributed Ledger Validators
        V1["BFT Consensus Quorum (2f + 1)"]
        V2["Monotonic Block Height"]
        V3["RFC-6962 Merkle Tree Roots"]
    end
    subgraph Domain 4: Offline Sovereign Verifier
        O1["Stateless Rule Engine (11 Rules)"]
        O2["Air-Gap Egress Guard"]
        O3["Fail-Closed Decision Engine"]
    end

    Domain 1 -- "Encrypted Broadcast Package" --> Domain 2
    Domain 2 -- "Signed DecryptionReceipt" --> Domain 3
    Domain 3 -- "Merkle Inclusion Proof" --> Domain 4
    Domain 1 -- "Lineage & Manifest" --> Domain 4
    Domain 2 -- "Leaked Watermarked Artifact" --> Domain 4
```

---

## 3. Server Capability & Trust Limits (What the Server CAN vs CANNOT Do)

| Server Capability | Permitted? | Cryptographic Enforcement Mechanism |
|---|:---:|---|
| Encapsulate broadcast encryption keys for authorized recipients | **YES** | Server uses recipient public ML-KEM-768 keys to encapsulate AES-256 session keys. |
| Decrypt broadcast content intended for a recipient | **NO** | Ciphertext decapsulation requires the recipient's private key ($\text{sk}_R$), which never leaves the recipient's secure enclave / TPM. |
| Forge a recipient's decryption receipt | **NO** | `DecryptionReceipt` requires a valid NIST FIPS 204 ML-DSA-65 signature from $\text{sk}_R$. |
| Delete or modify a previously committed decryption record | **NO** | BFT validator nodes reject blocks with modified transaction trees or invalid Merkle roots. |
| Alter an exported forensic evidence package | **NO** | Evidence packages contain an RFC-6962 Merkle tree committing to all objects, signed by the investigator. |
| Forge forensic attribution to an innocent party | **NO** | Attribution requires mathematical correlation between the extracted watermark token, the signed receipt, and the DLT inclusion proof. |

---

## 4. Mathematical Non-Repudiation Proof

When recipient $R$ decapsulates document release $D_{\text{rel}}$, the local client executes an atomic cryptographic protocol:

### Step 1: Payload Construction
The client compiles the deterministic canonical receipt payload:
$$\text{Payload} = \text{CanonicalJSON}\left(\{ \text{event\_id}, \text{doc\_id}, \text{doc\_hash}, \text{release\_id}, \text{copy\_id}, \text{sess\_id}, \text{device\_id}, \text{timestamp} \}\right)$$

### Step 2: Recipient Signature Generation
Recipient $R$ signs the SHA-256 digest of the payload using their sovereign ML-DSA-65 private key:
$$\sigma_R = \text{ML-DSA-65.Sign}\left(\text{sk}_R, \text{SHA-256}(\text{Payload})\right)$$

### Step 3: DLT Merkle Tree Inclusion
The receipt is broadcast to the BFT validator network. Upon inclusion in block $B_h$, a Merkle audit path $\Pi_{\text{Merkle}}$ is generated against the block's Merkle root $M_h$:
$$\text{VerifyMerkleProof}\left(\text{SHA-256}(\text{Receipt}), \Pi_{\text{Merkle}}, M_h\right) = \text{True}$$

### Step 4: Non-Repudiation Property
Recipient $R$ cannot repudiate decryption of the document because:
1. Under the hardness of Module Learning with Errors (**ML-KEM**) and Module Learning with Rounding / Short Integer Solution (**ML-DSA**), no other entity (including server administrators) could produce signature $\sigma_R$.
2. The receipt commits to both the recipient's hardware TPM device fingerprint ($\text{device\_id}$) and the document's cryptographic hash ($\text{doc\_hash}$).
3. The receipt is timestamped and anchored across multiple independent BFT validators.

---

## 5. Lineage Boundary & Downstream Gap Semantics

When an authorized recipient (e.g. Alice) exports or transfers a document outside the monitored application boundary (e.g. via USB or air-drop to Bob):

1. **Monitored Scope:** The platform maintains cryptographic certainty of all transfers within registered AegisTrace endpoints.
2. **Unmonitored Egress (Downstream Gap):** If an artifact is leaked after unmonitored transfer, the forensic engine does not hallucinate false hops. It reports:
   - **Attributed Parent:** Last verified cryptographic holder (Alice).
   - **Lineage Status:** `ATTRIBUTED_WITH_DOWNSTREAM_GAP`.
   - **Integrity Guarantee:** Proves that all downstream variants originated from Alice's unique watermarked decryption session.

---

## 6. Architecture Comparison Matrix

| Security Dimension | Conventional Centralized Logging | Public Blockchain DLT | AegisTrace Sovereign PQC DLT |
|---|---|---|---|
| **Cryptographic Resilience** | Classical RSA / ECDSA (Quantum Vulnerable) | Classical ECDSA / Secp256k1 (Vulnerable) | **NIST FIPS 203 ML-KEM-768 & FIPS 204 ML-DSA-65 (Quantum Secure)** |
| **Admin Tamper Resistance** | Low (DB admin can update/delete rows) | High (Requires 51% mining / stake) | **High (BFT Quorum consensus + immutable hash-chain)** |
| **Air-Gap & Sovereign Operation** | No (Requires cloud DB connectivity) | No (Requires public Internet node access) | **Yes (100% offline, local BFT replication)** |
| **Recipient Non-Repudiation** | Weak (Server logs "User X clicked download") | None for confidential payload | **Strong (Recipient signs decryption payload with local ML-DSA key)** |
| **Offline Verification** | Impossible (Requires live database query) | Requires live chain query | **Complete (Standalone .zip archive with 11-rule audit engine)** |
