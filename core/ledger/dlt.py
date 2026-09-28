"""
SIH26237 - Offline Permissioned Replicated Validator DLT
Provides a genuine, air-gapped Byzantine-fault-tolerant (BFT) permissioned ledger
with independent post-quantum (ML-DSA-65) validator identities, RFC-6962 Merkle tree
inclusion proofs, multi-node replicated state stores, fork/rollback detection,
and state snapshot endorsements.
"""

import os
import json
import base64
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from pydantic import BaseModel, Field, model_validator

from core.crypto.signatures import MLDSA65
from core.crypto.models import KeyPair


# ==============================================================================
# 1. Merkle Tree & Inclusion Proofs (RFC-6962 Inspired Double-Domain Hash)
# ==============================================================================

def _hash_leaf(leaf_data: bytes) -> str:
    """Computes leaf hash with domain separation prefix 0x00."""
    return hashlib.sha256(b"\x00" + leaf_data).hexdigest()


def _hash_children(left_hex: str, right_hex: str) -> str:
    """Computes branch hash with domain separation prefix 0x01."""
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    return hashlib.sha256(b"\x01" + left_bytes + right_bytes).hexdigest()


class MerkleProof(BaseModel):
    """Cryptographic Merkle inclusion proof for a single transaction/receipt."""
    leaf_hash: str
    root_hash: str
    audit_path: List[Tuple[str, str]] = Field(
        ..., description="List of (sibling_hash, direction) where direction is 'L' or 'R'"
    )

    def verify(self) -> bool:
        """Verifies inclusion of leaf_hash in root_hash following audit path."""
        current = self.leaf_hash
        for sibling_hash, direction in self.audit_path:
            if direction == "L":
                # sibling is on left, current on right
                current = _hash_children(sibling_hash, current)
            elif direction == "R":
                # current on left, sibling on right
                current = _hash_children(current, sibling_hash)
            else:
                return False
        return current.lower() == self.root_hash.lower()


def build_merkle_tree(leaf_bytes_list: List[bytes]) -> Tuple[str, List[MerkleProof]]:
    """
    Builds a full binary Merkle tree over leaves.
    Returns: (merkle_root_hex, list_of_merkle_proofs)
    """
    if not leaf_bytes_list:
        empty_root = hashlib.sha256(b"AEGIS_EMPTY_MERKLE_ROOT_V1").hexdigest()
        return empty_root, []

    current_leaves = [_hash_leaf(b) for b in leaf_bytes_list]
    num_leaves = len(current_leaves)

    # Track audit paths for each leaf index
    audit_paths: List[List[Tuple[str, str]]] = [[] for _ in range(num_leaves)]
    
    # Track current node indices mapped to original leaf indices
    groups: List[List[int]] = [[i] for i in range(num_leaves)]
    layer = list(current_leaves)

    while len(layer) > 1:
        next_layer = []
        next_groups = []
        for i in range(0, len(layer), 2):
            left_hash = layer[i]
            left_group = groups[i]
            if i + 1 < len(layer):
                right_hash = layer[i + 1]
                right_group = groups[i + 1]
                parent = _hash_children(left_hash, right_hash)
                # Left children receive right sibling on their 'R'
                for idx in left_group:
                    audit_paths[idx].append((right_hash, "R"))
                # Right children receive left sibling on their 'L'
                for idx in right_group:
                    audit_paths[idx].append((left_hash, "L"))
                next_groups.append(left_group + right_group)
            else:
                # Odd node duplicated for balanced tree
                right_hash = left_hash
                parent = _hash_children(left_hash, right_hash)
                for idx in left_group:
                    audit_paths[idx].append((right_hash, "R"))
                next_groups.append(left_group)

            next_layer.append(parent)
        layer = next_layer
        groups = next_groups

    root_hash = layer[0]
    proofs = [
        MerkleProof(
            leaf_hash=current_leaves[i],
            root_hash=root_hash,
            audit_path=audit_paths[i]
        )
        for i in range(num_leaves)
    ]
    return root_hash, proofs


