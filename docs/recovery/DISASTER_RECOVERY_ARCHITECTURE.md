# AegisTrace Disaster Recovery & Forensic State Recovery Architecture

## 1. Architectural Mission & Core Principles

AegisTrace is a mission-critical forensic security and document attribution platform. In high-stakes national security, intelligence, defense, and enterprise environments, the platform's evidentiary records must remain tamper-evident, non-repudiable, and court-admissible even under catastrophic physical destruction, cloud hypervisor outages, malicious operator compromise, database corruption, or targeted adversarial tampering.

Disaster Recovery in AegisTrace is governed by three non-negotiable principles:
1. **Fail-Closed Forensics**: Any corruption, hash discrepancy, sequence gap, parent mismatch, cross-tenant substitution, or unauthorized rollback results in an immediate fail-closed state (`ABSTAIN` / `RECOVERY_FAILED` / `ROLLBACK_DETECTED`). The platform refuses to manufacture speculative state or accept unverified artifacts.
2. **Cryptographic Self-Authentication**: All backups are content-addressed (`SHA-256`), Merkle-committed (RFC 6962), and signed using post-quantum digital signatures (`ML-DSA-65` / Dilithium) bound to cryptographic hardware identities.
3. **Non-Circular Trust**: Evidentiary audit logs and recovery manifests do not rely on the state being recovered. The audit trail is an independent, append-only hash chain enforcing separation of duties.

---

## 2. 24-Component Forensic State Catalog

Every stateful component in AegisTrace is classified into one of three Criticality Tiers with specific recovery requirements and reconstructive semantics:

| Subsystem Component | Criticality Tier | State Class | Recoverability | RPO Target | RTO Target |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01. Recipient Key Material** | Tier 1 (Security-Critical) | Sovereign / HSM | Refuse Plaintext Export (Public Keys Only) | 0s (Instant) | < 60s |
| **02. Document Encryption Keys** | Tier 1 (Security-Critical) | Sovereign / KEK | Encrypted Key Packages (AES-256-GCM + ML-DSA-65) | 0s (Instant) | < 30s |
| **03. Master Keystore / Rotation** | Tier 1 (Security-Critical) | Cryptographic Store | Hash-chained Epoch Manifests | 0s (Instant) | < 30s |
| **04. Decryption Policy Database** | Tier 1 (Security-Critical) | Authorization Rules | Exact Cryptographic Replication | < 1s | < 15s |
| **05. Recipient Identity Directory**| Tier 1 (Security-Critical) | Identity Store | Verified Signatures & Certificates | < 1s | < 60s |
| **06. Device Attestation Cache** | Tier 2 (Operational) | Hardware Tokens | Reconstituted from Authenticated Hardware | < 60s | < 120s |
| **07. Tamper-Evident Ledger** | Tier 1 (Evidence-Critical) | Sequential Hash Chain | Exact Cryptographic Replication (RFC 6962) | 0s (Tx Final) | < 30s |
| **08. Merkle Tree Checkpoints** | Tier 1 (Evidence-Critical) | Tree Commitments | Exact Root Recomputation | 0s (Block Final)| < 15s |
| **09. Lineage Graph Roots** | Tier 1 (Evidence-Critical) | Root Commitments | Exact Graph Node Preservation | 0s (Tx Final) | < 30s |
| **10. Lineage Copy Instances** | Tier 1 (Evidence-Critical) | DAG Edges | DAG Reconstitution & Cycle Prevention | 0s (Tx Final) | < 30s |
| **11. Lineage Session Nodes** | Tier 2 (Operational) | Ephemeral Lineage | Deduplicated Ingestion | < 1s | < 60s |
| **12. Lineage Sparse Index** | Tier 3 (Derivable Index) | Performance Index | 100% Reconstituted from Authoritative Roots/Copies | Derivable | < 120s |
| **13. Dynamic Watermark Commitments** | Tier 1 (Evidence-Critical)| Token Hashes | Exact Cryptographic Replication | 0s (Tx Final) | < 30s |
| **14. Watermark Codebooks** | Tier 1 (Security-Critical) | Secret Parameters | Deterministic Recomputation via Keystore Seed | 0s (Instant) | < 30s |
| **15. EDR Telemetry Events** | Tier 2 (Evidence-Critical) | High-volume Stream | Deduplicated Append (SHA-256 Fingerprint) | < 1s | < 60s |
| **16. Print Spooler Events** | Tier 2 (Evidence-Critical) | OS Logs | Deduplicated Append (SHA-256 Fingerprint) | < 5s | < 60s |
| **17. DLP Incident Records** | Tier 2 (Evidence-Critical) | Security Alerts | Deduplicated Append (SHA-256 Fingerprint) | < 1s | < 60s |
| **18. Identity Provider Logs** | Tier 2 (Operational) | Auth Logs | Deduplicated Append (SHA-256 Fingerprint) | < 5s | < 60s |
| **19. Multi-Channel Evidence Store** | Tier 1 (Evidence-Critical)| Forensic Bundles | Content-Addressed Target-Bound Recovery | 0s (Tx Final) | < 30s |
| **20. Attribution Case Files** | Tier 1 (Evidence-Critical) | Forensic Analyses | Exact Sealed Archive Verification | 0s (Sealed) | < 30s |
| **21. BFT Validator Node State** | Tier 1 (Security-Critical) | Replicated Blocks | BFT Quorum Reconciliation & Tip Check | 0s (Consensus) | < 60s |
| **22. Tenant Isolation Policies** | Tier 1 (Security-Critical) | Boundary Rules | Cryptographic Tenant Boundary Enforcement | 0s (Instant) | < 15s |
| **23. Recovery Audit Hash Chain** | Tier 1 (Security-Critical) | Chained Audit Log | Independent Append-Only Hash Chain | 0s (Instant) | < 15s |
| **24. Air-Gapped Media Manifests** | Tier 1 (Security-Critical) | Offline Manifests | Offline ML-DSA-65 Signature Verification | 0s (Immutable) | < 30s |

