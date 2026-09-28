# AegisTrace Performance Boundaries & Engineering Limitations

## 1. Scope & Purpose

This document outlines the concrete theoretical, algorithmic, software, and hardware limitations governing the AegisTrace system. It defines the operational envelope within which the platform provides deterministic forensic guarantees.

---

## 2. Cryptographic Execution Bounds

### 2.1 Post-Quantum Mathematical Ceilings (NIST FIPS 203 & 204)
- **ML-DSA-65 Signing Latency (~420–700 ms)**:
  - **Limitation**: ML-DSA-65 (Dilithium3) digital signature generation requires polynomial sampling, rejection sampling loops, and high-degree number theoretic transforms (NTT) over ring $\mathbb{Z}_q[X]/(X^{256} + 1)$.
  - **Implementation Constraint**: In pure Python/NumPy environments without C-level AVX-512 / ARM Neon vector extensions, rejection sampling iterations introduce noticeable variance in signing time (min 263 ms, max 890 ms).
  - **Engineering Boundary**: Signature generation must remain client-side (untrusted edge device) during release receipt generation, naturally distributing signing compute away from the central server.
  - **Recommendation for High-Throughput Relays**: If server-side batch signing is required, integrate native C FIPS 204 implementations (e.g., `liboqs` with AVX-512 / NEON assembly).

- **ML-KEM-768 Encapsulation & Decapsulation (~40–80 ms)**:
  - **Limitation**: Matrix-vector polynomial multiplications over Module-LWE lattices impose a hard CPU floor.
  - **Security Mandate**: Never cache decrypted symmetric keys or shared secrets to bypass decapsulation; key isolation must be strictly maintained per release.

---

## 3. Physical Channel & Computer Vision Bounds

### 3.1 Perspective Rectification & Homography Limits
- **OpenCV ArUco Detection Envelope**:
  - Requires all 4 fiducial markers (IDs 0, 1, 2, 3) to be at least partially visible and identifiable within the capture frame.
  - Rectification latency is bounded by image resolution and corner refinement ($5 \times 5$ sub-pixel window). High-resolution phone camera images ($4000 \times 3000$ px) take ~60–80 ms for detection and homography estimation.
  - **Extreme Geometric Limits**: Camera tilt angles $> 45^\circ$, perspective foreshortening where markers occupy $< 15 \times 15$ pixels, or optical blur exceeding Gaussian $\sigma > 4.0$ will trigger the fail-closed `NO_SIGNAL` state.

### 3.2 DSSS Capacity vs. Document Area Trade-Off
- **Carrier Capacity Floor**:
  - The canonical canvas ($800 \times 1000$ px) provides an active ROI of $(680-120) \times (880-120) = 560 \times 760 = 425,600\text{ pixels}$.
  - With a block size $B = 20\text{ px}$ (400 pixels/bit), the maximum raw capacity is $28 \times 38 = 1,064\text{ bits}$.
  - To embed a 128-bit Tardos codeword with 32 bytes of Reed-Solomon ECC (totaling 608 encoded bits), the tile redundancy is limited to $T = \lfloor 1064 / 608 \rfloor = 1\text{ tile}$.
  - **Limitation**: Payloads $> 128$ bits cannot be redundantly tiled on a single standard page without reducing $B$ (which decreases resilience to print-scan blur) or expanding the active canvas resolution.

---

## 4. In-Memory Scaling & Python Runtime Constraints

### 4.1 Global Interpreter Lock (GIL) & CPU-Bound Concurrency
- **Multi-Threading vs Multi-Processing**:
  - CPU-bound operations (ML-DSA verification, image warping, DSSS matched filtering) do not scale linearly under Python multi-threading (`threading.Thread`) due to GIL contention.
  - **Empirical Measurement**: Hashing 2,000 items with 1 worker took 241 ms; scaling across 2 workers reduced latency to 148 ms, but 4–8 workers showed plateauing at ~190–200 ms due to GIL thread-switch overhead.
  - **Production Deployment Rule**: Scale worker throughput using multi-process worker pools (`multiprocessing` or ASGI Uvicorn workers `gunicorn -w 8 -k uvicorn.workers.UvicornWorker`) where each worker process owns its isolated GIL and memory space.

### 4.2 Slotted Memory Footprint at 1,000,000 Scale
- **In-Memory Limits**:
  - At 1,000,000 nodes, `SparseLineageIndex` requires ~95 MB of physical RAM.
  - At 1,000,000 events, `ScalableLedger` requires ~140 MB of physical RAM.
  - At 1,000,000 records, `ScalableTelemetryProvider` requires ~160 MB of physical RAM.
  - **Total 1M Active Footprint**: ~400–500 MB RAM per tenant partition.
  - **Cold Storage Archival**: For scale beyond 1M events per tenant, instantiate cold tiering where events older than the active hot window (e.g. 50,000 events) are persisted to disk/LMDB and indexed by epoch checkpoints.

---

## 5. Storage & Disaster Recovery Bounds

### 5.1 Epoch Checkpointing Frequency
- **Checkpoint Overhead**:
  - Merkle root computation over an epoch of 1,000 SHA-256 hashes takes ~0.5 ms.
  - Checkpoint interval of $N = 1,000$ represents the optimal trade-off between append throughput and incremental verification speed.
  - Setting $N < 100$ introduces Merkle computation overhead on high-throughput ingest paths; setting $N > 10,000$ increases tip verification time during point-in-time recovery audits.

---

## 6. Summary of Engineering Guarantees

| Subsystem | Guaranteed Bound | Failure Mode / Boundary Condition |
| :--- | :--- | :--- |
| **Multi-Index Join** | $< 1.0\text{ ms}$ up to 1M scale | Truncated path if missing reference |
| **Lineage Traversal** | $< 5.0\text{ ms}$ up to 1,000 hops | Cycle detection returns `CYCLE_DETECTED` |
| **Watermark Extract** | $< 250\text{ ms}$ canonical canvas | Homography failure returns `NO_SIGNAL` |
| **Ledger Verification**| $< 0.05\text{ ms}$ incremental tip | Hash mismatch returns `TAMPER_DETECTED` |
| **Identity Resolution**| $< 0.1\text{ ms}$ per principal | Fallback to cached state `CACHED`/`STALE` |
