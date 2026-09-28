# DECRYPTION RECEIPT SPECIFICATION
## Canonical Payload Schema, ML-DSA-65 Digital Signatures, and Non-Repudiation Invariants
**Document Version:** 1.0.0  
**Classification:** AegisTrace Cryptographic Specification  
**Security Level:** Production / Post-Quantum Air-Gapped Standard  

---

### 1. Specification Overview

The `DecryptionReceipt` is the foundational cryptographic artifact generated at the moment an authorized recipient decrypts a release package. It acts as an **irrefutable, non-repudiable legal and forensic acknowledgment** signed directly by the recipient's post-quantum private key ($SK_R$).

---

### 2. Canonical JSON Schema & Field Definitions

To guarantee cross-platform signature reproducibility across different programming languages and runtimes, receipt serialization enforces strict canonical JSON formatting:
- Keys sorted lexicographically in ascending ASCII order.
- Compact formatting: separators `(',', ':')` with zero extraneous whitespace.
- UTF-8 encoding.

#### 2.1 Canonical Data Fields

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `receipt_id` | `str` | Unique deterministic identifier formatted as `rcpt_<sha256_prefix>`. |
| `doc_root_hash` | `str` | Hex-encoded SHA-256 hash of the master unwatermarked document plaintext. |
| `recipient_id` | `str` | Unique recipient principal identifier (e.g., `rec_alice_4f9a`). |
| `session_id` | `str` | Ephemeral viewer session identifier (e.g., `sess_a8b9c0d1`). |
| `event_id` | `str` | Monotonic decryption/export event identifier (e.g., `evt_dec_001`). |
| `copy_id` | `str` | Unique copy instance ID tracked in the lineage graph (`cpy_<hex>`). |
| `watermark_token` | `str` | 64-char hex string: 256-bit dynamic watermark identity token $T_{\text{wm}}$. |
| `watermark_salt` | `str` | 64-char hex string: 256-bit blinding salt $\sigma$. |
| `watermark_commitment` | `str` | 64-char hex string: Binding commitment $C_{\text{wm}} = \text{SHA-256}(T_{\text{wm}} \parallel \sigma)$. |
| `timestamp` | `str` | ISO 8601 UTC timestamp of the decryption event (e.g., `2026-09-27T10:15:30Z`). |
| `recipient_pubkey_hex` | `str` | Hex-encoded ML-DSA-65 public key (1,952 bytes = 3,904 hex chars). |
| `recipient_signature_hex`| `str` | Hex-encoded ML-DSA-65 signature over canonical signing payload (3,309 bytes = 6,618 hex chars). |
| `metadata` | `dict` | Optional auxiliary metadata (e.g., client environment, viewer version). |

---

### 3. Signing Payload Formulation

The recipient's ML-DSA-65 signature is computed strictly over the canonical signing payload dictionary $\mathcal{P}_{\text{sign}}$:

```python
signing_payload = {
    "copy_id": receipt.copy_id,
    "doc_root_hash": receipt.doc_root_hash,
    "event_id": receipt.event_id,
    "recipient_id": receipt.recipient_id,
    "session_id": receipt.session_id,
    "timestamp": receipt.timestamp,
    "watermark_commitment": receipt.watermark_commitment,
}
```

Notice that `watermark_token` and `watermark_salt` are **intentionally excluded from the signing payload**. This design ensures:
1. **Zero-Knowledge Ledger Inclusion:** The receipt signature binds the commitment $C_{\text{wm}}$, not the raw token.
2. **Public Auditability:** Any party verifying the ledger signature validates that the recipient acknowledged committing to *that specific watermark commitment* without needing to learn the underlying codeword.

---

### 4. Verification Algorithm & Failure Modes

When an offline DLT node or forensic investigator evaluates a `DecryptionReceipt`:

```
                    [ Receive DecryptionReceipt ]
                                  │
                                  ▼
               [ Step 1: Verify Commitment Integrity ]
               Compute: C' = SHA-256(watermark_token || watermark_salt)
               Assert:  C' == receipt.watermark_commitment
                     └── Failure ──► REJECT: COMMITMENT_MISMATCH
                                  │
                                  ▼
               [ Step 2: Canonical Payload Serialization ]
               Construct canonical JSON of signing fields
               Encode as UTF-8 bytes
                                  │
                                  ▼
               [ Step 3: ML-DSA-65 Signature Verification ]
               Call: ML-DSA-65.Verify(recipient_pubkey, payload_bytes, signature)
                     └── Failure ──► REJECT: INVALID_RECIPIENT_SIGNATURE
                                  │
                                  ▼
               [ Step 4: RFC-6962 Leaf Hash Computation ]
               Compute: LeafHash = SHA-256( 0x00 || CanonicalJSON(receipt) )
                                  │
                                  ▼
                     [ VALID: ACCEPT TRANSACTION ]
```

---

### 5. Non-Repudiation Invariant Proof

**Claim:** A recipient $R$ whose valid ML-DSA-65 digital signature is committed to the permissioned DLT cannot credibly claim that:
1. They never decrypted the document.
2. The watermark found in a leaked file was manufactured by the document distributor or an adversary.

*Proof:*
1. **Unforgeability of ML-DSA-65:** ML-DSA-65 provides 192-bit post-quantum security against existential forgery under chosen-message attacks (EUF-CMA). No polynomial-time adversary without $SK_R$ can forge $\sigma_{\text{recipient}}$ except with negligible probability $\epsilon \le 2^{-192}$.
2. **Binding to Document & Session:** $\mathcal{P}_{\text{sign}}$ explicitly binds the immutable SHA-256 document root hash $H_{\text{root}}$, the session ID $S_{\text{id}}$, and the watermark commitment $C_{\text{wm}}$.
3. **Consensus Timestamping:** The receipt is sealed within a DLT block signed by supermajority validator quorum $\mathcal{V}$, establishing provable chronological existence prior to any subsequent leak.
4. Therefore, the recipient possesses sole computational control over the decryption event. $\blacksquare$
