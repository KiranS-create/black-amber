"""
Scalable Cryptographic Capsule & Shared Envelope Architecture for AegisTrace.

Solves the O(N * doc_size) ciphertext replication bottleneck in multi-recipient releases.
Instead of replicating the document ciphertext N times for N recipients:
1. Document ciphertext C_doc is encrypted once under random document key K_doc (O(1) storage).
2. For each recipient, a lightweight Cryptographic Capsule is created:
   - ML-KEM-768 encapsulation of K_doc (1,088 bytes)
   - Authenticated key-wrap of K_doc (40 bytes)
   - Total capsule overhead: ~1.1 KB per recipient.
3. Decryption reassembles the full package on demand, or decrypts directly from
   (capsule, shared_payload).
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class CryptographicCapsule(BaseModel):
    """
    Lightweight, recipient-specific cryptographic envelope capsule.
    Size: ~1.1 KB (ML-KEM-768 ciphertext + wrapped key).
    """
    recipient_id: str
    kem_ciphertext_b64: str
    wrapped_doc_key_b64: str
    algorithm_kem: str = "ML-KEM-768"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SharedDocumentPayload(BaseModel):
    """
    Single, immutable document ciphertext payload shared across all recipients of a release.
    Stored once per release: O(1) in document size.
    """
    release_id: str
    document_id: str
    document_name: str
    original_hash: str
    encrypted_doc_nonce_b64: str
    encrypted_doc_tag_b64: str
    encrypted_doc_ciphertext_b64: str
    algorithm_sym: str = "AES-256-GCM"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def assemble_recipient_package(
    capsule: CryptographicCapsule,
    payload: SharedDocumentPayload
):
    """
    Reconstructs a backward-compatible ReleaseRecipientPackage on-demand
    from a shared payload and recipient capsule.
    Avoids storing redundant ciphertexts while satisfying legacy callers.
    """
    from core.release import ReleaseRecipientPackage
    return ReleaseRecipientPackage(
        release_id=payload.release_id,
        document_id=payload.document_id,
        recipient_id=capsule.recipient_id,
        kem_ciphertext_b64=capsule.kem_ciphertext_b64,
        wrapped_doc_key_b64=capsule.wrapped_doc_key_b64,
        encrypted_doc_nonce_b64=payload.encrypted_doc_nonce_b64,
        encrypted_doc_tag_b64=payload.encrypted_doc_tag_b64,
        encrypted_doc_ciphertext_b64=payload.encrypted_doc_ciphertext_b64,
        algorithm_kem=capsule.algorithm_kem,
        algorithm_sym=payload.algorithm_sym,
        document_hash=payload.original_hash,
        timestamp=capsule.timestamp
    )


def estimate_storage_metrics(
    doc_size_bytes: int,
    recipient_count: int,
    capsule_overhead_bytes: int = 1128
) -> Dict[str, Any]:
    """
    Analytically calculates storage footprint for naive replication vs shared capsule architecture.
    """
    naive_bytes = (doc_size_bytes + capsule_overhead_bytes) * recipient_count
    shared_bytes = doc_size_bytes + (capsule_overhead_bytes * recipient_count)
    saved_bytes = max(0, naive_bytes - shared_bytes)
    savings_pct = (saved_bytes / naive_bytes * 100.0) if naive_bytes > 0 else 0.0

    return {
        "recipient_count": recipient_count,
        "doc_size_bytes": doc_size_bytes,
        "naive_storage_bytes": naive_bytes,
        "shared_storage_bytes": shared_bytes,
        "saved_storage_bytes": saved_bytes,
        "savings_percentage": round(savings_pct, 4)
    }
