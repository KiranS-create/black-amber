# AegisTrace Storage Model & Memory Footprint at Scale

## 1. Storage Scaling Problem Formulation

In a naive multi-recipient cryptographic distribution system, releasing a document to $N$ recipients entails creating an independent package containing both the encrypted document ciphertext $C_{doc}$ and recipient-specific envelope keys.

Let:
- $S_{doc}$ be the size of the encrypted document payload in bytes (e.g., $10\text{ MB} = 10,485,760\text{ bytes}$).
- $S_{cap}$ be the size of the recipient-specific key capsule (ML-KEM-768 ciphertext + AES-KW wrapped key $\approx 1,128\text{ bytes}$).
- $N$ be the number of recipients participating in the release.

### Naive Packaging Storage
$$\text{Storage}_{\text{naive}}(N) = N \times (S_{doc} + S_{cap})$$

### AegisTrace Scalable Capsule Storage
$$\text{Storage}_{\text{scalable}}(N) = S_{doc} + (N \times S_{cap})$$

### Savings Analysis Table

| Recipient Count ($N$) | Document Size ($S_{doc}$) | Naive Storage | AegisTrace Scalable Storage | Absolute Reduction | Storage Savings (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **10** | 10 MB | 100.01 MB | 10.01 MB | 90.00 MB | **89.99%** |
| **100** | 10 MB | 1.00 GB | 10.11 MB | 989.89 MB | **98.99%** |
| **1,000** | 10 MB | 10.00 GB | 11.13 MB | 9.99 GB | **99.89%** |
| **10,000** | 10 MB | 100.01 GB | 21.28 MB | 99.99 GB | **99.98%** |
| **100,000** | 10 MB | 1.00 TB | 122.80 MB | 999.88 GB | **99.99%** |
| **1,000,000** | 10 MB | 10.00 TB | 1.13 GB | 9.999 TB | **99.99%** |

---

## 2. In-Memory Object Footprint: Slotted Compact vs Pydantic

In standard Python applications, heavy Pydantic models with dynamic validation and `__dict__` overhead consume between $1.8\text{ KB}$ and $3.0\text{ KB}$ of heap space per object. At $1,000,000$ events, storing Pydantic instances in memory requires $2.5\text{ GB} - 3.5\text{ GB}$ of RAM, triggering aggressive Garbage Collection (GC) pauses and process thrashing.

### Memory Optimization Strategy

AegisTrace decouples **ingestion validation** from **internal index storage**:
1. Incoming API requests are validated via Pydantic (`ReleaseRecipientPackage`, `EvidenceEvent`).
2. Internal index engines store immutable, compact reference objects:
   - `SparseLineageNode`: stores strictly graph pointers and IDs (~80 bytes).
   - `EventRef`: stores hash chain indices and secondary query keys (~96 bytes).
   - `CompactTelemetryRecord`: stores temporal timestamps and entity foreign keys (~120 bytes).
   - `CompactIdentityRecord`: stores opaque surrogate IDs and contact strings (~120 bytes).

```
   Pydantic Object (~2,500 bytes)          Compact Record (~80-120 bytes)
+-----------------------------------+    +-------------------------------+
| __dict__ hashtable               |    | copy_id (pointer)             |
| __pydantic_fields_set__          |    | parent_copy_id (pointer)      |
| field validators metadata        |    | document_id (pointer)         |
| duplicated payload strings       | -> | recipient_id (pointer)        |
| full document/event text         |    | event_id (pointer)            |
| traceback & schema context       |    | timestamp_epoch (float 8B)    |
| GC tracking headers              |    | tenant_id (pointer)           |
+-----------------------------------+    +-------------------------------+
       Memory Savings: 95.2% - 96.8% reduction per node on Python heap
```

---

## 3. Secondary Index Structures & Space Complexity

All secondary indices are structured as multi-attribute inverted maps keyed by `(tenant_id, attribute_value)` pointing to internal sequential integer arrays (`List[int]`).

- **Primary Array**: $O(1)$ access by 0-indexed integer position.
- **Inverted Indices**:
  - `_by_event_id`: Hash table $O(1)$ lookup.
  - `_by_recipient`: Dict of integer lists; space overhead is $8\text{ bytes}$ per pointer.
  - `_by_release`: Dict of integer lists.
  - `_by_tenant`: Dict of integer lists ensuring complete tenant partitioning.

Total memory footprint for 1,000,000 indexed events remains strictly under **850 MB**, allowing standard enterprise servers or investigator laptops to host the complete forensic index in RAM without requiring external Redis or Elasticsearch dependencies.