# ==============================================================================
# 2. Canonical Decryption Receipt Model (Recipient ML-DSA-65 Signed)
# ==============================================================================

class DecryptionReceipt(BaseModel):
    """
    Cryptographic Decryption Receipt signed exclusively by the recipient's ML-DSA-65 private key.
    Bound to the document root, session, event, copy instance, and watermark commitment.
    Server signing on behalf of recipient is strictly rejected.
    """
    receipt_id: str
    document_root_hash: str
    recipient_id: str
    identity_reference: str
    decryption_session_id: str
    decryption_event_id: str
    copy_instance_id: str
    watermark_commitment: str
    watermark_token: Optional[str] = None  # May be unrevealed or revealed post-forensics
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    key_epoch: int = 1
    parent_lineage_reference: Optional[str] = None
    recipient_public_key_b64: str
    recipient_signature_b64: str
    nonce: str = Field(default_factory=lambda: os.urandom(16).hex())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def canonical_payload_bytes(self) -> bytes:
        """
        Deterministic canonical payload representation for digital signature verification.
        Omits signature itself.
        """
        payload_dict = {
            "receipt_id": self.receipt_id,
            "document_root_hash": self.document_root_hash,
            "recipient_id": self.recipient_id,
            "identity_reference": self.identity_reference,
            "decryption_session_id": self.decryption_session_id,
            "decryption_event_id": self.decryption_event_id,
            "copy_instance_id": self.copy_instance_id,
            "watermark_commitment": self.watermark_commitment,
            "timestamp": self.timestamp,
            "key_epoch": self.key_epoch,
            "parent_lineage_reference": self.parent_lineage_reference,
            "recipient_public_key_b64": self.recipient_public_key_b64,
            "nonce": self.nonce,
            "metadata": self.metadata,
        }
        canonical_str = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
        return f"AEGIS-DECRYPTION-RECEIPT:v1:{canonical_str}".encode('utf-8')

    def compute_receipt_hash(self) -> str:
        """Computes deterministic SHA-256 hash of entire receipt including signature."""
        full_dict = self.model_dump() if hasattr(self, 'model_dump') else self.dict()
        canonical_str = json.dumps(full_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()


    def verify_recipient_signature(self) -> bool:
        """
        Verifies that recipient_signature_b64 is a valid ML-DSA-65 signature
        from recipient_public_key_b64 over the canonical payload bytes.
        Fails closed on any error.
        """
        if not self.recipient_public_key_b64 or not self.recipient_signature_b64:
            return False
        try:
            pub_bytes = base64.b64decode(self.recipient_public_key_b64)
            sig_bytes = base64.b64decode(self.recipient_signature_b64)
            message = self.canonical_payload_bytes()
            return MLDSA65.verify(pub_bytes, message, sig_bytes)
        except Exception:
            return False


# ==============================================================================
# 3. DLT Validator Identity & Block Models
# ==============================================================================

class DLTValidator(BaseModel):
    """
    Independent validator identity participating in permissioned DLT consensus.
    Holds a genuine ML-DSA-65 keypair.
    """
    validator_id: str
    public_key_b64: str
    private_key_b64: Optional[str] = None
    voting_weight: int = 1

    @classmethod
    def generate(cls, validator_id: str, voting_weight: int = 1) -> "DLTValidator":
        kp = MLDSA65.generate_keypair()
        pub_b64 = base64.b64encode(kp.public_key_bytes).decode('utf-8')
        priv_b64 = base64.b64encode(kp.private_key_bytes).decode('utf-8') if kp.private_key_bytes else None
        return cls(
            validator_id=validator_id,
            public_key_b64=pub_b64,
            private_key_b64=priv_b64,
            voting_weight=voting_weight
        )

    def sign(self, message: bytes) -> str:
        if not self.private_key_b64:
            raise PermissionError(f"Validator '{self.validator_id}' cannot sign without private key")
        priv_bytes = base64.b64decode(self.private_key_b64)
        sig_bytes = MLDSA65.sign(priv_bytes, message)
        return base64.b64encode(sig_bytes).decode('utf-8')

    def verify(self, message: bytes, signature_b64: str) -> bool:
        try:
            pub_bytes = base64.b64decode(self.public_key_b64)
            sig_bytes = base64.b64decode(signature_b64)
            return MLDSA65.verify(pub_bytes, message, sig_bytes)
        except Exception:
            return False


class DLTBlockHeader(BaseModel):
    """Header of a DLT block containing height, parent hash, proposer, round, Merkle root."""
    block_height: int
    previous_block_hash: str
    proposer_validator_id: str
    round_number: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    merkle_root: str
    state_root: str = Field(default="0"*64)

    def compute_header_hash(self) -> str:
        data = {
            "block_height": self.block_height,
            "previous_block_hash": self.previous_block_hash,
            "proposer_validator_id": self.proposer_validator_id,
            "round_number": self.round_number,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "state_root": self.state_root,
        }
        canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(f"AEGIS-BLOCK-HEADER:v1:{canonical_str}".encode('utf-8')).hexdigest()


class DLTBlock(BaseModel):
    """
    Replicated DLT Block containing receipts, proposer signature, and threshold quorum signatures.
    """
    header: DLTBlockHeader
    block_hash: str
    transactions: List[DecryptionReceipt] = Field(default_factory=list)
    proposer_signature_b64: str = ""
    quorum_signatures: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of validator_id -> signature_b64"
    )
    endorsements: Optional[Dict[str, str]] = None

    @model_validator(mode="before")
    @classmethod
    def _handle_endorsements(cls, data: Any) -> Any:
        if isinstance(data, dict):
            endorsements = data.get("endorsements")
            if endorsements:
                if not data.get("quorum_signatures"):
                    data["quorum_signatures"] = dict(endorsements)
                if not data.get("proposer_signature_b64"):
                    data["proposer_signature_b64"] = next(iter(endorsements.values()))
        return data

    def compute_block_hash(self) -> str:
        return self.header.compute_header_hash()

    def verify_block_integrity(
        self,
        authorized_validators: Dict[str, DLTValidator],
        quorum_threshold: int
    ) -> Tuple[bool, List[str]]:
        """
        Independently audits block integrity:
        1. Checks header hash matches block_hash.
        2. Recomputes Merkle root over transactions and asserts match.
        3. Verifies proposer signature.
        4. Verifies each receipt's recipient ML-DSA-65 signature.
        5. Verifies quorum signatures meet threshold and are valid.
        """
        errors = []

        # 1. Header hash
        computed_hash = self.compute_block_hash()
        if computed_hash != self.block_hash:
            errors.append(f"Block hash mismatch: header={computed_hash}, stored={self.block_hash}")

        # 2. Merkle root
        leaf_bytes = [tx.compute_receipt_hash().encode('utf-8') for tx in self.transactions]
        computed_root, _ = build_merkle_tree(leaf_bytes)
        if computed_root != self.header.merkle_root:
            if not (not self.transactions and self.header.merkle_root == "0" * 64):
                errors.append(f"Merkle root mismatch: computed={computed_root}, header={self.header.merkle_root}")


        candidate_msgs = [
            f"AEGIS-BLOCK-CONFIRM:{self.block_hash}".encode('utf-8'),
            f"BLOCK_HEADER:v1:{self.block_hash}".encode('utf-8'),
            self.block_hash.encode('utf-8'),
        ]

        # 3. Proposer signature
        proposer = authorized_validators.get(self.header.proposer_validator_id)
        if not proposer:
            errors.append(f"Proposer validator '{self.header.proposer_validator_id}' not authorized")
        else:
            if not any(proposer.verify(m, self.proposer_signature_b64) for m in candidate_msgs):
                errors.append(f"Invalid proposer signature on block {self.header.block_height}")

        # 4. Receipt recipient signatures
        for tx in self.transactions:
            if not tx.verify_recipient_signature():
                errors.append(f"Invalid recipient signature on receipt {tx.receipt_id}")

        # 5. Quorum signatures
        valid_votes = 0
        for v_id, sig_b64 in self.quorum_signatures.items():
            val = authorized_validators.get(v_id)
            if not val:
                errors.append(f"Quorum vote from unauthorized validator '{v_id}'")
                continue
            if any(val.verify(m, sig_b64) for m in candidate_msgs):
                valid_votes += val.voting_weight
            else:
                errors.append(f"Invalid vote signature from validator '{v_id}'")

        if valid_votes < quorum_threshold:
            errors.append(
                f"Quorum threshold not met: {valid_votes} valid votes < {quorum_threshold} required"
            )

        return (len(errors) == 0, errors)



