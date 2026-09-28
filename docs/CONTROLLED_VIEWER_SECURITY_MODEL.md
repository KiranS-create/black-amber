# AegisTrace: Controlled Viewer Security Model

## 1. Threat Model & Security Boundaries

The **Controlled Viewer** (`core/lineage/viewer.py`) represents the security-critical boundary where encrypted document material transitions into viewable plaintext. In classical DRM systems, the viewing application is either trusted blindly or relies on weak obfuscation that can be intercepted via memory dumps, process hooks, or local proxying.

AegisTrace establishes a zero-trust, post-quantum cryptographic viewing boundary:

```
+---------------------------------------------------------------------------------------+
|                               UNTRUSTED CLIENT ENVIRONMENT                            |
|                                                                                       |
|  +-----------------------------+                 +---------------------------------+  |
|  |     Controlled Viewer       |                 |  Recipient Local Keystore       |  |
|  |  (Volatile Memory Sandbox)  |                 |  - ML-KEM-768 Private Key       |  |
|  |                             |  Decapsulate    |  - ML-DSA-65 Private Key        |  |
|  | 1. Takes Broadcast Pkg     |<----------------|  (Server NEVER holds these keys)|  |
|  | 2. In-Memory Decryption     |                 +----------------+----------------+  |
|  | 3. Dynamic Watermark Gen    |                                  |                   |
|  | 4. Generates Receipt        |------- Signs DecryptionReceipt --+                   |
|  | 5. Emits Watermarked Output |                                                      |
|  +--------------+--------------+                                                      |
+-----------------|---------------------------------------------------------------------+
                  |
                  | Commit Receipt
                  v
+---------------------------------------------------------------------------------------+
|                             OFFLINE PERMISSIONED DLT                                  |
| - BFT Quorum Consensus across Independent Validators                                  |
| - Tamper-Evident Merkle Inclusion Logging                                             |
+---------------------------------------------------------------------------------------+
```

---

## 2. The 10-Step Decryption & Export Pipeline

1. **Broadcast Ingestion**: Controlled Viewer receives an encrypted `ReleaseRecipientPackage` containing an ML-KEM-768 encapsulated wrapping key and AES-256-GCM ciphertext.
2. **Identity Authentication**: The recipient client authenticates with its local credential provider and binds an active `AccessSession`.
3. **PQC Decapsulation**: The recipient decapsulates the AES wrapping key using their private ML-KEM-768 key:
   $$K_{\text{wrap}} \gets \text{ML-KEM-768.Decaps}(sk_{\text{kem}}, C_{\text{kem}})$$
4. **AES Key Unwrap & Decryption**: The master symmetric key $K_{\text{doc}}$ is unwrapped via AES-KW (NIST SP 800-38F), and plaintext bytes are decrypted in volatile memory via AES-256-GCM.
5. **Lineage Node Registration**: A new derivative `CopyInstance` (depth $d = d_{\text{parent}} + 1$) is created in `LineageService`.
6. **Dynamic Watermark Generation**: A domain-separated `DynamicWatermarkIdentity` is generated, binding the document root hash, recipient ID, session ID, event ID, copy ID, epoch, and nonce.
7. **Spatial Modulation & Embedding**: The dynamic codeword is embedded into the canvas using DSSS modulation and adaptive visual masking, preserving SSIM $\ge 0.98$ and PSNR $\ge 35\text{ dB}$.
8. **Recipient ML-DSA-65 Signing**: The recipient client independently constructs a canonical `DecryptionReceipt` and signs it using their private ML-DSA-65 key:
   $$\sigma_{\text{rec}} \gets \text{ML-DSA-65.Sign}(sk_{\text{dsa}}, \mathcal{M}_{\text{receipt}})$$
   **Crucial Invariant**: The server *never* signs on behalf of the recipient.
9. **DLT Quorum Consensus**: The signed receipt is submitted to the offline permissioned DLT, where independent validators verify the signature, ensure anti-replay, and commit it to an immutable Merkle block.
10. **Controlled Delivery**: The watermarked visual artifact is rendered to the user display or exported in a controlled format. Raw unwatermarked master bytes are never written to disk or exposed to downstream processes.

---

## 3. Threat Mitigation Matrix

| Threat Class | Adversary Goal | AegisTrace Mitigation |
| :--- | :--- | :--- |
| **Session Replay** | Replay a captured valid session ID to decrypt future packages or avoid new watermarking. | Sessions enforce cryptographic expiration, monotonic nonce consumption, and copy-binding. Replayed session IDs trigger `PermissionError: Session has expired`. |
| **Session Hijacking / Substitution** | Substitute Recipient A's session to export documents under Recipient B's name. | All export events cryptographically re-verify that `recipient.recipient_id == session.identity_id` and require Recipient A's private key to sign the export receipt. |
| **Server Key Compromise** | Rogue administrator attempts to forge decryption events to frame an innocent employee. | Server does not possess recipient private keys. Validators reject any receipt lacking a mathematically valid ML-DSA-65 signature matching the recipient's registered public key. |
| **Unilateral Ledger Tampering** | Malicious admin deletes or modifies past decryption records in the audit log. | Ledger requires Byzantine Fault Tolerant ($Q = \lfloor 2N/3 \rfloor + 1$) quorum consensus and produces immutable Merkle trees. Any altered block invalidates downstream block hashes. |
| **Physical Leak Capture** | Recipient photographs screen or prints document and leaks photograph. | Watermark survives camera-to-screen and print-to-scan optical capture via ArUco perspective rectification and Reed-Solomon DSSS demodulation, linking directly back to the DLT receipt. |

---

## 4. Key Custody Invariant

AegisTrace strictly adheres to the **Zero-Server Custody** principle for recipient identity:
- Server stores: Public keys ($\text{PK}_{\text{KEM}}$, $\text{PK}_{\text{DSA}}$), encrypted packages, lineage metadata, and finalized DLT blocks.
- Recipient workstation stores: Private keys ($\text{SK}_{\text{KEM}}$, $\text{SK}_{\text{DSA}}$) secured in hardware security modules (HSM) or local operating system keystores (DPAPI / Keychain).
- Under no operational circumstance is $\text{SK}_{\text{KEM}}$ or $\text{SK}_{\text{DSA}}$ transmitted across any network boundary or held by the viewer server.
