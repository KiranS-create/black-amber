# AegisTrace End-to-End Forensic Pipeline Benchmark Report

**Generated:** 2026-09-27T16:24:05Z  
**Python Version:** 3.9.0  
**OS Platform:** win32  
**CPU Cores:** 12  

---

## 1. Golden Case Forensic Verification Summary (3 Recipients)

| Metric | Result | Target / Standard | Status |
|---|---|---|---|
| **Overall Forensic Status** | `VERIFIED` | `VERIFIED` | PASS |
| **Attributed Principal** | `alice` | Ground Truth Match (`alice`) | PASS |
| **Total Pipeline Latency** | `4566.45 ms` | < 10,000 ms | PASS |
| **Post-Quantum Manifest Signature** | `VALID` | ML-DSA-65 Validated | PASS |
| **Evidence Merkle Tree Root** | `VALID` | RFC-6962 Recomputed | PASS |
| **Recipient Decryption Signature** | `VALID` | ML-DSA-65 Replayed | PASS |
| **Permissioned DLT Consensus** | `VALID` | Byzantine Quorum Valid | PASS |
| **Multi-Recipient Equivalence** | `EQUIVALENT_AND_FORENSICALLY_DISTINCT` | Invariant & Distinct | PASS |

---

## 2. Multi-Recipient Scalability Benchmark

| Recipient Count | Mean Latency (ms) | P50 (ms) | P95 (ms) | Throughput (rec/s) |
|---|---|---|---|---|
| **1** | 1936.12 | 1910.28 | 2305.69 | 0.52 |
| **5** | 5922.58 | 6049.62 | 6102.23 | 0.84 |
| **10** | 10286.22 | 10513.68 | 10873.14 | 0.97 |
| **25** | 22983.1 | 22983.1 | 22983.1 | 1.09 |
| **50** | 43671.88 | 43671.88 | 43671.88 | 1.14 |

---

## 3. Memory & Resource Footprint

- **Memory RSS Delta:** `30.04 MB`
- **Network Sockets Required:** `0 (Strict Air-Gap Verified)`
- **Cloud KMS Dependencies:** `0 (Autonomous Local PQC)`
