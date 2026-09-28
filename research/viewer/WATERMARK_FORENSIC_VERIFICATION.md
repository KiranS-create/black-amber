# WATERMARK FORENSIC VERIFICATION & THE HONESTY INVARIANT
## Mathematical Attribution, Dual-Layer Cryptographic Validation, and Evidentiary Boundaries
**Document Version:** 1.0.0  
**Classification:** AegisTrace Forensic Attribution Standard  
**Security Level:** Production / Post-Quantum Air-Gapped Standard  

---

### 1. The Forensic Challenge & End-to-End Pipeline

When an unauthorized document leak occurs (e.g., a PDF shared on external forums, a smartphone photo of a classified briefing, or a printed scan), forensic investigators face three fundamental questions:
1. **Source Document:** Which canonical document root does this leak originate from?
2. **Accessing Entity:** Which authorized recipient decrypted the instance that produced this leak?
3. **Session & Export Lineage:** When, where, and through which export transition was this instance created?

The AegisTrace `DynamicForensicExtractor` implements an end-to-end mathematical verification pipeline that answers these questions with post-quantum cryptographic proof.

```
       ┌────────────────────────────────────────────────────────┐
       │             LEAKED ARTIFACT INGESTION                  │
       │       (Digital PDF / Raster Image / Phone Photo)       │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             STAGE 1: SIGNAL RECOVERY                   │
       │  - ArUco Multi-Scale Alignment & Perspective Rectify   │
       │  - Orthogonal Carrier Despreading (2D DSSS)            │
       │  - Recover 128-Bit Dynamic Codeword: w_rec in {-1,+1}  │
       │    (Fail-Closed NO_SIGNAL if Correlation < Threshold)  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             STAGE 2: DLT RECEIPT LOOKUP                │
       │  - Search Replicated DLT for Matching Codeword:       │
       │    derive_dynamic_codeword(rcpt.watermark_token)       │
       │  - Retrieve Candidate DecryptionReceipt R               │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │        STAGE 3: MULTI-LAYER CRYPTOGRAPHIC AUDIT        │
       │  1. Check Salt Commitment:                             │
       │     SHA-256(watermark_token || salt) == commitment     │
       │  2. Verify Recipient ML-DSA-65 Signature:              │
       │     ML-DSA-65.Verify(PK_recipient, payload, sig)       │
       │  3. Verify Validator Quorum Consensus:                │
       │     |Signatures| >= Q (>= 3 of 3 Independent Keys)    │
       │  4. Verify RFC-6962 Merkle Inclusion Proof:            │
       │     MerkleProof.verify(ReceiptLeaf, BlockHeaderRoot)   │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │          STAGE 4: LINEAGE ANCESTRY TRACING             │
       │  - Query LineageStorage for CopyInstance cpy_id        │
       │  - Backtrack Ancestors to DocumentRoot                 │
       │  - Determine Last Controlled Holder                    │
       │  - Compute SSIM & PSNR Visual Equivalence              │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │        STAGE 5: HONEST ATTRIBUTION DETERMINATION       │
       │  Output: DynamicForensicAttributionResult              │
       │  - Status: VERIFIED_RECIPIENT_DECRYPTION               │
       │  - Confidence: 0.9999                                  │
       │  - Strict Evidentiary Disclaimer Applied               │
       └────────────────────────────────────────────────────────┘
```

---

### 2. Five-Stage Verification Algorithm

#### Stage 1: Dynamic Watermark Extraction
The extractor ingests the raster image $I_{\text{leak}}$, applies homography rectification using synchronization anchors, and computes the correlation with each of the $L = 128$ orthogonal carrier bases $\phi_i$:
$$\gamma_i = \frac{1}{W \cdot H} \sum_{x, y} I_{\text{leak}}(x, y) \cdot \phi_i(x, y)$$
$$w_i = \begin{cases} +1 & \text{if } \gamma_i > 0 \\ -1 & \text{if } \gamma_i \le 0 \end{cases}$$

If the average carrier correlation confidence is below the detection threshold $\tau = 0.50$, the extractor **fails closed immediately**:
$$\text{Status} = \mathtt{NO\_WATERMARK\_DETECTED}, \quad \text{AttributionLevel} = \mathtt{LEVEL\_0\_NO\_SIGNAL}$$

