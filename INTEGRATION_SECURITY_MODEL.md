# AegisTrace Integration Security Model

**Document:** Formal Threat Model, Trust Assumptions & Security Invariants  
**Target:** Post-Quantum Zero-Trust Document Tracking & Forensic Leak Attribution  

---

## 1. Threat Model & Attacker Capabilities

AegisTrace defends against state-sponsored adversaries and malicious insider threats equipped with:

1. **Quantum Computing Capabilities (Shor's Algorithm):** An adversary with a cryptanalytically relevant quantum computer (CRQC) capable of breaking RSA-2048, ECDSA, ECDH, and Ed25519.
2. **Malicious Recipient Insiders (Authorized Exfiltrators):** An authorized recipient who legitimately decapsulates the document, captures a photograph or digital export, wipes or crops visual fiducials, and publishes the document anonymously.
3. **Colluding Subsets of Validators ($< \frac{1}{3}N$ Byzantine Nodes):** Rogue validator nodes attempting to forge ledger receipts, fork block histories, or roll back time.
4. **Compromised Originating Servers / Database Intrusion:** An attacker who compromises the central application database or key registry after the leak incident occurs.
5. **Man-in-the-Middle & Eavesdropping:** Network interceptors attempting to decrypt broadcast packages in transit.

---

## 2. Security Invariants & Guarantees

### Invariant 1: Post-Quantum Forward Security & Unforgeability
- **Mechanism:** Key encapsulation via NIST FIPS 203 ML-KEM-768 (Category 3 Security, $\ge 128$ bits post-quantum security) and digital signatures via NIST FIPS 204 ML-DSA-65.
- **Guarantee:** Captured ciphertexts and signed receipts cannot be decrypted or forged by classical or quantum adversaries.

### Invariant 2: Recipient-Bound Decryption Provenance
- **Mechanism:** The document key $K_{\text{doc}}$ is only decapsulatable by the recipient's private KEM key. Decryption is cryptographically coupled to the creation and signing of a canonical `DecryptionReceipt`.
- **Guarantee:** A recipient cannot decrypt without generating a signed, ledger-committed receipt containing the dynamic watermark commitment.

### Invariant 3: Fail-Closed Attribution & Non-Repudiation
- **Mechanism:** The Bayesian multi-channel fusion engine requires matching watermark codeword correlation ($\ge 0.85$), recipient ML-DSA-65 signature verification, and DLT Merkle inclusion proof.
- **Guarantee:** If watermark signal is destroyed, corrupted, or inconclusive, the system strictly transitions to `NO_SIGNAL` / `ABSTAINED` and never outputs a false accusation.

### Invariant 4: Zero-Trust Origin Server Independence
- **Mechanism:** Portable evidence packages contain all 17 self-describing evidence schemas, RFC 6962 Merkle trees, and acyclic dependency DAGs.
- **Guarantee:** Even if the originating database is wiped, an independent offline verifier audits the package using only local cryptographic math.

### Invariant 5: Strict Multi-Tenant Boundary Isolation
- **Mechanism:** All cryptographic key derivations, release associated data, lineage indexes, and package manifests incorporate domain-separated `tenant_id` scopes.
- **Guarantee:** Cross-tenant decapsulation, lookup, or verification fails closed immediately.
