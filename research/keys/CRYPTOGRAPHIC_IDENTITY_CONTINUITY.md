# AegisTrace Cryptographic Identity Continuity

**Document ID:** AEGIS-THEORY-IDENTITY-CONTINUITY-01  
**Classification:** Cryptographic Identity Architecture  
**Subsystem:** Core Cryptography (`core/crypto/lifecycle/`)  
**Status:** Implemented & Formally Verified  

---

## 1. The Identity vs. Credential Dichotomy

A common pitfall in forensic attribution systems is conflating **Identity** with **Cryptographic Material**:
- If an entity's identity is defined solely by their public key, rotating the key creates a "new person," breaking historical evidence chains and lineage trees.
- Conversely, if an identity is merely a mutable database username, key rotation can be exploited by an adversary to perform repudiation attacks ("I didn't leak that document in 2024; my current key is different").

AegisTrace establishes a rigorous, mathematically sound decoupling:

$$\text{Entity Identity } \mathcal{I} = \text{Invariant UUID} \quad (\text{e.g. } \texttt{rec\_alice\_7b82})$$
$$\text{Authorization Credential } \mathcal{C}(t) = \langle \texttt{key\_id}, \text{Algorithm}, \text{Epoch}, [T_{\text{start}}, T_{\text{end}}] \rangle$$

At any forensic verification moment $t_0$, the attribution function maps:

$$\mathcal{A}(\text{Signature}, t_0) \xrightarrow{\text{Resolver}} \mathcal{C}(t_0) \xrightarrow{\text{Lineage}} \mathcal{I}$$

```
+----------------------------------------------------------------------------------------------------+
|                                    IDENTITY CONTINUITY TIMELINE                                    |
+------------------------------------+---------------------------------------------------------------+
| Identity                           | rec_alice_7b82 (PERMANENT, IMMUTABLE)                         |
| Epoch 1 (2024-2025)                | Key K_1 (ML-DSA-65: kid_01) -> Signed Document A             |
| Epoch 2 (2025-2026)                | Key K_2 (ML-DSA-65: kid_02) -> Signed Document B             |
| Epoch 3 (2026-Present)             | Key K_3 (ML-DSA-65: kid_03) -> Signed Document C             |
+------------------------------------+---------------------------------------------------------------+
| Forensic Resolution in 2027:       | Document A unambiguously attributed to rec_alice_7b82 via K_1 |
|                                    | Document B unambiguously attributed to rec_alice_7b82 via K_2 |
+------------------------------------+---------------------------------------------------------------+
```

---

## 2. Multi-Algorithm & Post-Quantum Continuity

Because `KeyLifecycleManager` indexes records by the composite tuple:

$$\langle \text{Owner}, \text{KeyType}, \text{Algorithm}, \text{TenantID} \rangle$$

A single recipient identity $\mathcal{I}$ simultaneously maintains distinct, non-interfering key lifecycles for:
1. **Digital Signatures**: ML-DSA-65 (NIST FIPS 204)
2. **Key Encapsulation**: ML-KEM-768 (NIST FIPS 203)
3. **Device Attestation**: P-256 ECDSA (FIPS 186-4 / FIDO2)

When an organization rotates its signing key from classical ECDSA to post-quantum ML-DSA-65:
- The `recipient_id` remains unchanged.
- Historical ECDSA signatures on older ledger receipts remain valid under the ECDSA historical index.
- New receipts require post-quantum ML-DSA-65 signatures under the active ML-DSA index.

---

## 3. Hardware Device Identity Continuity

In high-assurance deployments, users operate physical hardware tokens (TPM chips, FIDO2 security keys). 

When a user upgrades or replaces their hardware token:
1. `DeviceKeyLifecycleAdapter.rotate_device_key(device_id, new_pub_pem)` is invoked.
2. The `device_id` remains constant (`dev_workstation_44a`).
3. The old hardware key is retired in the device's key chain with explicit predecessor/successor pointers.
4. Historical hardware attestation receipts from previous years verify against the retired hardware key, while new session attestations must be signed by the newly enrolled token.

---

## 4. Evidence Fusion & Non-Repudiation Invariance

In court or formal tribunal proceedings, an accused recipient might claim:
> *"The leaked document bears a signature from a key I no longer hold. Therefore, the attribution is invalid."*

AegisTrace completely refutes this defense through **Cryptographic Identity Continuity**:
1. **Immutable Ledger Block**: The permissioned DLT contains the exact Decryption Receipt signed at time $T_E$ by key $K_1$.
2. **Merkle Inclusion Proof**: Proves that the receipt was permanently committed into Block $H$ prior to $K_1$'s retirement.
3. **Key Lifecycle Audit Trail**: Proves that at time $T_E$, $K_1$ was in the `ACTIVE` state and owned exclusively by `recipient_id`.
4. **Succession Pointer**: Proves that $K_1$'s registered successor is $K_2$, proving key ownership continuity under the same legal entity.

This mathematically guarantees **absolute non-repudiation** across the entire lifecycle of the document and recipient.
