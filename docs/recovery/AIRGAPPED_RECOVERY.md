# AegisTrace Air-Gapped Recovery Media & Offline Site Replacement

## 1. Architectural Philosophy & Threat Model

In national security and defense operations, forensic evidentiary platforms are frequently deployed within SCIFs (Sensitive Compartmented Information Facilities) or air-gapped network enclaves with zero external internet connectivity.

Under catastrophic physical disaster or total enclave compromise:
1. No external key management services (AWS KMS, Azure Key Vault, Google Cloud KMS) can be reached.
2. No online CRL / OCSP revocation endpoints can be queried.
3. No package managers or dependencies can be downloaded.

The recovery subsystem must support complete, standalone bare-metal rehydration from physical, write-once, post-quantum self-authenticating media.

---

## 2. Portable Media Structure & Layout

An AegisTrace Air-Gapped Recovery Media package is formatted as follows:

```
/
├── BOOT/
│   ├── aegis_bootstrap_loader.sh          # Immutable bootstrap script
│   └── sha256sums.txt                     # Checksums of all bootstrap binaries
├── MEDIA_MANIFEST.json                    # Canonical manifest with ML-DSA-65 signature
├── SCHEMAS/
│   ├── v2_manifest.schema.json            # Pydantic/JSON schema for manifests
│   └── v2_audit.schema.json               # Schema for audit logs
├── BACKUPS/
│   ├── FULL_bak_0001/                     # Baseline full backup
│   │   ├── manifest.json
│   │   └── objects/
│   └── DELTA_bak_0002/                    # Verified incremental delta
├── KEYS/
│   ├── root_authority_pubkey.bin          # Root authority ML-DSA-65 public key
│   └── validator_quorum_pubkeys.json      # Quorum public keys
└── AUDIT/
    └── historical_audit_chain.jsonl       # Tamper-evident audit chain
```

---

## 3. Media Manifest Specification (`RecoveryMediaManifest`)

The media manifest indexes every file payload with its content SHA-256 and byte size:

```json
{
  "manifest_version": "2.0.0",
  "media_id": "media_offline_site_alpha_2026",
  "created_at": "2026-09-27T15:00:00Z",
  "signing_authority_id": "root_ciso_offline_hsm",
  "media_root_hash": "c5d1e2...",
  "file_entries": [
    {
      "relative_path": "BOOT/aegis_bootstrap_loader.sh",
      "sha256_hash": "4a1f8b...",
      "byte_size": 2408
    },
    {
      "relative_path": "SCHEMAS/v2_manifest.schema.json",
      "sha256_hash": "9b2c3d...",
      "byte_size": 1540
    }
  ],
  "signer_public_key_b64": "...",
  "signature_b64": "..."
}
```

---

## 4. Bare-Metal Offline Rehydration Procedure (Scenario J)

When a replacement server is provisioned inside an air-gapped facility:

### Step 1: Mount Media & Initialize Builder
```python
from core.recovery.media import AirGappedMediaBuilder

# Ingest all files from physical media
file_payloads = {
    "BOOT/aegis_bootstrap_loader.sh": load_bytes("/media/BOOT/aegis_bootstrap_loader.sh"),
    "SCHEMAS/v2_manifest.schema.json": load_bytes("/media/SCHEMAS/v2_manifest.schema.json"),
    ...
}
```

### Step 2: Cryptographic Self-Authentication
The platform verifies the media manifest using the Root Authority's offline public key:
```python
is_valid, err = AirGappedMediaBuilder.verify_recovery_media(
    manifest=media_manifest,
    file_payloads=file_payloads,
    authority_public_key_bytes=root_authority_public_key
)
if not is_valid:
    raise SecurityError(f"AIR_GAPPED_MEDIA_VERIFICATION_FAILED: {err}")
```
- Recomputes SHA-256 for every file on disk and verifies against manifest entries.
- Recomputes RFC 6962 Merkle tree over all file entries.
- Validates the ML-DSA-65 post-quantum signature over the canonical manifest bytes.

### Step 3: Reconstitute Enclave Services
1. Load and initialize the `ContentAddressedStore` from media backups.
2. Ingest the base FULL backup and sequential DELTA backups via `DisasterRecoveryEngine`.
3. Re-verify ledger integrity and Merkle roots.
4. Re-establish Byzantine validator consensus quorum.
5. Record the offline bare-metal bootstrap event in the `RecoveryAuditLog`.