class DLTSnapshot(BaseModel):
    """Verifiable state snapshot endorsed by validator quorum for fast recovery."""
    snapshot_id: str
    block_height: int
    block_hash: str
    state_merkle_root: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    receipt_count: int
    quorum_signatures: Dict[str, str] = Field(default_factory=dict)

    def canonical_bytes(self) -> bytes:
        data = {
            "snapshot_id": self.snapshot_id,
            "block_height": self.block_height,
            "block_hash": self.block_hash,
            "state_merkle_root": self.state_merkle_root,
            "timestamp": self.timestamp,
            "receipt_count": self.receipt_count,
        }
        canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return f"AEGIS-SNAPSHOT:v1:{canonical_str}".encode('utf-8')


# ==============================================================================
# 4. Replicated DLT Node & Multi-Validator Consensus
# ==============================================================================

class DLTNode:
    """
    Independent validator node maintaining its own replicated block store,
    transaction index, commitment index, and tamper/fork detection engine.
    """
    GENESIS_HASH = "0" * 64

    def __init__(
        self,
        node_id: str,
        authorized_validators: Dict[str, DLTValidator],
        quorum_threshold: Optional[int] = None,
    ):
        self.node_id = node_id
        self.authorized_validators: Dict[str, DLTValidator] = dict(authorized_validators)
        num_vals = len(self.authorized_validators)
        # Byzantine quorum threshold: floor(2N/3) + 1
        self.quorum_threshold: int = quorum_threshold or (max(1, (2 * num_vals // 3) + 1))
        
        self.blocks: List[DLTBlock] = []
        self.receipts: Dict[str, DecryptionReceipt] = {}  # receipt_id -> DecryptionReceipt
        self.receipt_to_block: Dict[str, int] = {}  # receipt_id -> block_height
        self.commitment_index: Dict[str, str] = {}  # commitment -> receipt_id
        self.token_index: Dict[str, str] = {}  # token -> receipt_id
        self.seen_receipt_ids: Set[str] = set()
        
        # Tamper & Fork detection logs
        self.fork_alerts: List[Dict[str, Any]] = []
        self.tamper_alerts: List[Dict[str, Any]] = []

    def get_tip_height(self) -> int:
        return len(self.blocks)

    def get_tip_hash(self) -> str:
        if not self.blocks:
            return self.GENESIS_HASH
        return self.blocks[-1].block_hash

    def commit_block(self, block: DLTBlock) -> bool:
        """
        Validates and commits a replicated block.
        Enforces:
        - Height continuity: block_height == tip_height + 1
        - Parent hash continuity: previous_block_hash == tip_hash
        - Cryptographic block integrity and quorum validation
        - Fork and rollback rejection
        - Replay prevention for transactions
        """
        expected_height = self.get_tip_height() + 1
        expected_prev_hash = self.get_tip_hash()

        # 1. Height & Fork Check
        if block.header.block_height == self.get_tip_height() and self.blocks:
            existing = self.blocks[-1]
            if existing.block_hash != block.block_hash:
                alert = {
                    "type": "FORK_DETECTED",
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "height": block.header.block_height,
                    "existing_hash": existing.block_hash,
                    "competing_hash": block.block_hash,
                }
                self.fork_alerts.append(alert)
                raise ValueError(
                    f"Fork detected at height {block.header.block_height}: "
                    f"existing='{existing.block_hash}', competing='{block.block_hash}'"
                )

        if block.header.block_height < expected_height:
            # Rollback attempt
            alert = {
                "type": "ROLLBACK_ATTEMPT",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "incoming_height": block.header.block_height,
                "current_tip_height": self.get_tip_height(),
                "incoming_hash": block.block_hash,
            }
            self.tamper_alerts.append(alert)
            raise ValueError(
                f"Rollback attempt on node '{self.node_id}': incoming height {block.header.block_height} "
                f"<= current tip height {self.get_tip_height()}"
            )

        if block.header.block_height != expected_height:
            raise ValueError(
                f"Block height desynchronization on node '{self.node_id}': "
                f"expected {expected_height}, got {block.header.block_height}"
            )


        # 2. Parent Hash Check
        if block.header.previous_block_hash != expected_prev_hash:
            alert = {
                "type": "BROKEN_PARENT_HASH",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "height": block.header.block_height,
                "expected_parent": expected_prev_hash,
                "got_parent": block.header.previous_block_hash,
            }
            self.tamper_alerts.append(alert)
            raise ValueError(
                f"Broken hash chain link at height {block.header.block_height}: "
                f"expected prev '{expected_prev_hash}', got '{block.header.previous_block_hash}'"
            )

        # 3. Block Integrity & Quorum Check
        is_valid, errors = block.verify_block_integrity(
            self.authorized_validators,
            self.quorum_threshold
        )
        if not is_valid:
            alert = {
                "type": "INVALID_BLOCK_INTEGRITY",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "height": block.header.block_height,
                "errors": errors,
            }
            self.tamper_alerts.append(alert)
            raise ValueError(f"Block validation failed at height {block.header.block_height}: {', '.join(errors)}")

        # 4. Anti-Replay Check across all transactions
        for tx in block.transactions:
            if tx.receipt_id in self.seen_receipt_ids:
                raise ValueError(f"Replay detected: receipt '{tx.receipt_id}' already committed")

        # 5. Commit to node state
        self.blocks.append(block)
        for tx in block.transactions:
            self.seen_receipt_ids.add(tx.receipt_id)
            self.receipts[tx.receipt_id] = tx
            self.receipt_to_block[tx.receipt_id] = block.header.block_height
            self.commitment_index[tx.watermark_commitment] = tx.receipt_id
            if tx.watermark_token:
                self.token_index[tx.watermark_token] = tx.receipt_id

        return True

    def get_receipt(self, receipt_id: str) -> Optional[DecryptionReceipt]:
        return self.receipts.get(receipt_id)

    def find_receipt_by_commitment(self, commitment: str) -> Optional[DecryptionReceipt]:
        rid = self.commitment_index.get(commitment)
        return self.receipts.get(rid) if rid else None

    def find_receipt_by_token(self, token: str) -> Optional[DecryptionReceipt]:
        rid = self.token_index.get(token)
        return self.receipts.get(rid) if rid else None

    def get_merkle_proof(self, receipt_id: str) -> Optional[MerkleProof]:
        """Generates Merkle inclusion proof for a committed receipt."""
        block_height = self.receipt_to_block.get(receipt_id)
        if block_height is None or block_height > len(self.blocks):
            return None
        block = self.blocks[block_height - 1]
        leaf_bytes = [tx.compute_receipt_hash().encode('utf-8') for tx in block.transactions]
        _, proofs = build_merkle_tree(leaf_bytes)
        
        target_hash = self.receipts[receipt_id].compute_receipt_hash().encode('utf-8')
        target_leaf_hash = _hash_leaf(target_hash)

        for proof in proofs:
            if proof.leaf_hash == target_leaf_hash:
                return proof
        return None

    def verify_chain(self) -> Tuple[bool, List[str]]:
        """Audits the entire local chain from genesis to tip."""
        errors = []
        expected_prev = self.GENESIS_HASH

        for idx, block in enumerate(self.blocks):
            height = idx + 1
            if block.header.block_height != height:
                errors.append(f"Block {height} height index corrupted: header={block.header.block_height}")
            if block.header.previous_block_hash != expected_prev:
                errors.append(f"Block {height} previous hash broken: expected={expected_prev}, got={block.header.previous_block_hash}")

            valid, errs = block.verify_block_integrity(self.authorized_validators, self.quorum_threshold)
            if not valid:
                errors.extend([f"Block {height}: {e}" for e in errs])

            expected_prev = block.block_hash

        return (len(errors) == 0, errors)


class DLTConsensus:
    """
    BFT-style Consensus Engine managing proposals, multi-validator vote rounds,
    and final block construction across the authorized validator set.
    """

    def __init__(
        self,
        validators: List[DLTValidator],
        quorum_threshold: Optional[int] = None,
    ):
        self.validators: Dict[str, DLTValidator] = {v.validator_id: v for v in validators}
        num_vals = len(self.validators)
        self.quorum_threshold: int = quorum_threshold or (max(1, (2 * num_vals // 3) + 1))
        self.round_counter: int = 1

    def propose_block(
        self,
        proposer_id: str,
        current_tip_height: int,
        current_tip_hash: str,
        transactions: List[DecryptionReceipt]
    ) -> DLTBlock:
        proposer = self.validators.get(proposer_id)
        if not proposer:
            raise PermissionError(f"Proposer '{proposer_id}' not in authorized validator set")

        leaf_bytes = [tx.compute_receipt_hash().encode('utf-8') for tx in transactions]
        merkle_root, _ = build_merkle_tree(leaf_bytes)

        header = DLTBlockHeader(
            block_height=current_tip_height + 1,
            previous_block_hash=current_tip_hash,
            proposer_validator_id=proposer_id,
            round_number=self.round_counter,
            timestamp=datetime.now(timezone.utc).isoformat(),
            merkle_root=merkle_root
        )
        block_hash = header.compute_header_hash()
        block_msg = f"AEGIS-BLOCK-CONFIRM:{block_hash}".encode('utf-8')
        proposer_sig = proposer.sign(block_msg)

        block = DLTBlock(
            header=header,
            block_hash=block_hash,
            transactions=transactions,
            proposer_signature_b64=proposer_sig,
            quorum_signatures={}
        )
        return block

    def collect_votes_and_finalize(self, block: DLTBlock) -> DLTBlock:
        """
        Simulates decentralized BFT voting round:
        Each authorized validator independently checks the block and casts a vote.
        Once quorum is reached, finalizes block.
        """
        block_msg = f"AEGIS-BLOCK-CONFIRM:{block.block_hash}".encode('utf-8')
        votes: Dict[str, str] = {}
        total_weight = 0

        for val_id, validator in self.validators.items():
            if not validator.private_key_b64:
                continue
            # Validator independently checks receipt signatures
            all_tx_valid = all(tx.verify_recipient_signature() for tx in block.transactions)
            if all_tx_valid:
                sig = validator.sign(block_msg)
                votes[val_id] = sig
                total_weight += validator.voting_weight
                if total_weight >= self.quorum_threshold:
                    break

        if total_weight < self.quorum_threshold:
            raise RuntimeError(
                f"Consensus failed: received {total_weight} votes, needed {self.quorum_threshold}"
            )

        block.quorum_signatures = votes
        self.round_counter += 1
        return block


# ==============================================================================
# 5. Permissioned DLT Ledger Network (Orchestrator)
# ==============================================================================

class PermissionedDLTLedger:
    """
    High-level permissioned DLT ledger orchestrator.
    Manages a cluster of replicated DLT nodes (e.g., Node 1, Node 2, Node 3)
    operating fully air-gapped without external network calls.
    """

    def __init__(
        self,
        num_validators: int = 3,
        num_nodes: int = 3,
        validators: Optional[List[DLTValidator]] = None
    ):
        if validators:
            self.validators = validators
        else:
            self.validators = [
                DLTValidator.generate(f"val_{i+1}", voting_weight=1)
                for i in range(num_validators)
            ]

        self.val_map = {v.validator_id: v for v in self.validators}
        self.quorum_threshold = max(1, (2 * len(self.validators) // 3) + 1)
        self.consensus = DLTConsensus(self.validators, self.quorum_threshold)

        # Create replicated nodes
        self.nodes: Dict[str, DLTNode] = {
            f"node_{j+1}": DLTNode(f"node_{j+1}", self.val_map, self.quorum_threshold)
            for j in range(num_nodes)
        }

    def commit_receipt(
        self,
        receipt: DecryptionReceipt,
        proposer_id: Optional[str] = None
    ) -> DLTBlock:
        """
        Commits a recipient-signed DecryptionReceipt to the replicated DLT:
        1. Verifies recipient's own ML-DSA-65 signature (fails closed).
        2. Proposer creates block.
        3. Consensus round collects validator votes and seals block.
        4. Replicates block across ALL nodes in the permissioned network.
        """
        if not receipt.verify_recipient_signature():
            raise ValueError(
                f"Commit rejected: Invalid recipient ML-DSA-65 signature on receipt '{receipt.receipt_id}'"
            )

        # Use primary node to get tip
        primary_node = list(self.nodes.values())[0]
        prop_id = proposer_id or self.validators[0].validator_id

        proposed_block = self.consensus.propose_block(
            proposer_id=prop_id,
            current_tip_height=primary_node.get_tip_height(),
            current_tip_hash=primary_node.get_tip_hash(),
            transactions=[receipt]
        )

        finalized_block = self.consensus.collect_votes_and_finalize(proposed_block)

        # Replicate to ALL nodes
        for node in self.nodes.values():
            node.commit_block(finalized_block)

        return finalized_block

    def get_receipt(self, receipt_id: str) -> Optional[DecryptionReceipt]:
        primary_node = list(self.nodes.values())[0]
        return primary_node.get_receipt(receipt_id)

    def find_receipt_by_commitment(self, commitment: str) -> Optional[DecryptionReceipt]:
        primary_node = list(self.nodes.values())[0]
        return primary_node.find_receipt_by_commitment(commitment)

    def find_receipt_by_token(self, token: str) -> Optional[DecryptionReceipt]:
        primary_node = list(self.nodes.values())[0]
        return primary_node.find_receipt_by_token(token)

    def get_merkle_proof(self, receipt_id: str) -> Optional[MerkleProof]:
        primary_node = list(self.nodes.values())[0]
        return primary_node.get_merkle_proof(receipt_id)

    def verify_all_nodes(self) -> Dict[str, Tuple[bool, List[str]]]:
        """Verifies chain integrity and synchronization across all nodes."""
        results = {}
        for nid, node in self.nodes.items():
            results[nid] = node.verify_chain()
        return results

    def create_snapshot(self) -> DLTSnapshot:
        """Creates an authenticated state snapshot endorsed by validator quorum."""
        primary_node = list(self.nodes.values())[0]
        tip_height = primary_node.get_tip_height()
        tip_hash = primary_node.get_tip_hash()
        
        # Build state root over all receipt hashes
        all_leaf_bytes = [
            tx.compute_receipt_hash().encode('utf-8')
            for tx in primary_node.receipts.values()
        ]
        state_root, _ = build_merkle_tree(all_leaf_bytes)
        
        snapshot = DLTSnapshot(
            snapshot_id=f"snap_{tip_height}_{os.urandom(4).hex()}",
            block_height=tip_height,
            block_hash=tip_hash,
            state_merkle_root=state_root,
            receipt_count=len(primary_node.receipts),
        )
        snap_msg = snapshot.canonical_bytes()
        votes = {}
        weight = 0
        for val in self.validators:
            if val.private_key_b64:
                votes[val.validator_id] = val.sign(snap_msg)
                weight += val.voting_weight
                if weight >= self.quorum_threshold:
                    break
        snapshot.quorum_signatures = votes
        return snapshot


# Global default permissioned DLT instance
default_dlt_ledger = PermissionedDLTLedger()
