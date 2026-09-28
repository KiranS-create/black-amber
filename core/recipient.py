import os
import json
import base64
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from core.crypto.models import KeyPair
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.identity.models import RecipientPrincipal, Identity, IdentityStatus
from core.identity.resolver import default_identity_resolver

class PublicRecipient(BaseModel):
    recipient_id: str
    identity_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    organization_id: Optional[str] = None
    provider: Optional[str] = None
    kem_public_key_b64: str
    dsa_public_key_b64: str
    algorithm_kem: str = "ML-KEM-768"
    algorithm_dsa: str = "ML-DSA-65"
    created_at: str
    status: str = "ACTIVE"
    revoked_at: Optional[str] = None

class Recipient(BaseModel):
    recipient_id: str
    identity_id: str = ""
    name: str
    email: Optional[str] = None
    organization_id: Optional[str] = None
    provider: Optional[str] = "local_directory"
    kem_keypair: KeyPair
    dsa_keypair: KeyPair
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "ACTIVE"
    revoked_at: Optional[str] = None

    def to_public(self) -> PublicRecipient:
        return PublicRecipient(
            recipient_id=self.recipient_id,
            identity_id=self.identity_id,
            name=self.name,
            email=self.email,
            organization_id=self.organization_id,
            provider=self.provider,
            kem_public_key_b64=base64.b64encode(self.kem_keypair.public_key_bytes).decode('utf-8'),
            dsa_public_key_b64=base64.b64encode(self.dsa_keypair.public_key_bytes).decode('utf-8'),
            algorithm_kem=self.kem_keypair.algorithm,
            algorithm_dsa=self.dsa_keypair.algorithm,
            created_at=self.created_at,
            status=self.status,
            revoked_at=self.revoked_at
        )

    def to_principal(self) -> RecipientPrincipal:
        return RecipientPrincipal(
            recipient_id=self.recipient_id,
            identity_id=self.identity_id,
            display_name=self.name,
            identity_provider=self.provider or "local_directory",
            kem_public_key_b64=base64.b64encode(self.kem_keypair.public_key_bytes).decode('utf-8'),
            dsa_public_key_b64=base64.b64encode(self.dsa_keypair.public_key_bytes).decode('utf-8'),
            algorithm_kem=self.kem_keypair.algorithm,
            algorithm_dsa=self.dsa_keypair.algorithm,
            status=IdentityStatus(self.status) if self.status in IdentityStatus._value2member_map_ else IdentityStatus.ACTIVE,
            created_at=self.created_at,
            revoked_at=self.revoked_at
        )

class RecipientRegistry:
    """
    Cryptographic Recipient Registry.
    Binds opaque recipient_ids to Identity records and manages post-quantum keypairs.
    """
    def __init__(self, storage_path: Optional[str] = None, resolver: Optional[Any] = None):
        self._recipients: Dict[str, Recipient] = {}
        self._identity_to_recipient: Dict[str, str] = {}
        self.storage_path = storage_path
        self.resolver = resolver or default_identity_resolver

    def clear(self):
        """Clear all enrolled recipients and identity mappings."""
        self._recipients.clear()
        self._identity_to_recipient.clear()

    def enroll(
        self,
        name: str,
        recipient_id: Optional[str] = None,
        identity_id: Optional[str] = None,
        email: Optional[str] = None,
        organization_id: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Recipient:
        if recipient_id is None:
            entropy = os.urandom(8).hex()
            recipient_id = f"rec_{entropy}"
        
        if recipient_id in self._recipients:
            return self._recipients[recipient_id]

        if not identity_id:
            # Generate stable internal identity reference if not provided
            clean_ident = hashlib.sha256(f"{name}:{recipient_id}".encode()).hexdigest()[:10]
            identity_id = f"usr_{clean_ident}"

        kem_kp = MLKEM768.generate_keypair()
        dsa_kp = MLDSA65.generate_keypair()

        recipient = Recipient(
            recipient_id=recipient_id,
            identity_id=identity_id,
            name=name,
            email=email,
            organization_id=organization_id,
            provider=provider or "local_directory",
            kem_keypair=kem_kp,
            dsa_keypair=dsa_kp,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="ACTIVE"
        )
        self._recipients[recipient_id] = recipient
        self._identity_to_recipient[identity_id] = recipient_id

        # Register in identity resolver
        principal = recipient.to_principal()
        self.resolver.register_principal(principal)

        return recipient

    def enroll_identity(self, identity: Identity, recipient_id: Optional[str] = None) -> Recipient:
        """Enroll an enterprise Identity as a cryptographic recipient."""
        if identity.identity_id in self._identity_to_recipient:
            rec_id = self._identity_to_recipient[identity.identity_id]
            return self._recipients[rec_id]

        return self.enroll(
            name=identity.display_name,
            recipient_id=recipient_id,
            identity_id=identity.identity_id,
            email=identity.email,
            organization_id=identity.organization_id,
            provider=identity.provider
        )

    def revoke(self, recipient_id: str) -> bool:
        """Revoke a recipient principal while preserving historical auditability."""
        rec = self._recipients.get(recipient_id)
        if not rec:
            return False
        rec.status = "REVOKED"
        rec.revoked_at = datetime.now(timezone.utc).isoformat()
        principal = rec.to_principal()
        self.resolver.register_principal(principal)
        return True

    def get(self, recipient_id: str) -> Optional[Recipient]:
        return self._recipients.get(recipient_id)

    def get_by_identity(self, identity_id: str) -> Optional[Recipient]:
        rec_id = self._identity_to_recipient.get(identity_id)
        if rec_id:
            return self._recipients.get(rec_id)
        return None

    def list_all(self) -> List[Recipient]:
        return list(self._recipients.values())

    def list_public(self) -> List[PublicRecipient]:
        return [r.to_public() for r in self._recipients.values()]

    def init_demo_recipients(self) -> Dict[str, Recipient]:
        """Test fixture compatibility helper for legacy unit and integration tests."""
        demo_users = [("Alice", "alice"), ("Bob", "bob"), ("Charlie", "charlie")]
        res = {}
        for name, rec_id in demo_users:
            if rec_id not in self._recipients:
                res[name] = self.enroll(
                    name=name,
                    recipient_id=rec_id,
                    identity_id=f"usr_test_{rec_id}",
                    email=f"{rec_id}@example.test"
                )
            else:
                res[name] = self._recipients[rec_id]
        return res

# Global registry instance pre-initialized for test fixtures
default_registry = RecipientRegistry()
default_registry.init_demo_recipients()
