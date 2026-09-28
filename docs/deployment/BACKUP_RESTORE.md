# Cryptographic Backup & Restoration Runbook

> **Platform Scope**: Enterprise Ledger & Evidence Persistence.  
> **Desktop Status**: Standalone native desktop distributions are **DEFERRED TO FUTURE WORKSTREAM**. Backup & restoration commands operate across standard server container volumes.

---

## 1. Backup Scope & Data Directories

AegisTrace maintains state in two dedicated data paths:
1. `SIH_DATA_DIR` (`data/`): Contains the SQLite transaction database, recipient public keys, and cryptographic hash chains.
2. `artifacts/`: Contains encrypted document envelopes, watermarked release payloads, and signed `.zip` evidence dossiers.

```
data/
├── dlt_ledger.db          # Cryptographic Merkle event blocks
├── identities.db          # Enrolled public keys (ML-KEM / ML-DSA)
└── provenance.db          # Decryption receipts and causal graph
artifacts/
├── releases/              # Key encapsulated payloads
└── evidence/              # Sealed forensic evidence packages
```

---

## 2. Automated Hot Backup Procedure

Run the backup script while the service is live (SQLite WAL mode permits zero-downtime hot snapshots):

```bash
# Set timestamp variable
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/aegistrace_${BACKUP_DATE}"

mkdir -p "${BACKUP_DIR}"

# 1. Vacuum SQLite databases into backup snapshot
sqlite3 data/dlt_ledger.db ".backup '${BACKUP_DIR}/dlt_ledger.db'"
sqlite3 data/identities.db ".backup '${BACKUP_DIR}/identities.db'"

# 2. Archive artifact storage directory
tar -czf "${BACKUP_DIR}/artifacts.tar.gz" artifacts/

# 3. Generate cryptographic SHA-256 manifest of the backup
cd "${BACKUP_DIR}"
sha256sum * > SHA256SUMS
cd -

echo "Cryptographic backup completed: ${BACKUP_DIR}"
```

---

## 3. Restoration Procedure

### 3.1 Pre-Restoration Verification
Before restoring into an environment, verify that the backup manifest matches the files:

```bash
cd "backups/aegistrace_YYYYMMDD_HHMMSS"
sha256sum -c SHA256SUMS
```
All files must report `OK`.

### 3.2 Restore into Application Directory
1. Stop the AegisTrace service:
   ```bash
   docker compose down
   # or terminate local uvicorn process
   ```

2. Restore database files:
   ```bash
   cp backups/aegistrace_YYYYMMDD_HHMMSS/dlt_ledger.db data/dlt_ledger.db
   cp backups/aegistrace_YYYYMMDD_HHMMSS/identities.db data/identities.db
   ```

3. Extract artifact packages:
   ```bash
   tar -xzf backups/aegistrace_YYYYMMDD_HHMMSS/artifacts.tar.gz -C ./
   ```

4. Start AegisTrace:
   ```bash
   docker compose up -d
   ```

---

## 4. Post-Restoration Cryptographic Audit

Immediately following restoration, run the ledger audit to verify that no hash chain links were corrupted:

```bash
curl -X POST http://localhost:8000/ledger/verify
```
Expected response:
```json
{
  "is_valid": true,
  "total_events": 42,
  "tampered_block_index": null,
  "head_hash": "a1b2c3d4e5f6..."
}
```
If `is_valid` is `true`, the restoration is cryptographically intact and certified for operations.
