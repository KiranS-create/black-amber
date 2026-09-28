# CONTROLLED VIEWER SECURITY MODEL
## In-Memory Decryption Boundaries, Session Isolation, and Export Lineage
**Document Version:** 1.0.0  
**Classification:** AegisTrace Core Architecture  
**Security Level:** Production / Post-Quantum Air-Gapped Standard  

---

### 1. Security Objectives & Impossibility Boundaries

The Controlled Viewer subsystem in AegisTrace governs the critical transition between encrypted ciphertexts and readable human-facing documents. Its security architecture is grounded in a rigorous threat model that acknowledges physical boundaries while enforcing non-negotiable cryptographic invariants.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PHYSICAL / OS BOUNDARY                          │
│                                                                        │
│   ┌─────────────────────┐                 ┌────────────────────────┐   │
│   │ Release Ciphertext  │                 │ Recipient Private Key  │   │
│   │ (Encrypted on Disk) │                 │ (ML-DSA-65 / ML-KEM)   │   │
│   └──────────┬──────────┘                 └───────────┬────────────┘   │
│              │                                        │                │
│              ▼                                        ▼                │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │           IN-MEMORY CONTROLLED VIEWER BOUNDARY                 │   │
│   │                                                                │   │
│   │  1. ML-KEM-768 Decapsulation & HKDF Key Expansion              │   │
│   │  2. AES-256-GCM In-Memory Decryption (Zero Disk Footprint)     │   │
│   │  3. Ephemeral Session Context Creation                         │   │
│   │  4. Dynamic Watermark Synthesis (HMAC-SHA256 Token)            │   │
│   │  5. 2D Spatial Carrier Modulation (SSIM >= 0.995)              │   │
│   │  6. DecryptionReceipt Signed by Recipient ML-DSA-65            │   │
│   │  7. Synchronous 3-Node Offline DLT Quorum Commitment           │   │
│   │                                                                │   │
│   │  Output A: In-Memory Render Buffer (Display Only)              │   │
│   │  Output B: Controlled Export (Hardened Dynamic Mark + New DLT) │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### 1.1 Non-Negotiable Invariants
1. **Zero Unencrypted Disk Footprint:** Neither the master unencrypted plaintext nor unwatermarked image frames are ever committed to non-volatile storage, swap partitions, or temporary files.
2. **Deterministic Pre-Render Ledger Commitment:** No visual rendering or export artifact may be generated until the recipient's signed `DecryptionReceipt` is permanently accepted and committed by the DLT validator quorum.
3. **Session & Export Nonce Binding:** Each view session and each subsequent export operation derives a unique, orthogonal watermark codeword. Re-exporting an already opened document produces a new distinct lineage copy and an independent DLT receipt.

#### 1.2 The Fundamental Impossibility Boundary (Physical Screen & Sensor Capture)
A core scientific tenet of AegisTrace is intellectual honesty regarding physical capture:
- If an attacker uses an external analog camera (smartphone, high-resolution DSLR) to photograph a monitor displaying an authorized document, the software running on the workstation **cannot prevent light photons from striking the optical sensor**.
- **What AegisTrace Guarantees:** Because the display buffer itself contains the recipient's dynamic watermark modulated into the pixel luminance, any photograph of the screen captures the 128-bit carrier codeword. The recovered codeword cryptographically proves that the document was displayed on Recipient $X$'s workstation during Session $Y$ under DLT Block $Z$.

---

### 2. In-Memory Lifecycle & Execution Flow

#### Step 1: Package Ingestion & Recipient Decapsulation
The viewer client receives an encrypted release package containing:
- Broadcast ciphertext encrypted under ephemeral AES-256-GCM key $K_{\text{doc}}$.
- Recipient-specific key capsule $C_{\text{kem}} = \text{ML-KEM-768.Encaps}(PK_R)$.
- Canonical Document Root Hash $H_{\text{root}}$.

The client decapsulates the shared secret using recipient private key $SK_R$:
$$SS = \text{ML-KEM-768.Decaps}(SK_R, C_{\text{kem}})$$
$$K_{\text{doc}} = \text{HKDF-SHA256}(SS, \text{salt}=\text{"AEGISTRACE-DOC-KEY-DERIVATION"})$$

