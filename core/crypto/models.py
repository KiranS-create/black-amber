from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class KeyPair(BaseModel):
    algorithm: str
    public_key_bytes: bytes
    private_key_bytes: Optional[bytes] = None

class EncapsulationResult(BaseModel):
    ciphertext: bytes
    shared_secret: bytes

class SymmetricCiphertext(BaseModel):
    nonce: bytes
    ciphertext: bytes
    tag: bytes
    associated_data: Optional[bytes] = None

class RecipientPackage(BaseModel):
    release_id: str
    document_id: str
    recipient_id: str
    encapsulated_key: bytes  # ML-KEM ciphertext
    encrypted_document: SymmetricCiphertext  # AES-256-GCM ciphertext
    algorithm_kem: str
    algorithm_sym: str
    document_hash: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