#### Stage 2: Replicated DLT Receipt Matching
The extractor searches the committed blocks of the offline permissioned DLT. For each transaction $T_x$, it recomputes the expected 128-bit codeword:
$$\mathbf{w}_{\text{expected}} = \text{HKDF-Expand}(T_x.\text{watermark\_token}, \text{length}=128)$$
When $\mathbf{w}_{\text{expected}} \equiv \mathbf{w}_{\text{recovered}}$ (or Hamming distance within acceptable error correction bounds), the corresponding `DecryptionReceipt` is selected.

#### Stage 3: Cryptographic Audit
The candidate receipt must pass all four verification gates:
1. **Commitment Gate:** $\text{SHA-256}(T_{\text{wm}} \parallel \sigma) == C_{\text{wm}}$.
2. **Signature Gate:** $\text{ML-DSA-65.Verify}(PK_R, \mathcal{P}_{\text{sign}}, \sigma_R) == \text{True}$.
3. **Quorum Gate:** Block header contains $\ge \lfloor 2N/3 \rfloor + 1$ valid signatures from registered validators.
4. **Merkle Gate:** RFC-6962 inclusion proof $\Pi$ correctly hashes leaf node to block `merkle_root`.

If any gate fails, attribution halts and returns `TAMPERED_OR_TRANSPLANTED` or `INVALID_SIGNATURE`.

#### Stage 4: Lineage Graph Cross-Referencing
The extractor queries `LineageStorage` using `receipt.copy_id`. It reconstructs the directed ancestor path from the copy to the document root, checking for edge breaks, forwarding events, and session validity.

---

### 3. THE HONESTY INVARIANT

In forensic systems, overstated claims destroy credibility in courtrooms and military tribunals. AegisTrace adheres strictly to **The Honesty Invariant**:

> **THE HONESTY INVARIANT:**  
> A successful dynamic forensic attribution cryptographically and irrefutably proves:  
> **"Recipient $R$ decrypted Document $D$ during Session $S$ on Workstation $W$ at Time $T$, as signed by their private key and committed to the DLT."**  
>  
> It **DOES NOT** automatically prove:  
> **"The human individual named $R$ personally leaked the file to the adversary."**

#### 3.1 Alternative Physical Hypotheses Acknowledged
The forensic result explicitly notes alternative physical explanations that cannot be ruled out by pure cryptography:
1. **Endpoint Compromise:** An adversary compromised Recipient $R$'s workstation with kernel malware and captured the framebuffer after authorized decryption.
2. **Physical Coercion / Shoulder Surfing:** A third party photographed the display over Recipient $R$'s shoulder while $R$ was legitimately reviewing the document.
3. **Stolen Hardware:** The physical device was stolen while an authorized session was active.

By explicitly stating these evidentiary boundaries, AegisTrace reports provide unassailable scientific integrity.

---

### 4. Attribution Confidence Matrix

| Forensic State | Watermark Signal | Recipient Signature | DLT Quorum | Merkle Proof | Attribution Level | Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Clean Master / Unmarked** | None | N/A | N/A | N/A | `LEVEL_0_NO_SIGNAL` | Fail-closed: No attribution |
| **Heavily Destroyed Mark** | Sub-threshold | N/A | N/A | N/A | `LEVEL_0_NO_SIGNAL` | Fail-closed: Abstain |
| **Signature Mismatch** | Valid Codeword | Invalid | Valid | Valid | `LEVEL_1_DOC_DETECTED` | Tampered / Forgery detected |
| **Ledger Rollback/Fork** | Valid Codeword | Valid | Sub-quorum | Invalid | `LEVEL_1_DOC_DETECTED` | Consensus failure: Abstain |
| **Transplanted Mark** | Valid Codeword | Valid | Valid | Valid | `LEVEL_2_RECIPIENT_ID` | Hash mismatch: Transplant detected |
| **Full Mathematical Match** | Valid Codeword | Valid (ML-DSA-65) | Valid (Quorum) | Valid (RFC-6962) | `LEVEL_4_FULL_LINEAGE` | **PROVED: Signed Decryption Event** |
