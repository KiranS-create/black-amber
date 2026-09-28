# AegisTrace Backup Format & Content-Addressed Specification

## 1. Overview & Serialization Invariants

AegisTrace backup files are structured as deterministic, self-describing cryptographic packages. Every object and manifest is formatted to guarantee bitwise reproducibility across disparate architectures (POSIX, Windows, ARM64, x86_64).

### Serialization Rules (RFC 8785 JSON Canonicalization)
1. Keys are sorted lexicographically by Unicode code point.
2. No extraneous whitespace: separators are strictly `','` and `':'`.
3. Floats and numbers must use deterministic representations.
4. Timestamps are formatted as ISO-8601 UTC strings with second precision: `YYYY-MM-DDTHH:MM:SSZ`.
5. Binary payloads are base64-encoded with standard RFC 4648 alphabet.

---

## 2. Directory & Storage Hierarchy

A backup archive consists of a signed manifest accompanied by content-addressed chunk files:

```
backup_root/
├── manifests/
│   ├── bak_9c4e2a81_manifest.json          # Canonical signed manifest
│   └── bak_9c4e2a81_manifest.sig           # Detached ML-DSA-65 signature (optional)
├── objects/
│   ├── sha256/
│   │   ├── 4a/
│   │   │   └── 4a1f8b2c9...                # Content-addressed chunk file
│   │   ├── b2/
│   │   │   └── b2874cf30...                # Content-addressed chunk file
│   │   └── ...
└── audit/
    └── recovery_audit_chain.jsonl          # Independent tamper-evident audit trail
```

---

## 3. Object Header & Content Addressing

Every logical dataset entity (or batch of entities) is serialized canonically and hashed via `SHA-256`.

$$\text{Object ID} = \text{SHA-256}(\text{Canonical JSON Payload})$$

### 3.1. Object Record Schema (`BackupObjectRecord`)
```json
{
  "object_id": "8510ea8378dd95c0cb531c3669a75296e931310f049bd13b186aea5a4ce8eba9",
  "dataset_type": "ledger_events",
  "tenant_id": "tenant_prod_01",
  "byte_size": 4812,
  "object_count": 25,
  "created_at": "2026-09-27T12:00:00Z"
}
```

---

## 4. Double-Domain RFC 6962 Merkle Commitment Tree

To prevent second-preimage and length-extension vulnerabilities, the `merkle_root` recorded in the backup manifest is computed over all sorted `object_id` values according to RFC 6962 double-domain hashing:

1. **Leaf Hash**:
   $$\text{Leaf}_i = \text{SHA-256}(0x00 \parallel \text{object\_id}_i)$$
2. **Interior Node**:
   $$\text{Parent}(L, R) = \text{SHA-256}(0x01 \parallel L \parallel R)$$
3. **Odd Node Duplication**: If a layer has an odd number of nodes, the last node is paired with itself:
   $$\text{Parent}(L, L) = \text{SHA-256}(0x01 \parallel L \parallel L)$$

---

## 5. Envelope Encryption Architecture (AES-256-GCM + HKDF)

When backup encryption is enabled, payloads are encrypted before persistence:

```
+-----------------------------------------------------------------------+
| Envelope Header:                                                      |
|   - algorithm: "AES-256-GCM"                                          |
|   - kdf: "HKDF-SHA256"                                                |
|   - salt_b64: Base64(16 bytes)                                        |
|   - nonce_b64: Base64(12 bytes)                                       |
|   - ciphertext_b64: Base64(N bytes)                                   |
|   - tag_b64: Base64(16 bytes authentication tag)                      |
|                                                                       |
| Authenticated Additional Data (AAD):                                  |
|   {"backup_id":"...","sequence":1,"tenant_id":"...","version":"2.0.0"}|
+-----------------------------------------------------------------------+
```

### Key Derivation
$$\text{Salt} \leftarrow \text{Random}(16 \text{ bytes})$$
$$\text{DerivedKey} = \text{HKDF-Expand}(\text{HKDF-Extract}(\text{Salt}, \text{Passphrase}), \text{"AegisTrace-Backup-Encryption-v2"}, 32)$$

### Authenticated Additional Data (AAD) Binding
Modifying any header field or swapping backup files across tenants causes GCM authentication tag verification to fail immediately.

---

## 6. Manifest Specification (`SignedBackupManifest`)

The manifest contains all metadata required for self-contained verification:

```json
{
  "manifest_version": "2.0.0",
  "backup_id": "bak_0a8b7c6d5e4f3a21",
  "tenant_id": "tenant_defense_hq",
  "backup_type": "DELTA",
  "backup_sequence": 7,
  "created_at": "2026-09-27T14:30:00Z",
  "parent_backup_id": "bak_0a8b7c6d5e4f3a20",
  "parent_backup_commitment": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "application_version": "2.0.0",
  "datasets": [
    "ledger_events",
    "lineage_copies",
    "telemetry_events"
  ],
  "objects": [
    {
      "object_id": "1c7a2...",
      "dataset_type": "ledger_events",
      "tenant_id": "tenant_defense_hq",
      "byte_size": 2048,
      "object_count": 10,
      "created_at": "2026-09-27T14:30:00Z"
    }
  ],
  "merkle_root": "5f4dcc3b5aa765d61d8327deb882cf99...",
  "cryptographic_digest": "4a1f8b2c...",
  "is_encrypted": true,
  "encryption_algorithm": "AES-256-GCM",
  "key_derivation_algorithm": "HKDF-SHA256",
  "signer_id": "admin_signing_key_01",
  "signer_public_key_b64": "...",
  "signature_b64": "..."
}
```

---

## 7. Verification Algorithm

To verify a backup without restoring:
1. Verify manifest JSON format and assert `manifest_version == "2.0.0"`.
2. Extract `signature_b64` and `cryptographic_digest`.
3. Compute canonical representation of manifest with empty signature/digest fields.
4. Recompute `SHA-256` digest and assert equality with `cryptographic_digest`.
5. Verify ML-DSA-65 signature over canonical bytes using the embedded or authoritative public key.
6. Verify Merkle root matches the recomputed RFC 6962 root of sorted object IDs.
7. For each object, verify its SHA-256 matches its `object_id`.
