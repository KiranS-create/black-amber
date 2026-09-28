# OFFLINE PERMISSIONED DLT CONSENSUS ARCHITECTURE
## Byzantine Fault Tolerant Quorum, RFC-6962 Merkle Trees, and Air-Gapped State Replication
**Document Version:** 1.0.0  
**Classification:** AegisTrace Core Distributed Ledger Architecture  
**Security Level:** Production / Post-Quantum Air-Gapped Standard  

---

### 1. Architectural Philosophy & Threat Model

Traditional enterprise blockchain systems (Hyperledger Fabric, Ethereum-based private chains, Corda) presuppose persistent network connectivity, gossip protocols, complex P2P discovery engines, and heavy containerized runtime environments. In contrast, sensitive forensic applications operate in **isolated, high-security air-gapped enclaves** (SCIFs, defense testbeds, sovereign document repositories) where external network connectivity is strictly forbidden (`socket.AF_INET` disabled).

A common engineering antipattern in such environments is degrading the audit log to a single append-only JSON file or a local hash chain. This introduces critical vulnerabilities:
1. **Single Point of Compromise:** A root administrator or hostile endpoint can rewrite history or backdate records without detection.
2. **Fork Vulnerability:** An adversary can present conflicting historical states to different verifiers.
3. **Rollback Attacks:** An attacker can truncate the ledger to an earlier block height to erase evidence of a decryption event.

**The AegisTrace Solution:**  
AegisTrace implements a lightweight, pure-Python, zero-dependency **Offline Permissioned DLT (Distributed Ledger Technology)** network. The network comprises $N$ independent validator nodes ($N \ge 3$) operating with independent post-quantum ML-DSA-65 signing keypairs. Consensus on new blocks requires an explicit supermajority quorum of $\ge \lfloor 2N/3 \rfloor + 1$ validator signatures. History is secured via RFC-6962 double-domain Merkle trees, enabling compact logarithmic inclusion proofs verifiable in any air-gapped forensic workstation.

---

### 2. Multi-Validator Byzantine Quorum Consensus

#### 2.1 Network Topology & Quorum Threshold
Let $\mathcal{V} = \{V_1, V_2, \dots, V_N\}$ denote the set of authorized validator nodes, where each validator $V_j$ possesses:
- An ML-DSA-65 public key $PK_{V_j}$ registered in the genesis ledger configuration.
- A secure private key $SK_{V_j}$ accessible only to validator $j$.

For a network of size $N$, the consensus quorum threshold $Q$ is defined as:
$$Q = \left\lfloor \frac{2N}{3} \right\rfloor + 1$$

For the default 3-node air-gapped deployment ($N = 3$):
$$Q = \left\lfloor \frac{6}{3} \right\rfloor + 1 = 3 \quad (\text{Supermajority Quorum requires } \ge 2 \text{ or } 3 \text{ votes})$$
In AegisTrace, with $N=3$, $Q = 3$ guarantees safety against arbitrary single-node Byzantine faults while enforcing unanimous endorsement among active enclave authorities.

#### 2.2 Consensus State Machine
When a recipient submits a `DecryptionReceipt` transaction $T_x$:
```
                    [ DecryptionReceipt Submitted ]
                                  │
                                  ▼
               [ Transaction Queue / Mempool Ingestion ]
                                  │
                                  ▼
                [ Quorum Voting Round Initiated ]
               ┌──────────────────┼──────────────────┐
               ▼                  ▼                  ▼
        [ Validator 1 ]    [ Validator 2 ]    [ Validator 3 ]
        - Verify Tx Sig    - Verify Tx Sig    - Verify Tx Sig
        - Check Duplicates - Check Duplicates - Check Duplicates
        - Sign Header      - Sign Header      - Sign Header
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  │
                                  ▼
                [ Quorum Check: |Signatures| >= Q ]
                     ├── If < Q  ──► REJECT (Sub-Quorum Exception)
                     └── If >= Q ──► COMMIT BLOCK
                                  │
                                  ▼
             [ Broadcast / Replicate Block to Node Stores ]
               - Enforce Monotonic Height: H_new == H_curr + 1
               - Verify PrevBlockHash == H_curr.hash
               - Prevent Forks & Rollbacks
               - Re-index Merkle Inclusion Trees
```

---

### 3. RFC-6962 Double-Domain Merkle Tree

To ensure tamper-evidence and enable verifiable non-membership and inclusion queries without transferring the full ledger, transactions within each block are committed to an RFC-6962 compliant binary Merkle tree.

