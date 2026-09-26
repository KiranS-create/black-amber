# SIH26237 System Architecture

## 1. Architectural Overview
SIH26237 provides a quantum-resistant cryptographic framework for multi-recipient document distribution, decentralized decryption provenance logging, and fail-closed leak attribution.

```
                    +------------------------+
                    |    Original Document   |
                    +-----------+------------+
                                |
                   [ AES-256-GCM Encryption ]
                                |
             +------------------+------------------+
             | Ephemeral 256-bit Document Key (K_doc) |
             +------------------+------------------+
                                |
     +--------------------------+--------------------------+
     |                          |                          |
[ ML-KEM-768 Encap ]       [ ML-KEM-768 Encap ]       [ ML-KEM-768 Encap ]
(Alice Public Key)         (Bob Public Key)           (Charlie Public Key)
     |                          |                          |
+----+----+                +----+----+                +----+----+
| Package |                | Package |                | Package |
| (Alice) |                |  (Bob)  |                | (Charlie)|
+----+----+                +----+----+                +----+----+
     |                          |                          |
     |                     [ Bob Decrypts ]                |
     |                     - KEM Decapsulate               |
     |                     - AES-GCM Decrypt               |
     |                     - Embed Marker                  |
     |                     - Sign Decryption Event (ML-DSA)|
     |                          |                          |
     |                          v                          |
     |              [ Tamper-Evident Ledger ]              |
     |              (Hash-chained audit log)               |
     |                          |                          |
     |                          v                          |
     |                   [ Leak Occurs ]                   |
     |                          |                          |
     |                          v                          |
     +--------------> [ Attribution Engine ] <-------------+
                      - Extract Marker
                      - Verify HMAC Token
                      - Verify Signature
                      - Verify Ledger Chain
                                |
                   +------------+------------+
                   |                         |
              [ ATTRIBUTED ]            [ ABSTAIN ]
              (Legitimate)            (Forged/Missing)
```

## 2. Core Components
- **`core/crypto/`**: Post-quantum ML-KEM-768 key encapsulation, ML-DSA-65 digital signatures, AES-256-GCM symmetric encryption, HKDF-SHA256 derivation.
- **`core/recipient.py`**: Recipient cryptographic enrollment and public/private key isolation.
- **`core/release.py`**: Multi-recipient envelope packaging.
- **`core/provenance/decryption.py`**: Recipient-side decryption with non-repudiation signing.
- **`core/ledger/ledger.py`**: Hash-chained tamper-evident audit ledger.
- **`core/traceability/`**: Cryptographic marker issuance and embedding.
- **`core/attribution/engine.py`**: Fail-closed attribution engine evaluating evidence completeness.
