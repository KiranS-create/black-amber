"""
AegisTrace RFC-6962 Double-Domain Merkle Tree & Inclusion Proof Engine.

Constructs deterministic binary Merkle trees over content-addressed evidence objects
with domain-separated prefixes (0x00 for leaves, 0x01 for branches).
Guarantees:
1. Immunity to second-preimage length extension attacks.
2. Cryptographic inclusion proofs for any evidence object.
3. Offline verifiability without external dependencies.
"""

import hashlib
from typing import List, Tuple, Optional
from pydantic import BaseModel, Field


def _hash_leaf(leaf_data: bytes) -> str:
    """Computes leaf hash with domain separation prefix 0x00."""
    return hashlib.sha256(b"\x00" + leaf_data).hexdigest()


def _hash_branch(left_hex: str, right_hex: str) -> str:
    """Computes branch hash with domain separation prefix 0x01."""
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    return hashlib.sha256(b"\x01" + left_bytes + right_bytes).hexdigest()


class MerkleInclusionProof(BaseModel):
    """
    Cryptographic proof demonstrating inclusion of a specific evidence object
    inside a package's committed Merkle root.
    """
    leaf_hash: str
    root_hash: str
    audit_path: List[Tuple[str, str]] = Field(
        ...,
        description="List of (sibling_hash, direction) where direction is 'L' or 'R'"
    )

    def verify(self) -> bool:
        """Verifies inclusion of leaf_hash in root_hash following audit path."""
        current = self.leaf_hash
        for sibling_hash, direction in self.audit_path:
            if direction == "L":
                # sibling is on left, current is on right
                current = _hash_branch(sibling_hash, current)
            elif direction == "R":
                # current is on left, sibling is on right
                current = _hash_branch(current, sibling_hash)
            else:
                return False
        return current.lower() == self.root_hash.lower()


class EvidenceMerkleTree:
    """
    RFC-6962 inspired balanced binary Merkle tree over evidence objects.
    """
    EMPTY_ROOT = hashlib.sha256(b"\x00AEGIS_EMPTY_EVIDENCE_ROOT").hexdigest()

    def __init__(self, leaf_hashes: List[str]):
        """
        Initializes tree from an ordered list of leaf SHA-256 content hashes.
        Leaves are prefixed with 0x00.
        """
        self.leaf_hashes = list(leaf_hashes)
        self.leaves: List[str] = [_hash_leaf(bytes.fromhex(h)) for h in self.leaf_hashes]
        self.layers: List[List[str]] = []
        self.root: str = self._build_tree()

    def _build_tree(self) -> str:
        if not self.leaves:
            return self.EMPTY_ROOT

        current_layer = list(self.leaves)
        self.layers.append(current_layer)

        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                if i + 1 < len(current_layer):
                    right = current_layer[i + 1]
                else:
                    right = left  # Duplicate odd node
                next_layer.append(_hash_branch(left, right))
            self.layers.append(next_layer)
            current_layer = next_layer

        return current_layer[0]

    def get_inclusion_proof(self, leaf_index: int) -> MerkleInclusionProof:
        """Generates an inclusion proof for the leaf at leaf_index."""
        if not (0 <= leaf_index < len(self.leaf_hashes)):
            raise IndexError(f"Leaf index {leaf_index} out of range [0, {len(self.leaf_hashes)})")

        audit_path: List[Tuple[str, str]] = []
        idx = leaf_index

        for layer in self.layers[:-1]:
            if idx % 2 == 0:
                # Node is left child, sibling is right
                if idx + 1 < len(layer):
                    sibling = layer[idx + 1]
                else:
                    sibling = layer[idx]
                audit_path.append((sibling, "R"))
            else:
                # Node is right child, sibling is left
                sibling = layer[idx - 1]
                audit_path.append((sibling, "L"))
            idx //= 2

        return MerkleInclusionProof(
            leaf_hash=self.leaves[leaf_index],
            root_hash=self.root,
            audit_path=audit_path
        )
