# AegisTrace Evidence Package Format Specification (v1.0)
**Standard:** NIST FIPS 204 (ML-DSA-65) | RFC 6962 | RFC 8785 (Canonical JSON)  
**Security Classification:** Strict Compartmentalization & Air-Gapped Verification  
**Author:** AegisTrace Cryptographic Architecture Group  

---

## 1. Executive Overview

In zero-trust digital forensics and leak investigation, an evidentiary claim is only as trustworthy as the independent verification boundary surrounding it. Traditional forensic reports—such as static PDF documents embedded with SHA-256 checksums—suffer from four fatal flaws:
1. **Implicit Trust:** They rely on trust in the originating database, application server, or cloud KMS.
2. **Fragile Serialization:** Hash calculations vary based on key ordering, whitespace, and floating-point representations.
3. **No Mathematical Grounding:** Conclusions are stated textually rather than mathematically deduced from empirical evidence nodes through a validated dependency graph.
4. **Quantum Vulnerability:** Traditional signatures (RSA-PSS, ECDSA P-256/Ed25519) will be invalidated by Shor's algorithm on cryptanalytically relevant quantum computers (CRQC).

The **AegisTrace Evidence Package Format** defines an immutable, self-contained, content-addressed, post-quantum digitally signed container for forensic evidence. It converts raw forensic investigation outputs into a portable archive that can be completely audited by an external magistrate, judicial examiner, or foreign intelligence agency with **zero network access, zero database connectivity, and zero server dependencies**.

---

## 2. Container Architecture & Directory Layout

An AegisTrace evidence package exists either as a directory structure or as an unencrypted, deflate-compressed `.zip` archive.

```
evidence_package_pkg_case_2026_audit_001/
├── manifest.json                  # Root package manifest (RFC 8785 canonical JSON)
├── signature.json                 # Post-quantum ML-DSA-65 signature over manifest
├── objects/                       # Content-addressed evidence objects
│   ├── case_case_2026_audit_001.json
│   ├── art_leak_pdf.json
│   ├── wm_extracted_01.json
│   ├── receipt_decrypt_alice.json
│   ├── idproof_rec_officer_alice.json
│   ├── lp_block_5001.json
│   ├── lineage_tree_01.json
│   ├── tel_session_alice_01.json
│   └── decision_final_01.json
├── edges/                         # Directional dependency DAG edges
│   ├── edge_0000_decision_to_wm.json
│   ├── edge_0001_decision_to_receipt.json
│   └── edge_0002_wm_to_artifact.json
└── custody/                       # Append-only cryptographic chain of custody
    └── chain_of_custody.json      # Sequenced event list H_i = SHA256(H_{i-1} || payload)
```

---

## 3. Canonical Serialization & Content-Addressing Invariant

To guarantee that hashes computed on Windows, Linux, macOS, or specialized forensic hardware produce identical bitstreams, all serialization conforms to RFC 8785:

$$\text{CanonicalJSON}(O) = \text{serialize}(O, \text{sort\_keys}=\text{True}, \text{separators}=(',', ':'), \text{ensure\_ascii}=\text{False})$$

### Content Hash Preimage
For every evidence object $O$ in `objects/`, its canonical content digest is computed strictly by excluding the `content_hash` field itself:

$$H(O) = \text{SHA-256}(\text{CanonicalJSON}(O \setminus \{\text{content\_hash}\}))$$

When stored, $O.\text{content\_hash} = H(O)$. Any alteration to a single character, timestamp, confidence float, or enum string mutates $H(O)$, causing instant failure during verification.

---

## 4. RFC-6962 Double-Domain Evidence Merkle Tree

All evidentiary objects in the package are committed into a balanced binary Merkle tree inspired by RFC 6962 (Certificate Transparency). To prevent second-preimage length-extension and leaf-node substitution attacks, domain separation prefixes are strictly enforced:

* **Leaf Domain Prefix:** `0x00`
* **Branch Domain Prefix:** `0x01`

$$\text{LeafHash}(h_i) = \text{SHA-256}(0\text{x}00 \parallel \text{bytes.fromhex}(h_i))$$

$$\text{NodeHash}(L, R) = \text{SHA-256}(0\text{x}01 \parallel \text{bytes.fromhex}(L) \parallel \text{bytes.fromhex}(R))$$

### Deterministic Leaf Ordering
Before computing the Merkle tree, objects are sorted strictly in ascending lexicographical order by their `object_id`:

$$\text{SortedObjects} = \text{sort}(Objects, \text{key} = \lambda x: x.\text{object\_id})$$

The root of this tree is recorded in `manifest.evidence_merkle_root`.

---

## 5. The 17 Strongly-Typed Evidence Objects