---

## 3. Storage Architecture: Content-Addressed Store (CAS)

All backup payloads are decomposed into immutable, content-addressed objects:
- **Object ID**: `SHA-256` of canonical object JSON bytes.
- **RFC 6962 Merkle Commitment**: Backup packages compute an RFC 6962 double-domain Merkle root over sorted object hashes:
  $$\text{Leaf} = \text{SHA-256}(0x00 \parallel \text{object\_id})$$
  $$\text{Node} = \text{SHA-256}(0x01 \parallel \text{Left} \parallel \text{Right})$$
- **Envelope Encryption**: When encryption is requested, each object payload is encrypted with `AES-256-GCM` using a 256-bit symmetric key derived via `HKDF-SHA256` from a high-entropy passphrase and random salt.
- **Authenticated Additional Data (AAD)**: Every ciphertext envelope cryptographically binds:
  ```json
  {
    "tenant_id": "<tenant>",
    "backup_id": "<backup_id>",
    "backup_sequence": 12,
    "schema_version": "2.0.0"
  }
  ```
  Modifying any bit of the tenant, sequence, or backup metadata invalidates the GCM authentication tag, failing closed before decryption.

---

## 4. Cryptographic Manifest & Post-Quantum Signing

Backups are sealed by a canonical `SignedBackupManifest`:
```json
{
  "manifest_version": "2.0.0",
  "backup_id": "bak_9c4e2a81...",
  "tenant_id": "tenant_defense_01",
  "backup_type": "DELTA",
  "backup_sequence": 4,
  "created_at": "2026-09-27T14:00:00Z",
  "parent_backup_id": "bak_8b3d1f70...",
  "parent_backup_commitment": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
  "datasets": ["ledger_events", "lineage_copies"],
  "merkle_root": "a3b2c1d0...",
  "cryptographic_digest": "7f83b165...",
  "is_encrypted": true,
  "signer_id": "operator_offline_01",
  "signer_public_key_b64": "...",
  "signature_b64": "..."
}
```
- **Canonical Serialization**: Strictly ordered keys, no whitespace separators (`canonical_json_bytes`).
- **Signature Algorithm**: Post-Quantum NIST FIPS 204 **ML-DSA-65** (Dilithium-3 equivalent, Category 3 quantum security).
- **Offline Verifiability**: Verification relies only on public key cryptography, zero network access required.

---

## 5. Incremental Delta Chains & Monotonic Anti-Rollback

