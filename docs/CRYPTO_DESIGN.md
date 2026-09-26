# SIH26237 Cryptographic Design & Specification

## 1. Threat Model
The system addresses confidential document distribution across multiple potentially untrusted or partially untrusted recipient endpoints.
- **Insider Threat / Leaker**: An authorized recipient decrypts the confidential document using legitimate credentials and leaks it externally.
- **Framing / Repudiation Attack**: A dishonest party attempts to fabricate evidence framing an innocent recipient or deny an authentic decryption action.
- **Harvest-Now-Decrypt-Later (HNDL)**: Adversaries intercept network-distributed encrypted packages to decrypt them once cryptanalytically relevant quantum computers (CRQCs) exist.
- **Cryptographic Assumptions**: Classical hardness of AES-256-GCM and SHA-256; Post-quantum hardness of Module Learning With Errors (M-LWE) and Module Short Integer Solution (M-SIS) lattice problems (FIPS 203 & FIPS 204).

---

## 2. Standardized Cryptographic Primitives
| Operation | Algorithm Standard | Parameters | Security Strength |
| :--- | :--- | :--- | :--- |
| **Key Encapsulation** | NIST FIPS 203 (ML-KEM-768) | $k=3, \eta_1=2, \eta_2=2$ | NIST Security Category 3 (AES-192 equivalent quantum hardness) |
| **Digital Signatures** | NIST FIPS 204 (ML-DSA-65) | $(k, l)=(6, 5), \gamma_1=2^{19}$ | NIST Security Category 3 (EUF-CMA / SUF-CMA secure) |
| **Payload Encryption** | NIST SP 800-38D (AES-256-GCM) | 256-bit key, 96-bit unique IV, 128-bit tag | 256-bit symmetric security |
| **Key Derivation** | RFC 5869 (HKDF-SHA256) | Extract-and-Expand with domain separation | 256-bit pseudo-random security |
| **Tamper-Evident Ledger** | SHA-256 Chained Hash Graph | $H_n = \text{SHA256}(\text{CanonicalJSON}(E_n))$ | Preimage and collision resistance |

---

## 3. Cryptographic Key Hierarchy

```
[Master / Issuer Key Material]
      |
      +---> Document Session: Ephemeral K_doc (256-bit AES-GCM Key, os.urandom(32))
                 |
                 +---> Recipient 1: ML-KEM-768 Shared Secret (ss_1)
                 |          |
                 |          +---> HKDF-SHA256 Domain Separation ---> K_wrap,1
                 |                     |
                 |                     +---> AES-KW(K_wrap,1, K_doc) ---> Wrapped Doc Key 1
                 |
                 +---> Recipient 2: ML-KEM-768 Shared Secret (ss_2)
                 |          |
                 |          +---> HKDF-SHA256 Domain Separation ---> K_wrap,2
                 |                     |
                 |                     +---> AES-KW(K_wrap,2, K_doc) ---> Wrapped Doc Key 2
                 |
                 +---> Recipient N: ML-KEM-768 Shared Secret (ss_N)
                            |
                            +---> HKDF-SHA256 Domain Separation ---> K_wrap,N
                                       |
                                       +---> AES-KW(K_wrap,N, K_doc) ---> Wrapped Doc Key N
```

---

## 4. Document Encryption (AES-256-GCM)
1. Document $M$ is hashed: $\text{ORIGINAL\_DOCUMENT\_HASH} = \text{SHA-256}(M)$.
2. Ephemeral key $K_{doc} \leftarrow \{0,1\}^{256}$ is generated.
3. Nonce $IV \leftarrow \{0,1\}^{96}$ is generated uniformly at random.
4. Authenticated Associated Data ($AD$) binds the release and document context:
   $$AD = \text{"DOC-RELEASE:"} \parallel \text{release\_id} \parallel \text{":"} \parallel \text{document\_id}$$
5. Ciphertext $C$ and authentication tag $T$ are computed:
   $$(C, T) = \text{AES-256-GCM-Encrypt}(K_{doc}, IV, M, AD)$$

---

## 5. Recipient Key Encapsulation & Domain Separation
For each recipient $R_i$ with public key $PK_{R_i}$:
1. Key Encapsulation:
   $$(c_i, ss_i) = \text{ML-KEM-768.Encaps}(PK_{R_i})$$
