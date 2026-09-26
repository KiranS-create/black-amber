# SIH26237 Cryptographic Design

## 1. Cryptographic Primitives Selection
- **Envelope Encryption**: `AES-256-GCM` (NIST SP 800-38D) with a fresh random 256-bit key ($K_{doc}$) and 96-bit unique nonce per release.
- **Key Encapsulation Mechanism (KEM)**: `ML-KEM-768` (FIPS 203 / Kyber-768) for post-quantum recipient public key encapsulation.
- **Key Derivation Function (KDF)**: `HKDF-SHA256` (RFC 5869) with release and recipient domain separation.
- **Digital Signatures**: `ML-DSA-65` (FIPS 204 / Dilithium3) / Ed25519 for non-repudiation signing of decryption provenance events.
- **Traceability Authentication**: `HMAC-SHA256` bound over $(doc\_id, release\_id, recipient\_id, doc\_hash)$.

## 2. Key Isolation & Envelope Protocol
1. **Issuer Phase**:
   - Computes $H_{doc} = \text{SHA-256}(\text{Document})$.
   - Generates random $K_{doc} \leftarrow \{0,1\}^{256}$.
   - Encrypts Document: $C_{doc}, T = \text{AES-GCM-Encrypt}(K_{doc}, \text{Document}, \text{AD})$.
   - For each recipient $R_i$:
     - $(\text{ct}_i, ss_i) = \text{ML-KEM-Encap}(\text{PK}_{R_i})$.
     - $K_{wrap, i} = \text{HKDF-SHA256}(ss_i, \text{salt}="WRAP-SALT:rel:R_i")$.
     - $W_i = \text{AES-Wrap}(K_{wrap, i}, K_{doc})$.
     - Assembles package $P_i = (rel\_id, doc\_id, R_i, \text{ct}_i, W_i, C_{doc}, \dots)$.

2. **Recipient Decryption Phase**:
   - $ss_i = \text{ML-KEM-Decap}(\text{SK}_{R_i}, \text{ct}_i)$.
   - $K_{wrap, i} = \text{HKDF-SHA256}(ss_i)$.
   - $K_{doc} = \text{AES-Unwrap}(K_{wrap, i}, W_i)$.
   - $\text{Document} = \text{AES-GCM-Decrypt}(K_{doc}, C_{doc})$.
   - Verifies $\text{SHA-256}(\text{Document}) == H_{doc}$.
   - Embeds recipient-specific marker $M_i$.
   - Signs decryption provenance event with $\text{SK}_{DSA, R_i}$.
