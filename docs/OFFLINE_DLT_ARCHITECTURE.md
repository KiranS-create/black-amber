# AegisTrace: Offline Permissioned DLT Architecture

## 1. Architectural Overview

The **Offline Permissioned Distributed Ledger Technology (DLT)** subsystem provides an air-gapped, tamper-evident, multi-node replicated commit log for all decryption and export provenance events.

In classified, defence, and critical enterprise environments, internet connectivity is strictly prohibited. AegisTrace's DLT operates entirely within local air-gapped network segments or on isolated single-host replicated topologies, ensuring zero reliance on public blockchains, external NTP servers, or cloud key custody.

```
                    +---------------------------+
                    |    Recipient Client       |
                    | (ML-DSA-65 Private Key)   |
                    +-------------+-------------+
                                  |
                                  | Signs DecryptionReceipt
                                  v
+---------------------------------------------------------------+
|             OFFLINE BFT CONSENSUS LEADER NODE                 |
| - Verifies Recipient ML-DSA-65 Signature                      |
| - Validates Anti-Replay Nonce & Timestamp                     |
| - Batches Receipts into Candidate Block                       |
| - Computes Merkle Tree Root Hash                              |
+-------------------------------+-------------------------------+
                                |
                                | Broadcasts Proposed Block
                                v
+---------------------------------------------------------------+
|            INDEPENDENT DLT VALIDATOR CLUSTER                  |
| - Validator 1 (ML-DSA-65 Sign)                                |
| - Validator 2 (ML-DSA-65 Sign)   Quorum Threshold:            |
| - Validator 3 (ML-DSA-65 Sign)   Q = floor(2N/3) + 1          |
+-------------------------------+-------------------------------+
                                |
                                | Commits Finalized Block
                                v
+---------------------------------------------------------------+
|         REPLICATED STATE MACHINES (Nodes 1, 2, 3...)          |
| - Appends Finalized Block to Immutable Chain                  |
| - Indexes Receipts by ID, Token, Commitment, and Copy ID      |
| - Generates Cryptographic Merkle Inclusion Proofs             |
+---------------------------------------------------------------+
```

---

## 2. Consensus Model: Byzantine Fault Tolerant (BFT) Quorum

The offline DLT utilizes a round-robin leader-based BFT quorum voting protocol:
- **Total Validators**: $N$ authorized validators ($N \ge 3$).
- **Byzantine Fault Tolerance**: Tolerates up to $f = \lfloor (N - 1) / 3 \rfloor$ faulty or malicious nodes.
- **Quorum Threshold**:
  $$Q = \left\lfloor \frac{2N}{3} \right\rfloor + 1$$
  - For $N = 3$, $Q = \lfloor 6/3 \rfloor + 1 = 3$ votes required.
  - For $N = 4$, $Q = \lfloor 8/3 \rfloor + 1 = 3$ votes required.
  - For $N = 7$, $Q = \lfloor 14/3 \rfloor + 1 = 5$ votes required.

Each validator inspects every candidate transaction, verifies the recipient's ML-DSA-65 signature, and independently signs the block header hash using its own validator private key. A block is only finalized when it accumulates at least $Q$ valid validator signatures.

---

## 3. Data Structures & Merkle Audit Proofs

### 3.1 Block Header
```python
class DLTBlockHeader(BaseModel):
    block_height: int               # Monotonically increasing height (1, 2, 3...)
    previous_block_hash: str        # Hex SHA-256 of parent block header
    merkle_root: str                # Merkle root of committed receipts
    timestamp: str                  # ISO-8601 UTC timestamp
    epoch: int                      # Key / governance epoch
    validator_set_hash: str         # Hash of authorized validator public keys
```

### 3.2 Binary Merkle Tree
Receipts committed within a block are serialized into canonical leaves:
$$L_i = \text{SHA-256}(\text{CanonicalReceiptBytes}_i)$$
Intermediate nodes are computed hierarchically:
$$N_{\text{parent}} = \text{SHA-256}(N_{\text{left}} \parallel N_{\text{right}})$$

### 3.3 Merkle Inclusion Proof
For any committed receipt, an offline investigator can generate a lightweight, self-contained Merkle audit proof containing:
1. `leaf_hash`: $L_i$
2. `audit_path`: List of $(H_k, \text{direction})$ sibling hashes from leaf to root.
3. `merkle_root`: The verified root stored in the finalized block header.

Verification requires $O(\log_2 M)$ hash operations and proves receipt membership without disclosing other transactions in the block.

---

## 4. Security Guarantees & Attack Resistance

### 4.1 Anti-Replay Protection
- Every `DecryptionReceipt` contains an `event_id` and a 128-bit cryptographic `nonce`.
- The ledger maintains an in-memory and persisted set of processed `event_id` and `nonce` values.
- Submitting an identical receipt twice triggers immediate rejection: `DLTReplayAttackError: Replay detected for event_id`.

### 4.2 Fork Detection & Rejection
- If an adversary attempts to fork history by creating an alternative block at an existing height $h$ with a conflicting parent or payload, node state synchronization rejects the block:
  `DLTStateError: Fork detected at height h. Existing hash does not match proposed hash.`

### 4.3 Rollback & Truncation Resistance
- Blocks strictly enforce monotonic height progression ($h = h_{\text{tip}} + 1$).
- Nodes reject any attempt to revert the tip to an earlier block height or replay older chains without the genesis root.

### 4.4 Unilateral Insertion Prevention
- A malicious server administrator cannot unilaterally insert or modify records.
- Any receipt lacking a valid recipient ML-DSA-65 signature fails validator verification before reaching the consensus pool.
- Any block lacking $Q$ independent validator signatures is rejected by all peer nodes.