2. Domain-Separated HKDF-SHA256 derivation:
   $$\text{Salt} = \text{SHA-256}(\text{"SALT:"} \parallel \text{protocol\_version} \parallel \text{":"ML-KEM-768:"} \parallel \text{release\_id})$$
   $$\text{Info} = \text{"DOC-KEY-WRAP:"} \parallel \text{protocol\_version} \parallel \text{":ML-KEM-768:REL="} \parallel \text{release\_id} \parallel \text{":DOC="} \parallel \text{document\_id} \parallel \text{":REC="} \parallel R_i$$
   $$K_{wrap, i} = \text{HKDF-Expand}(\text{HKDF-Extract}(\text{Salt}, ss_i), \text{Info}, 32)$$
3. Key Wrapping with authenticated context:
   $$\text{WrapAD} = \text{"KEY-WRAP-AUTH:"} \parallel \text{release\_id} \parallel \text{":"} \parallel R_i$$
   $$W_i = \text{AES-256-GCM-Encrypt}(K_{wrap, i}, IV_{wrap}, K_{doc}, \text{WrapAD})$$

Package $P_i$ contains:
$$\{release\_id, document\_id, R_i, c_i, W_i, IV, T, C, \text{ORIGINAL\_DOCUMENT\_HASH}\}$$

---

## 6. Decryption Provenance & ML-DSA Signatures
Upon authorized decapsulation and decryption by recipient $R_i$:
1. $R_i$ executes ML-KEM-768.Decaps$(SK_{KEM, R_i}, c_i) \rightarrow ss_i$.
   - **Implicit Rejection (FIPS 203)**: If $c_i$ or $SK$ is mismatched, a pseudorandom secret is derived; unwrapping $K_{doc}$ subsequently fails the authentication tag.
2. $K_{wrap, i}$ is derived via identical HKDF domain separation.
3. $K_{doc}$ is unwrapped and document $M$ is decrypted and verified against $\text{ORIGINAL\_DOCUMENT\_HASH}$.
4. A traceable copy $M_{trace, i}$ is generated with embedded marker $T_i$.
5. Recipient signs the provenance event using private signing key $SK_{DSA, R_i}$:
   $$\text{Payload} = \text{"DECRYPTION\_PROVENANCE:"} \parallel event\_id \parallel \text{":"} \parallel document\_id \parallel \text{":"} \parallel release\_id \parallel \text{":"} \parallel R_i \parallel \text{":"} \parallel \text{LEAK\_ARTIFACT\_HASH} \parallel \text{":"} \parallel \text{previous\_event\_hash} \parallel \text{":"} \parallel timestamp$$
   $$\sigma_i = \text{ML-DSA-65.Sign}(SK_{DSA, R_i}, \text{Payload})$$
6. Event is recorded to the hash-chained tamper-evident ledger.

---

## 7. Document Hashing & Lifecycle Identity
To prevent semantic confusion, three distinct cryptographic hashes are enforced across the lifecycle:
1. `ORIGINAL_DOCUMENT_HASH`: SHA-256 hash of the pristine plaintext document before distribution.
2. `RELEASE_ARTIFACT_HASH`: SHA-256 hash of the encrypted release payload / package.
3. `LEAK_ARTIFACT_HASH`: SHA-256 hash of the decrypted, recipient-specific traceable document copy.

---

## 8. Tamper-Evident Ledger Architecture
Events are cryptographically chained:
$$H_0 = 0^{64}$$
$$H_n = \text{SHA-256}(\text{CanonicalJSON}(E_n))$$
Where $E_n$ contains $previous\_event\_hash = H_{n-1}$.
Any retroactive tampering, event deletion, substitution, or reordering breaks the chain $H_n \neq H_{stored}$ and is detected during `verify_chain()`.

---

## 9. Traceability Boundary
- **Milestone v0.1**: Cryptographic marker binding $(document\_id, release\_id, recipient\_id, document\_hash)$ via HMAC-SHA256 authentication.
- **Fail-Closed Guarantee**: Missing, corrupted, modified, or forged markers result in strict `ABSTAIN` (states `NO_SIGNAL` or `INSUFFICIENT_EVIDENCE`).
- **Handoff Boundary**: Abstract interface `TraceabilityProvider` allows modular addition of collusion-resistant `TardosProvider` and visual watermarking without altering cryptographic release or ledger layers.

---

## 10. Known Cryptographic Limitations
- **Side-Channel Protections**: The current Python reference implementations (`kyber_py` / `dilithium_py`) prioritize mathematical correctness and auditability. Hardware-level power analysis / timing side-channel attacks on endpoints are not addressed without OS-level constant-time C/assembly hardware extensions.
- **Key Storage**: Recipient private keys in v0.1 are stored locally in application memory. Hardware token (PKCS#11 / TPM / HSM) binding is deferred to later milestones.
