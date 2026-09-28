"""
AegisTrace Immutable Forensic Backup Format & Content-Addressed Storage.

Provides canonical serialization, content-addressed object storage,
RFC-6962 Merkle tree commitment, and archive packaging for forensic state backups.
No unstable Python pickle or platform-dependent serialization is permitted.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from pydantic import BaseModel

from core.ledger.dlt import build_merkle_tree
from core.recovery.models import BackupObjectRecord, SignedBackupManifest


def canonical_json_bytes(data: Any) -> bytes:
    """
    Deterministic canonical JSON serialization.
    - Strict lexicographical key sorting
    - Compact separators (no trailing spaces: ',', ':')
    - UTF-8 encoding
    - Rejects unstable/non-serializable types
    """
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    elif hasattr(data, "dict"):
        data = data.dict()
    
    canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return canonical_str.encode('utf-8')


class ContentAddressedStore:
    """
    Immutable, content-addressed object storage engine.
    Every object is indexed strictly by the SHA-256 hash of its byte content.
    Guarantees bit-level integrity and deduplication across backups.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir
        self._memory_objects: Dict[str, bytes] = {}
        if self.base_dir:
            os.makedirs(self.base_dir, exist_ok=True)

    def put_bytes(self, payload: bytes) -> str:
        """
        Stores raw payload and returns its SHA-256 content address.
        """
        digest = hashlib.sha256(payload).hexdigest()
        if self.base_dir:
            obj_path = os.path.join(self.base_dir, digest)
            if not os.path.exists(obj_path):
                temp_path = f"{obj_path}.tmp_{os.urandom(8).hex()}"
                with open(temp_path, "wb") as f:
                    f.write(payload)
                os.replace(temp_path, obj_path)
        else:
            self._memory_objects[digest] = payload
        return digest

    def put_object(self, obj: Any) -> Tuple[str, int]:
        """
        Serializes and stores an object canonically.
        Returns: (sha256_digest, byte_count)
        """
        payload = canonical_json_bytes(obj)
        digest = self.put_bytes(payload)
        return digest, len(payload)

    def get_bytes(self, object_id: str) -> bytes:
        """
        Retrieves raw payload by object_id, verifying content hash.
        Fails closed with ValueError if the stored object is corrupt or missing.
        """
        payload: Optional[bytes] = None
        if self.base_dir:
            obj_path = os.path.join(self.base_dir, object_id)
            if not os.path.exists(obj_path):
                raise FileNotFoundError(f"Content-addressed object '{object_id}' not found.")
            with open(obj_path, "rb") as f:
                payload = f.read()
        else:
            if object_id not in self._memory_objects:
                raise FileNotFoundError(f"Content-addressed object '{object_id}' not found.")
            payload = self._memory_objects[object_id]

        # Verify integrity
        computed = hashlib.sha256(payload).hexdigest()
        if computed != object_id:
            raise ValueError(
                f"CORRUPTED_OBJECT: Content-addressed object '{object_id}' hash mismatch! Computed: '{computed}'"
            )
        return payload

    def get_object(self, object_id: str) -> Any:
        """Retrieves and deserializes canonical JSON object."""
        payload = self.get_bytes(object_id)
        return json.loads(payload.decode('utf-8'))

    def has_object(self, object_id: str) -> bool:
        if self.base_dir:
            return os.path.exists(os.path.join(self.base_dir, object_id))
        return object_id in self._memory_objects


class BackupPackageBuilder:
    """
    Constructs a deterministic backup package from individual datasets.
    Computes object records, RFC-6962 Merkle tree commitment, and package structure.
    """

    def __init__(self, store: ContentAddressedStore):
        self.store = store
        self.objects: List[BackupObjectRecord] = []
        self.datasets: Set[str] = set()

    def add_dataset(
        self,
        dataset_type: str,
        records: List[Any],
        tenant_id: str = "default_tenant"
    ) -> BackupObjectRecord:
        """
        Adds a list of records as a content-addressed object.
        """
        digest, size = self.store.put_object(records)
        record = BackupObjectRecord(
            object_id=digest,
            dataset_type=dataset_type,
            tenant_id=tenant_id,
            byte_size=size,
            object_count=len(records)
        )
        self.objects.append(record)
        self.datasets.add(dataset_type)
        return record

    def compute_merkle_root(self) -> str:
        """
        Computes RFC-6962 double-domain binary Merkle root over sorted object IDs.
        """
        sorted_digests = sorted([o.object_id for o in self.objects])
        leaf_bytes_list = [d.encode('utf-8') for d in sorted_digests]
        root_hash, _ = build_merkle_tree(leaf_bytes_list)
        return root_hash