#### Step 2: In-Memory Decryption
The master document bytes are decrypted entirely in RAM:
$$D_{\text{plain}} = \text{AES-256-GCM.Decrypt}(K_{\text{doc}}, \text{ciphertext}, \text{nonce}, \text{tag})$$
The viewer verifies that $\text{SHA-256}(D_{\text{plain}}) == H_{\text{root}}$. If the hash check fails, RAM is wiped and execution terminates immediately.

#### Step 3: Dynamic Identity & Codeword Generation
An ephemeral session ID $S_{\text{id}}$ and monotonic event ID $E_{\text{id}}$ are generated. The dynamic watermark engine evaluates:
$$M_{\text{ctx}} = \text{"AEGISTRACE-DYNAMIC-WATERMARK-V1"} \parallel \dots \parallel H_{\text{root}} \parallel R_{\text{id}} \parallel S_{\text{id}} \parallel E_{\text{id}} \parallel C_{\text{id}}$$
$$T_{\text{wm}} = \text{HMAC-SHA256}(N_c, M_{\text{ctx}})$$
$$\mathbf{w} = \text{HKDF-Expand}(T_{\text{wm}}, \text{length}=128) \in \{-1, +1\}^{128}$$

#### Step 4: Recipient-Owned ML-DSA-65 Digital Signature
The recipient client constructs the canonical `DecryptionReceipt`:
$$\mathcal{R}_{\text{payload}} = \text{CanonicalJSON}\left( H_{\text{root}}, R_{\text{id}}, S_{\text{id}}, E_{\text{id}}, C_{\text{id}}, C_{\text{wm}}, T_{\text{timestamp}} \right)$$
$$\sigma_{\text{recipient}} = \text{ML-DSA-65.Sign}(SK_R, \mathcal{R}_{\text{payload}})$$

#### Step 5: Offline Replicated DLT Consensus
The signed receipt is submitted to the local permissioned DLT:
- Validators independently verify $\text{ML-DSA-65.Verify}(PK_R, \mathcal{R}_{\text{payload}}, \sigma_{\text{recipient}})$.
- Validators check for transaction deduplication and monotonic block height.
- Upon supermajority quorum ($\ge 3$ of 3 signatures), the block is finalized and replicated across node state stores.

#### Step 6: Presentation or Export
Only after DLT confirmation is the document rasterized:
- **Display Buffer:** $\alpha = 1.0$ (SSIM $\ge 0.995$, imperceptible).
- **Controlled Export:** $\alpha = 10.0$ (survives optical recapture and physical print/scan).

---

### 3. Attack Surface & Security Guarantees

| Attack Vector | Attacker Action | System Defense / Guarantee |
| :--- | :--- | :--- |
| **Recipient Forgery** | Attacker attempts to forge Alice's signature on a decryption receipt. | **REJECTED:** ML-DSA-65 post-quantum digital signature verification fails closed. |
| **Admin Frame-Up** | Central administrator attempts to insert a fake decryption receipt without recipient key. | **REJECTED:** DLT validator quorum rejects any receipt not signed by recipient's genuine ML-DSA-65 key. |
| **Receipt Replay** | Attacker resubmits a valid previous receipt to obscure a new leak. | **REJECTED:** DLT nodes maintain state deduplication; duplicate transaction IDs or hashes are rejected. |
| **Sub-Quorum Collusion** | Corrupt validator node attempts to unilaterally commit a tampered block. | **REJECTED:** Nodes require $Q \ge 3$ independent validator signatures before accepting block tip. |
| **Watermark Transplantation** | Attacker cuts watermark signal from Page A and overlays onto Page B. | **REJECTED:** Token includes $H_{\text{root}}$. Watermark verification against DLT fails closed with `TAMPERED_OR_TRANSPLANTED`. |
| **Disk Memory Scrape** | Forensic examination of workstation storage after viewer session. | **PROTECTED:** Plaintext bytes and unwatermarked frames are never written to filesystem; zero disk footprint. |
