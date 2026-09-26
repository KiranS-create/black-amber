import os
import json
import base64
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from core.crypto.models import KeyPair
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65

class PublicRecipient(BaseModel):
    recipient_id: str
    name: str
    kem_public_key_b64: str
    dsa_public_key_b64: str
    algorithm_kem: str = "ML-KEM-768"
    algorithm_dsa: str = "ML-DSA-65"
    created_at: str
    status: str = "ACTIVE"

class Recipient(BaseModel):
    recipient_id: str
    name: str
    kem_keypair: KeyPair
    dsa_keypair: KeyPair
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "ACTIVE"

    def to_public(self) -> PublicRecipient:
        return PublicRecipient(
            recipient_id=self.recipient_id,
            name=self.name,
            kem_public_key_b64=base64.b64encode(self.kem_keypair.public_key_bytes).decode('utf-8'),
            dsa_public_key_b64=base64.b64encode(self.dsa_keypair.public_key_bytes).decode('utf-8'),
            algorithm_kem=self.kem_keypair.algorithm,
            algorithm_dsa=self.dsa_keypair.algorithm,
            created_at=self.created_at,
            status=self.status
        )

# In-memory repository with file persistence support
class RecipientRegistry:
    def __init__(self, storage_path: Optional[str] = None):
        self._recipients: Dict[str, Recipient] = {}
        self.storage_path = storage_path

    def enroll(self, name: str, recipient_id: Optional[str] = None) -> Recipient:
        if recipient_id is None:
            clean_name = name.lower().replace(" ", "_")
            recipient_id = f"rec_{clean_name}_{os.urandom(3).hex()}"
        
        if recipient_id in self._recipients:
            return self._recipients[recipient_id]

        kem_kp = MLKEM768.generate_keypair()
        dsa_kp = MLDSA65.generate_keypair()

        recipient = Recipient(
            recipient_id=recipient_id,
            name=name,
            kem_keypair=kem_kp,
            dsa_keypair=dsa_kp,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="ACTIVE"
        )
        self._recipients[recipient_id] = recipient
        return recipient

    def get(self, recipient_id: str) -> Optional[Recipient]:
        return self._recipients.get(recipient_id)

    def list_all(self) -> List[Recipient]:
        return list(self._recipients.values())

    def list_public(self) -> List[PublicRecipient]:
        return [r.to_public() for r in self._recipients.values()]

    def init_demo_recipients(self) -> Dict[str, Recipient]:
        demo_users = [("Alice", "alice"), ("Bob", "bob"), ("Charlie", "charlie")]
        res = {}
        for name, rec_id in demo_users:
            if rec_id not in self._recipients:
                res[name] = self.enroll(name=name, recipient_id=rec_id)
            else:
                res[name] = self._recipients[rec_id]
        return res

# Global registry instance pre-initialized with demo users
default_registry = RecipientRegistry()
default_registry.init_demo_recipients()