The format defines 17 strongly-typed schemas:

| # | Evidence Object Class | Domain Purpose | Key Integrity Invariants |
|---|---|---|---|
| 1 | `CaseObject` | Formal investigation scope & classification | Bound to case identifier, tenant, and classification level. |
| 2 | `ArtifactEvidenceObject` | Physical or digital file analyzed | Contains SHA-256 digest, byte length, and MIME type. |
| 3 | `WatermarkEvidenceObject` | Extracted watermark carrier evidence | Extracted token, confidence score, BER/PSNR, detection state. |
| 4 | `DecryptionReceiptObject` | Recipient-side decryption proof | Recipient ML-DSA-65 signature on canonical confirmation payload. |
| 5 | `RecipientIdentityProofObject` | Historical public key certificate | Public key, key epoch, activation and revocation timestamps. |
| 6 | `DeviceEvidenceObject` | Hardware identity & attestation | TPM/Secure Enclave attestation status, hardware key ID. |
| 7 | `SessionEvidenceObject` | Active viewing / decryption session | Session nonce, ephemeral session key ID, expiration bounds. |
| 8 | `LineageEvidenceObject` | Document instance provenance graph | Root copy ID, target copy ID, last known holder, downstream gap flag. |
| 9 | `LedgerProofObject` | DLT block header & inclusion proof | Merkle audit path to receipt hash, proposer signature, quorum votes. |
| 10 | `TelemetryEvidenceObject` | Enclave / network logging signals | External event hash, source trust level, dependency relation. |
| 11 | `ChainOfCustodyEvent` | Append-only handler audit trail | Strict SHA-256 chaining to previous custody event link. |
| 12 | `AttributionDecisionObject` | Grounded forensic conclusion | Attribution state (`ATTRIBUTED`, `ABSTAINED`), principal ID, hypothesis. |
| 13 | `DependencyEdge` | Directed edge in evidence DAG | Source ID, Target ID, `TelemetryDependencyRelation`. |
| 14 | `RedactedEvidenceStub` | Cryptographic surrogate for private nodes | Preserves original `content_hash` and `object_id` to maintain Merkle root. |
| 15 | `PackageManifest` | Cryptographic inventory and root digest | Case ID, tenant ID, Merkle root, DAG root, decision reference. |
| 16 | `PackageSignature` | Post-quantum manifest signature | ML-DSA-65 public key, manifest digest, signature bytes. |
| 17 | `VerificationResult` | Machine-readable audit report | 12-pillar validation flags, error log, overall verdict. |

---

## 6. Cryptographic Safe Redaction Model

In sensitive investigations, certain evidence objects (such as classified operational names, internal IP addresses, or unrelated recipient keys) must be redacted prior to sharing with external tribunals or third parties. 

Traditional redaction destroys cryptographic hashes and invalidates signatures. AegisTrace solves this via **Cryptographic Safe Redaction**:

1. A redacted object $O$ is replaced with a `RedactedEvidenceStub`.
2. The stub retains the exact original `object_id` and original `content_hash`:
   $$\text{Stub}.\text{content\_hash} = O.\text{content\_hash}$$
3. Because the leaf hash in the sorted inventory remains identical, **the Merkle root is 100% preserved**:
   $$\text{MerkleRoot}(\text{RedactedPackage}) = \text{MerkleRoot}(\text{OriginalPackage})$$
4. The manifest signature remains valid because `is_redacted` and `redacted_object_ids` are metadata envelope attributes excluded from the signed manifest digest:
   $$\text{ManifestDigest} = \text{SHA-256}(\text{CanonicalJSON}(\text{Manifest} \setminus \{\text{is\_redacted}, \text{redacted\_object\_ids}\}))$$
5. Explicit classification tags are enforced on each stub:
   * `REDACTED`: Content withheld for security/privacy.
   * `NOT_INCLUDED`: Content omitted from this specific export tier.
   * `NOT_REQUIRED_FOR_THIS_PROOF`: Ancillary data uncontested in current tribunal.

---

## 7. Post-Quantum Package Signing (ML-DSA-65)

To guarantee long-term evidentiary durability against quantum decryption and forgery:
* Packages are signed using **NIST FIPS 204 (ML-DSA-65)** (formerly CRYSTALS-Dilithium).
* The signed message is the canonical UTF-8 hex string of the manifest digest:
  $$\sigma = \text{ML-DSA-65.Sign}(SK_{\text{examiner}}, \text{ManifestDigest})$$
* **Non-Embedding Invariant:** The private signing key $SK_{\text{examiner}}$ is **NEVER** stored or bundled inside the evidence package. Only the public key $PK_{\text{examiner}}$ and signature $\sigma$ are stored in `signature.json`.
