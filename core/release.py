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
from core.identity.targeting import ReleaseTargetingService, ReleaseTargetSpec, ReleaseTargetType
from core.identity.models import Identity

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
    target_summary: Optional[Dict[str, Any]] = None
    shared_payload: Optional[Any] = None
    capsules: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = "default_tenant"

class ReleaseManager:
    def __init__(
        self,
        registry: Optional[RecipientRegistry] = None,
        targeting_service: Optional[ReleaseTargetingService] = None
    ):
        self.registry = registry or default_registry
        self.targeting_service = targeting_service or ReleaseTargetingService()
        self.releases: Dict[str, DocumentRelease] = {}

    def clear(self):
        """Clear all active releases."""
        self.releases.clear()

    def create_release(
        self,
        document_bytes: bytes,
        document_name: str,
        issuer_id: str,
        recipient_ids: List[str],
        document_id: Optional[str] = None,
        release_id: Optional[str] = None,
        target_summary: Optional[Dict[str, Any]] = None,
        tenant_id: str = "default_tenant"
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

        # Create shared payload
        from core.crypto.capsule import SharedDocumentPayload, CryptographicCapsule, assemble_recipient_package
        shared_payload = SharedDocumentPayload(
            release_id=rel_id,
            document_id=doc_id,
            document_name=document_name,
            original_hash=original_hash,
            encrypted_doc_nonce_b64=enc_nonce_b64,
            encrypted_doc_tag_b64=enc_tag_b64,
            encrypted_doc_ciphertext_b64=enc_ct_b64,
            algorithm_sym="AES-256-GCM",
            created_at=timestamp_now
        )

        capsules: Dict[str, CryptographicCapsule] = {}

        # 4. For each recipient: ML-KEM encapsulation + domain-separated key derivation + wrap
        for r_id in recipient_ids:
            recipient = self.registry.get(r_id)
            if not recipient:
                raise ValueError(f"Recipient {r_id} is not registered")
            if recipient.status != "ACTIVE":
                raise ValueError(f"Cannot create release package for inactive recipient '{r_id}' (status: {recipient.status})")
            
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

            kem_ct_b64 = base64.b64encode(encap_res.ciphertext).decode('utf-8')
            wrapped_key_b64 = base64.b64encode(wrapped_doc_key).decode('utf-8')

            capsule = CryptographicCapsule(
                recipient_id=r_id,
                kem_ciphertext_b64=kem_ct_b64,
                wrapped_doc_key_b64=wrapped_key_b64,
                algorithm_kem=MLKEM768.ALGORITHM_NAME,
                timestamp=timestamp_now
            )
            capsules[r_id] = capsule

            package = ReleaseRecipientPackage(
                release_id=rel_id,
                document_id=doc_id,
                recipient_id=r_id,
                kem_ciphertext_b64=kem_ct_b64,
                wrapped_doc_key_b64=wrapped_key_b64,
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
            packages=packages,
            target_summary=target_summary,
            shared_payload=shared_payload.model_dump(),
            capsules={k: v.model_dump() for k, v in capsules.items()},
            tenant_id=tenant_id
        )

        self.releases[rel_id] = release
        return release

    def create_scalable_release(
        self,
        document_bytes: bytes,
        document_name: str,
        issuer_id: str,
        recipient_ids: List[str],
        document_id: Optional[str] = None,
        release_id: Optional[str] = None,
        target_summary: Optional[Dict[str, Any]] = None
    ) -> DocumentRelease:
        """
        Scalable variant for large recipient counts (1,000 to 1,000,000).
        Stores document ciphertext ONCE (O(1)) and creates lightweight O(N) capsules.
        Does not eagerly allocate N redundant packages in memory; reconstructs on demand.
        """
        if not recipient_ids:
            raise ValueError("Release must have at least one recipient")

        from core.crypto.capsule import SharedDocumentPayload, CryptographicCapsule
        original_hash = hashlib.sha256(document_bytes).hexdigest()
        doc_id = document_id or f"doc_{hashlib.sha256(document_bytes[:64] + os.urandom(4)).hexdigest()[:12]}"
        rel_id = release_id or f"rel_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{os.urandom(3).hex()}"
        
        doc_key = generate_symmetric_key()
        associated_data = f"DOC-RELEASE:{rel_id}:{doc_id}".encode('utf-8')
        enc_doc = encrypt_aes_gcm(doc_key, document_bytes, associated_data=associated_data)

        enc_nonce_b64 = base64.b64encode(enc_doc.nonce).decode('utf-8')
        enc_tag_b64 = base64.b64encode(enc_doc.tag).decode('utf-8')
        enc_ct_b64 = base64.b64encode(enc_doc.ciphertext).decode('utf-8')

        timestamp_now = datetime.now(timezone.utc).isoformat()
        shared_payload = SharedDocumentPayload(
            release_id=rel_id,
            document_id=doc_id,
            document_name=document_name,
            original_hash=original_hash,
            encrypted_doc_nonce_b64=enc_nonce_b64,
            encrypted_doc_tag_b64=enc_tag_b64,
            encrypted_doc_ciphertext_b64=enc_ct_b64,
            algorithm_sym="AES-256-GCM",
            created_at=timestamp_now
        )

        capsules: Dict[str, Any] = {}
        for r_id in recipient_ids:
            recipient = self.registry.get(r_id)
            if not recipient:
                raise ValueError(f"Recipient {r_id} is not registered")
            if recipient.status != "ACTIVE":
                raise ValueError(f"Cannot create release package for inactive recipient '{r_id}'")
            
            encap_res = MLKEM768.encapsulate(recipient.kem_keypair.public_key_bytes)
            wrapping_key = derive_recipient_wrapping_key(
                shared_secret=encap_res.shared_secret,
                release_id=rel_id,
                document_id=doc_id,
                recipient_id=r_id,
                algorithm_id=MLKEM768.ALGORITHM_NAME
            )
            wrap_ad = f"KEY-WRAP-AUTH:{rel_id}:{r_id}".encode('utf-8')
            wrapped_doc_key = wrap_key_aes_kw(wrapping_key, doc_key, associated_data=wrap_ad)

            capsule = CryptographicCapsule(
                recipient_id=r_id,
                kem_ciphertext_b64=base64.b64encode(encap_res.ciphertext).decode('utf-8'),
                wrapped_doc_key_b64=base64.b64encode(wrapped_doc_key).decode('utf-8'),
                algorithm_kem=MLKEM768.ALGORITHM_NAME,
                timestamp=timestamp_now
            )
            capsules[r_id] = capsule.model_dump()

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
            packages={},  # Omitted to save RAM at million scale
            target_summary=target_summary,
            shared_payload=shared_payload.model_dump(),
            capsules=capsules
        )
        self.releases[rel_id] = release
        return release

    def create_release_from_targets(
        self,
        document_bytes: bytes,
        document_name: str,
        issuer_id: str,
        target_spec: ReleaseTargetSpec,
        document_id: Optional[str] = None,
        release_id: Optional[str] = None
    ) -> DocumentRelease:
        """
        Create a release targeting directory individuals or groups.
        Resolves each target identity and ensures individual cryptographic bindings.
        """
        identities = self.targeting_service.resolve_targets(target_spec)
        recipient_ids: List[str] = []

        for ident in identities:
            rec = self.registry.get_by_identity(ident.identity_id)
            if not rec:
                rec = self.registry.enroll_identity(ident)
            recipient_ids.append(rec.recipient_id)

        target_summary = {
            "target_type": target_spec.target_type.value,
            "target_ids": target_spec.target_ids,
            "resolved_identities_count": len(identities)
        }

        return self.create_release(
            document_bytes=document_bytes,
            document_name=document_name,
            issuer_id=issuer_id,
            recipient_ids=recipient_ids,
            document_id=document_id,
            release_id=release_id,
            target_summary=target_summary
        )

    def get_release(self, release_id: str) -> Optional[DocumentRelease]:
        return self.releases.get(release_id)

    def get_recipient_package(self, release_id: str, recipient_id: str) -> Optional[ReleaseRecipientPackage]:
        release = self.get_release(release_id)
        if not release:
            return None
        if recipient_id in release.packages:
            return release.packages[recipient_id]
        if release.shared_payload and recipient_id in release.capsules:
            from core.crypto.capsule import assemble_recipient_package, CryptographicCapsule, SharedDocumentPayload
            capsule_raw = release.capsules[recipient_id]
            capsule = capsule_raw if isinstance(capsule_raw, CryptographicCapsule) else CryptographicCapsule(**capsule_raw)
            payload_raw = release.shared_payload
            payload = payload_raw if isinstance(payload_raw, SharedDocumentPayload) else SharedDocumentPayload(**payload_raw)
            return assemble_recipient_package(capsule, payload)
        return None

    def list_releases(self) -> List[DocumentRelease]:
        return list(self.releases.values())

default_release_manager = ReleaseManager()
