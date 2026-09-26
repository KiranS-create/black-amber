import os
import hashlib
import json
import base64
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.crypto.models import SymmetricCiphertext, RecipientPackage
from core.crypto.symmetric import generate_symmetric_key, encrypt_aes_gcm, wrap_key_aes_kw
from core.crypto.kem import MLKEM768
from core.crypto.key_derivation import derive_recipient_wrapping_key
from core.recipient import RecipientRegistry, default_registry

class ReleaseRecipientPackage(BaseModel):
    release_id: str
    document_id: str
    recipient_id: str
    kem_ciphertext_b64: str  # ML-KEM-768 ciphertext
    wrapped_doc_key_b64: str  # Document key wrapped with KEM-derived wrapping key
    encrypted_doc_nonce_b64: str
    encrypted_doc_tag_b64: str
    encrypted_doc_ciphertext_b64: str
    algorithm_kem: str = "ML-KEM-768"
    algorithm_sym: str = "AES-256-GCM"
    document_hash: str
    timestamp: str

class DocumentRelease(BaseModel):
    release_id: str
    document_id: str
    document_name: str
    original_hash: str  # SHA-256 hex digest of pristine plaintext document
    issuer_id: str
    recipient_ids: List[str]
    crypto_parameters: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    packages: Dict[str, ReleaseRecipientPackage] = Field(default_factory=dict)

class ReleaseManager:
    def __init__(self, registry: Optional[RecipientRegistry] = None):
        self.registry = registry or default_registry
        self.releases: Dict[str, DocumentRelease] = {}

    def create_release(
        self,
        document_bytes: bytes,
        document_name: str,
        issuer_id: str,
        recipient_ids: List[str],
        document_id: Optional[str] = None,
        release_id: Optional[str] = None
    ) -> DocumentRelease:
        if not recipient_ids:
            raise ValueError("Release must have at least one recipient")

        # 1. Compute original document SHA-256 hash (ORIGINAL_DOCUMENT_HASH)
        original_hash = hashlib.sha256(document_bytes).hexdigest()
        
        doc_id = document_id or f"doc_{hashlib.sha256(document_bytes[:64] + os.urandom(4)).hexdigest()[:12]}"
        rel_id = release_id or f"rel_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{os.urandom(3).hex()}"
        
        # 2. Generate random 256-bit document key (K_doc)
        doc_key = generate_symmetric_key()

        # 3. Encrypt document once with AES-256-GCM using authenticated associated data
        associated_data = f"DOC-RELEASE:{rel_id}:{doc_id}".encode('utf-8')
        enc_doc = encrypt_aes_gcm(doc_key, document_bytes, associated_data=associated_data)

        enc_nonce_b64 = base64.b64encode(enc_doc.nonce).decode('utf-8')
        enc_tag_b64 = base64.b64encode(enc_doc.tag).decode('utf-8')
        enc_ct_b64 = base64.b64encode(enc_doc.ciphertext).decode('utf-8')

        packages: Dict[str, ReleaseRecipientPackage] = {}
        timestamp_now = datetime.now(timezone.utc).isoformat()

        # 4. For each recipient: ML-KEM encapsulation + domain-separated key derivation + wrap
        for r_id in recipient_ids:
            recipient = self.registry.get(r_id)
            if not recipient:
                raise ValueError(f"Recipient {r_id} is not registered")
            
            # ML-KEM-768 encapsulation with recipient's public key
            encap_res = MLKEM768.encapsulate(recipient.kem_keypair.public_key_bytes)
            
            # Derive wrapping key using explicit domain separation
            wrapping_key = derive_recipient_wrapping_key(
                shared_secret=encap_res.shared_secret,
                release_id=rel_id,
                document_id=doc_id,
                recipient_id=r_id,
                algorithm_id=MLKEM768.ALGORITHM_NAME
            )

            # Wrap document key with authenticated release/recipient context
            wrap_ad = f"KEY-WRAP-AUTH:{rel_id}:{r_id}".encode('utf-8')
            wrapped_doc_key = wrap_key_aes_kw(wrapping_key, doc_key, associated_data=wrap_ad)

            package = ReleaseRecipientPackage(
                release_id=rel_id,
                document_id=doc_id,
                recipient_id=r_id,
                kem_ciphertext_b64=base64.b64encode(encap_res.ciphertext).decode('utf-8'),
                wrapped_doc_key_b64=base64.b64encode(wrapped_doc_key).decode('utf-8'),
                encrypted_doc_nonce_b64=enc_nonce_b64,
                encrypted_doc_tag_b64=enc_tag_b64,
                encrypted_doc_ciphertext_b64=enc_ct_b64,
                algorithm_kem=MLKEM768.ALGORITHM_NAME,
                algorithm_sym="AES-256-GCM",
                document_hash=original_hash,
                timestamp=timestamp_now
            )
            packages[r_id] = package

        release = DocumentRelease(
            release_id=rel_id,
            document_id=doc_id,
            document_name=document_name,
            original_hash=original_hash,
            issuer_id=issuer_id,
            recipient_ids=recipient_ids,
            crypto_parameters={
                "kem_algorithm": MLKEM768.ALGORITHM_NAME,
                "kem_provider": MLKEM768.get_metadata().get("provider"),
                "sym_algorithm": "AES-256-GCM",
                "key_length_bits": 256,
                "derivation": "HKDF-SHA256-DomainSeparated"
            },
            created_at=timestamp_now,
            packages=packages
        )

        self.releases[rel_id] = release
        return release

    def get_release(self, release_id: str) -> Optional[DocumentRelease]:
        return self.releases.get(release_id)

    def get_recipient_package(self, release_id: str, recipient_id: str) -> Optional[ReleaseRecipientPackage]:
        release = self.get_release(release_id)
        if not release:
            return None
        return release.packages.get(recipient_id)

    def list_releases(self) -> List[DocumentRelease]:
        return list(self.releases.values())

default_release_manager = ReleaseManager()