#### 3.1 Domain Separation Rules
Standard naive Merkle trees are susceptible to second-preimage attacks, where an internal node hash can be interpreted as a leaf hash. AegisTrace eliminates this attack surface via strict RFC-6962 one-byte domain prefixing:
- **Leaf Hash Domain Prefix:** `0x00`
- **Internal Node Domain Prefix:** `0x01`

#### 3.2 Hashing Specification
1. **Leaf Nodes:** For a serialized canonical receipt payload $T_x^{(i)}$:
   $$H_{\text{leaf}}^{(i)} = \text{SHA-256}\left( \mathtt{0x00} \parallel T_x^{(i)} \right)$$
2. **Internal Branch Nodes:** For left child $H_L$ and right child $H_R$:
   $$H_{\text{branch}} = \text{SHA-256}\left( \mathtt{0x01} \parallel H_L \parallel H_R \right)$$
3. **Odd-Node Balancing & Second-Preimage Defense:** When the number of nodes at any tree layer is odd, the trailing node is paired with an identical duplicate (`right_hash = left_hash`), yielding balanced binary trees and uniform $O(\log_2 M)$ audit paths. While naive node duplication can introduce vulnerability to duplicate-leaf injections in unauthenticated systems (e.g. CVE-2012-2459), AegisTrace completely eliminates this vector by enforcing strict transaction-level deduplication: every `DecryptionReceipt` is bound to a unique `receipt_id`, random nonces, and verified against the state-level `seen_receipt_ids` set prior to Merkle tree ingestion.

#### 3.3 Inclusion Proof Construction & Verification
A Merkle inclusion proof for leaf $k$ consists of the path of sibling hashes:
$$\Pi_k = \left\{ (H_1, \text{pos}_1), (H_2, \text{pos}_2), \dots, (H_d, \text{pos}_d) \right\}, \quad \text{pos}_j \in \{\text{left}, \text{right}\}$$

Verification computes the candidate root hash $R'$ by folding up the tree and asserts:
$$R' \equiv R_{\text{merkle\_root}} \quad \land \quad \text{BlockHeader.merkle\_root} == R_{\text{merkle\_root}}$$
Verification complexity is $O(\log_2 M)$ where $M$ is the number of transactions in the block.

---

### 4. Replicated State Storage & Attack Defenses

AegisTrace maintains replicated state across multiple distinct storage instances (`DLTNode`). Each node independently validates blocks before committing them to its persistent store.

#### 4.1 Fork Detection & Rejection
- **Condition:** A proposed block arrives with height $H = H_{\text{current}}$, but with block hash $B_{\text{hash}} \neq B_{\text{current\_tip\_hash}}$.
- **Defense:** The node detects a competing tip, halts processing for that chain, and raises `DLTIntegrityError("FORK_DETECTED: Conflicting block proposed at existing height")`.

#### 4.2 Rollback Detection & Truncation Resistance
- **Condition:** An adversary attempts to submit a block with height $H < H_{\text{current}}$.
- **Defense:** The node validates $H_{\text{new}} == H_{\text{current}} + 1$. Any block with $H \le H_{\text{current}}$ is unconditionally rejected:
  `DLTIntegrityError("ROLLBACK_DETECTED: Proposed height less than or equal to current tip")`.

#### 4.3 Transaction Deduplication & Replay Prevention
Every committed transaction ID is indexed in a state-level deduplication set:
$$\mathcal{S}_{\text{tx}} = \{ T_{\text{id}}^{(1)}, T_{\text{id}}^{(2)}, \dots \}$$
If a receipt with an existing `receipt_id` or identical `(doc_root_hash, recipient_id, session_id, event_id)` is submitted, the node halts with `ValueError("REPLAY_DETECTED: Transaction already committed")`.

---

### 5. Quorum-Endorsed State Snapshots

For rapid archival, disaster recovery, and cross-enclave transfer, AegisTrace supports ledger state snapshots (`DLTSnapshot`):
$$\mathcal{S}_{\text{snap}} = \left\langle H_{\text{tip}}, B_{\text{tip\_hash}}, R_{\text{state\_merkle}}, \Sigma_{\mathcal{V}} \right\rangle$$
where $\Sigma_{\mathcal{V}} = \{ \sigma_{V_j} \}_{j=1}^Q$ represents the supermajority of validator ML-DSA-65 signatures endorsing the snapshot header.

An air-gapped node receiving a snapshot can verify the entire historical state in $O(Q \cdot \tau_{\text{verify}})$ time without replaying all individual historical transactions.
