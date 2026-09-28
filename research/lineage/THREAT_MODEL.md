# Active Cryptographic Copy Lineage: Threat Model & Adversarial Analysis

## 1. Threat Model & Adversary Capabilities

We assume a computationally sophisticated adversary with the following capabilities:
1. **Full Bitstream Access:** Can copy, duplicate, inspect, truncate, or compress any document file in their possession.
2. **Offline Possession:** Can manipulate document artifacts outside the enterprise network and without network connectivity to AegisTrace servers.
3. **Adversarial Collaboration:** Multiple recipients or rogue insiders can exchange documents, re-share artifacts out-of-band, or attempt collusion attacks.
4. **Physical Capture:** Can photograph displays, capture screenshots with third-party tools, or print documents onto physical paper.
5. **Cryptographic Bounds:** The adversary cannot break SHA-256 preimages or forge ML-DSA-65 post-quantum digital signatures.

---

## 2. Attack Vectors & AegisTrace Defenses (Scenarios A through T)

The table below catalogs the 20 formal attack scenarios validated in the test suite (`tests/attacks/test_lineage_attacks.py`):

| Attack Vector | Adversarial Mechanism | AegisTrace Mitigation & Boundary Defense |
| :--- | :--- | :--- |
| **A: Forged Child Copy** | Attacker invents a child copy record pointing to a fabricated or missing parent. | `LineageVerifier` verifies parent existence in storage; missing parent triggers fail-closed `LINEAGE_BROKEN`. |
| **B: Wrong Parent Reference** | Attacker links a copy from Document Root A as a child of Document Root B. | `verify_copy_derivation` verifies `copy.document_id == root.document_id` and `parent.document_id == root.document_id`. Contamination caught. |
| **C: Modified Parent ID** | Attacker tampers with the `parent_copy_id` field in an existing copy instance record. | Parent lookup fails or derivation invariant fails; verifier flags `LINEAGE_BROKEN`. |
| **D: Replayed Forwarding Receipt** | Attacker replays an intercepted `ForwardingEvent` receipt to duplicate a forwarding edge. | `LineageStorage` checks `event.compute_event_hash()` against indexed event set. Replay is rejected with `ValueError`. |
| **E: Replayed Export Receipt** | Attacker replays an `ExportEvent` receipt hash to forge export history. | Same anti-replay hash check prevents replayed export events. |
| **F: Duplicate Events** | Double submission of identical transition receipts across network retries. | Deduplicated via $O(1)$ set containment index; duplicate submissions are safely rejected. |
| **G: Reordered Events** | Attacker tampers with receipt timestamps or event hashes to invert causal sequence. | Hash mismatch detected: `signed_event_hash != compute_event_hash()`; receipt rejected. |
| **H: Forged Actor Signature** | Attacker attempts to forge sender signature on forwarding receipt using rogue key. | `MLDSA65.verify` fails on event preimage; receipt rejected, lineage breaks. |
| **I: Forged Device ID** | Attacker supplies fabricated device key or spoofed hardware attestation. | `DeviceBindingProvider` verifies device enrollment; unregistered device IDs rejected. |
| **J: Session Substitution** | Attacker uses a valid session ID belonging to another user to export or render. | `ControlledViewer` asserts session principal binding and active lifecycle state. |
| **K: Export Without Re-fingerprint** | Attacker bypasses export re-fingerprinting to leak file without child token. | Export boundary in `ControlledViewer` atomically combines child copy issuance and fingerprint embedding before releasing bytes. |
| **L: Lineage Fork Attack** | Parent copy is shared to multiple recipients, creating a tree branch. | Legitimate behavior in DAG; each fork maintains an independent, valid path back to root. |
| **M: Lineage Merge / Cycle Attack** | Attacker introduces cyclic loop ($A \to B \to C \to A$) in ancestry graph. | `LineageVerifier` maintains `visited_ids` set during traversal; cycles immediately detected and rejected. |
| **N: Cross-Document Substitution** | Attacker substitutes a copy from another document to confuse forensic attribution. | `verify_copy_derivation` checks document root equality; mismatches immediately rejected. |
| **O: Cross-Release Substitution** | Attacker mixes copies between different distribution releases. | Target bindings check `release_id` continuity; mismatched releases trigger `CONFLICT`. |
| **P: Stale Epoch / Expired Session** | Attacker attempts to view or export after session expiry or revocation. | `render_view` and `controlled_export` assert `session.is_active` and time bounds. Expired sessions fail closed. |
| **Q: Offline Child Dissemination** | Actor passes file out-of-band to unrecorded third party. | System attributes custody up to last known controlled holder; flags `UNKNOWN_DOWNSTREAM_ACTOR`. |
| **R: Bitstream Duplication** | Attacker duplicates file bit-for-bit $N$ times. | System limits attribution to copy instance holder (`LEVEL_3` / `LEVEL_4`); strictly refrains from inventing downstream identities. |
| **S: Screenshot Outside Viewer** | Attacker photographs or snips screen externally. | Dynamic session watermark (`sf_...`) remains visible in render; maps back to viewer session and user identity. |
| **T: Raw File Exfiltration / Print** | Attacker prints document to physical paper and leaks paper. | Forensic analysis recovers watermark/fingerprint; flags boundary state `LAST_KNOWN_HOLDER` without overclaiming human guilt. |

---

## 3. Defense-in-Depth Summary

By combining:
1. **Cryptographic Proofs:** ML-DSA-65 post-quantum signed transition receipts.
2. **Invariant Verification:** Strict depth sequencing, cycle detection, and cross-document isolation.
3. **Honesty Invariants:** Refusing to frame intermediaries or invent unproven downstream identities.

AegisTrace provides mathematical defensibility against both active cryptographic tampering and uncontrolled out-of-band leaks.