AegisTrace maintains continuous delta backup chains anchored by periodic full backups:
1. **Delta Commitments**: Each delta backup commits to `parent_backup_id` and the parent's exact `cryptographic_digest`.
2. **Chain Validation**: The `BackupChainManager` verifies the entire chain from the initial FULL backup through each delta, rejecting:
   - `MISSING_DELTA`: Gaps in sequence (e.g., delta 1, 3).
   - `REORDERED_DELTA`: Out-of-order delta application.
   - `DUPLICATE_DELTA`: Repeated delta application.
   - `ALTERED_DELTA`: Byte corruption in intermediate deltas.
   - `WRONG_PARENT`: Forks or mismatched parent hash commitments.
   - `CROSS_TENANT_SUBSTITUTION`: Ingestion of deltas signed for another tenant.
3. **Monotonic Rollback Protection**: The recovery engine tracks the highest applied sequence number per tenant. Any attempt to restore an older sequence without dual-authorized break-glass override is rejected immediately as a `ROLLBACK_DETECTED` attack.

---

## 6. Subsystem Recovery Engines

### 6.1. Ledger Recovery Engine (`LedgerRecoveryEngine`)
- **Intact Recovery**: Verifies sequential hash chaining $H_i = \text{SHA-256}(H_{i-1} \parallel \dots)$.
- **Partial Recovery with Tail Quarantine**: If a storage sector corrupts the tail of the ledger, the engine preserves the clean prefix, marks the recovery as `PARTIAL_RECOVERY`, quarantines the corrupted tail for forensic inspection, and refuses silent truncation unless `allow_tail_truncation=True` is explicitly specified.
- **Merkle Checkpoint Verification**: Recomputes the entire receipt Merkle tree and validates it against historical commitments.
- **BFT Node Reconstitution**: Rebuilds permissioned Byzantine Fault Tolerant validator nodes from block headers and cryptographic quorum signatures.

### 6.2. Lineage Recovery Engine (`LineageRecoveryEngine`)
- Reconstitutes document lineage DAGs (`roots`, `copies`, `sessions`).
- Recomputes indices and verifies topological ordering.
- Fails closed on cycle injection (`CYCLE_DETECTED`), conflicting parent branches, or cross-tenant links.
- Preserves forensic boundaries when historical parent documents were released prior to retention window (`MISSING_PARENT`).

### 6.3. Telemetry Deduplication Engine (`TelemetryRecoveryEngine`)
- Reconstitutes events from disparate sources (EDR, print spoolers, DLP, CASB).
- Derives deterministic event fingerprints:
  $$\text{FP} = \text{SHA-256}(\text{source} \parallel \text{timestamp} \parallel \text{event\_type} \parallel \text{subject\_id} \parallel \text{artifact\_hash})$$
- Prevents double-counting and replay attacks during recovery merges.

### 6.4. Key Recovery & Temporal Validity Engine (`KeyRecoveryEngine`)
- **Non-Exportable Hardware Guards**: Plaintext private keys bound to HSMs / TPMs are never exported. Any attempt to package hardware keys raises a security violation.
- **Key Status Classification**: Tracks keys as `ACTIVE`, `ROTATED`, `SUSPECTED_COMPROMISE`, `COMPROMISED`, or `REVOKED`.
- **Temporal Validity Analysis**: Signatures produced before a registered compromise timestamp are validated as legally and forensically sound (`EVIDENCE_VALID`). Signatures created at or after compromise are marked `EVIDENCE_SUSPECT` and refused for automated attribution.

---

## 7. Dual-Controlled Incident Response & Forensic Preservation

The system features a formal 12-state state machine:
```
NORMAL -> SUSPECTED_COMPROMISE -> CONTAINMENT -> FORENSIC_PRESERVATION -> RECOVERY_VALIDATION -> RESTORED -> POST_INCIDENT_REVIEW
```
- **Forensic Preservation Mode**: When engaged, the engine executes an immediate write freeze. All mutating database operations raise `PreservationFreezeError`, allowing forensic examiners to capture immutable content-addressed snapshots of live volatile memory and databases before recovery commences.
- **Separation of Duties (Dual Control)**: Critical transitions (such as unfreezing preservation mode, restoring from an intentional rollback, or finalizing state to `RESTORED`) strictly require two independent authorized operators (e.g., Primary Operator + Security Administrator / CISO).
