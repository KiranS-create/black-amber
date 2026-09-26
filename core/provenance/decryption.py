import os
import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any
from pydantic import BaseModel

from core.crypto.models import SymmetricCiphertext
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import decrypt_aes_gcm, unwrap_key_aes_kw
from core.crypto.key_derivation import derive_recipient_wrapping_key
from core.recipient import Recipient, default_registry
from core.release import ReleaseRecipientPackage
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import EvidenceEvent, TamperEvidentLedger, default_ledger

class DecryptionResult(BaseModel):
    recipient_id: str
    release_id: str
    document_id: str
    original_document_hash: str
    traceable_artifact_hash: str
    event_id: str
    event_hash: str
    ledger_index: int

class RecipientDecryptionClient:
    """
    Client-side cryptographic decryption and provenance recording service.
    Ensures that recipient private keys perform the decapsulation and signing.
    """
    def __init__(
        self,
        ledger: Optional[TamperEvidentLedger] = None,
        traceability_provider: Optional[PrototypeTraceabilityProvider] = None
    ):
        self.ledger = ledger or default_ledger
        self.traceability_provider = traceability_provider or PrototypeTraceabilityProvider()

    def decrypt_package(
        self,
        package: ReleaseRecipientPackage,
        recipient: Recipient
    ) -> Tuple[bytes, bytes, EvidenceEvent, str]:
        """
        Execute full recipient decryption flow:
        1. Recipient ML-KEM decapsulation of kem_ciphertext with recipient.kem_keypair.private_key_bytes
        2. Derive domain-separated wrapping key via HKDF-SHA256
        3. Unwrap document symmetric key with authenticated release/recipient context
        4. AES-256-GCM decrypt document ciphertext with authenticated release associated data
        5. Verify document SHA-256 hash matches package.document_hash (ORIGINAL_DOCUMENT_HASH)
        6. Produce recipient-specific traceable copy with embedded marker
        7. Recipient signs decryption event using recipient.dsa_keypair.private_key_bytes
        8. Append event to tamper-evident ledger

        Returns: (plaintext_bytes, traceable_copy_bytes, evidence_event, event_hash)
        """
        if recipient.recipient_id != package.recipient_id:
            raise ValueError(
                f"Recipient mismatch: package is for '{package.recipient_id}', "
                f"but decryption attempted by '{recipient.recipient_id}'"
            )

        # 1. KEM Decapsulation
        kem_ciphertext = base64.b64decode(package.kem_ciphertext_b64)
        if not recipient.kem_keypair.private_key_bytes:
            raise ValueError("Recipient private KEM key is missing")
        
        shared_secret = MLKEM768.decapsulate(
            recipient.kem_keypair.private_key_bytes,
            kem_ciphertext
        )

        # 2. Derive domain-separated wrapping key
        wrapping_key = derive_recipient_wrapping_key(
            shared_secret=shared_secret,
            release_id=package.release_id,
            document_id=package.document_id,
            recipient_id=recipient.recipient_id,
            algorithm_id=package.algorithm_kem
        )

        # 3. Unwrap document key with authenticated context
        wrap_ad = f"KEY-WRAP-AUTH:{package.release_id}:{recipient.recipient_id}".encode('utf-8')
        wrapped_doc_key = base64.b64decode(package.wrapped_doc_key_b64)
        doc_key = unwrap_key_aes_kw(wrapping_key, wrapped_doc_key, associated_data=wrap_ad)

        # 4. Decrypt document with AES-256-GCM
        associated_data = f"DOC-RELEASE:{package.release_id}:{package.document_id}".encode('utf-8')
        nonce = base64.b64decode(package.encrypted_doc_nonce_b64)
        tag = base64.b64decode(package.encrypted_doc_tag_b64)
        ciphertext = base64.b64decode(package.encrypted_doc_ciphertext_b64)

        sym_ciphertext = SymmetricCiphertext(
            nonce=nonce,
            tag=tag,
            ciphertext=ciphertext,
            associated_data=associated_data
        )
        plaintext = decrypt_aes_gcm(doc_key, sym_ciphertext)

        # 5. Verify document hash against ORIGINAL_DOCUMENT_HASH
        computed_hash = hashlib.sha256(plaintext).hexdigest()
        if computed_hash != package.document_hash:
            raise ValueError(
                f"Integrity check failed: decrypted document hash '{computed_hash}' "
                f"does not match package hash '{package.document_hash}'"
            )

        # 6. Produce recipient-specific traceable copy
        marker = self.traceability_provider.issue_marker(
            document_id=package.document_id,
            release_id=package.release_id,
            recipient_id=recipient.recipient_id,
            document_hash=computed_hash,
            metadata={"recipient_name": recipient.name}
        )
        traceable_doc_bytes = self.traceability_provider.embed_marker(plaintext, marker)
        traceable_hash = hashlib.sha256(traceable_doc_bytes).hexdigest()
        marker_evidence_hash = hashlib.sha256(marker.signature_token.encode('utf-8')).hexdigest()

        # 7. Create and sign decryption evidence event with anti-replay nonce
        replay_nonce = os.urandom(16).hex()
        event_id = f"evt_dec_{package.release_id[:12]}_{recipient.recipient_id}_{os.urandom(3).hex()}"
        timestamp_now = datetime.now(timezone.utc).isoformat()
        prev_event_hash = self.ledger.get_last_event_hash()

        # Sign event payload (anchored to previous event hash, document ID, release ID, recipient ID, traceable hash)
        sign_payload = (
            f"DECRYPTION_PROVENANCE:{event_id}:{package.document_id}:"
            f"{package.release_id}:{recipient.recipient_id}:{traceable_hash}:"
            f"{prev_event_hash}:{timestamp_now}"
        ).encode('utf-8')

        if not recipient.dsa_keypair.private_key_bytes:
            raise ValueError("Recipient private DSA signing key is missing")

        signature_bytes = MLDSA65.sign(recipient.dsa_keypair.private_key_bytes, sign_payload)
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        signer_pub_b64 = base64.b64encode(recipient.dsa_keypair.public_key_bytes).decode('utf-8')

        event = EvidenceEvent(
            event_id=event_id,
            event_type="DECRYPTION_EVENT",
            timestamp=timestamp_now,
            document_id=package.document_id,
            release_id=package.release_id,
            recipient_id=recipient.recipient_id,
            algorithm=MLDSA65.ALGORITHM_NAME,
            artifact_hash=traceable_hash,
            evidence_hash=marker_evidence_hash,
            previous_event_hash=prev_event_hash,
            signature=signature_b64,
            signer_public_key_b64=signer_pub_b64,
            metadata={
                "recipient_name": recipient.name,
                "original_document_hash": computed_hash,
                "marker_token": marker.signature_token,
                "anti_replay_nonce": replay_nonce
            }
        )

        # 8. Record in ledger
        event_hash = self.ledger.append_event(event)

        return (plaintext, traceable_doc_bytes, event, event_hash)

default_decryption_client = RecipientDecryptionClient()
