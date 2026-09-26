import os
from typing import Optional, Tuple
from Crypto.Cipher import AES
from core.crypto.models import SymmetricCiphertext

def generate_symmetric_key() -> bytes:
    """Generate a random 256-bit (32 bytes) symmetric key for AES-256-GCM."""
    return os.urandom(32)

def encrypt_aes_gcm(
    key: bytes,
    plaintext: bytes,
    associated_data: Optional[bytes] = None,
    nonce: Optional[bytes] = None
) -> SymmetricCiphertext:
    """
    Encrypt plaintext using AES-256-GCM.
    Returns nonce, ciphertext, 16-byte tag, and associated data.
    """
    if len(key) != 32:
        raise ValueError(f"AES-256 key must be exactly 32 bytes, got {len(key)}")
    
    if nonce is None:
        nonce = os.urandom(12)  # Standard 96-bit nonce for GCM
    elif len(nonce) != 12:
        raise ValueError(f"AES-GCM nonce must be 12 bytes, got {len(nonce)}")

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    if associated_data:
        cipher.update(associated_data)
    
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    return SymmetricCiphertext(
        nonce=nonce,
        ciphertext=ciphertext,
        tag=tag,
        associated_data=associated_data
    )

def decrypt_aes_gcm(
    key: bytes,
    encrypted: SymmetricCiphertext
) -> bytes:
    """
    Decrypt ciphertext using AES-256-GCM and verify tag authentication.
    Raises ValueError if authentication fails.
    """
    if len(key) != 32:
        raise ValueError(f"AES-256 key must be exactly 32 bytes, got {len(key)}")
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=encrypted.nonce)
    if encrypted.associated_data:
        cipher.update(encrypted.associated_data)
    
    return cipher.decrypt_and_verify(encrypted.ciphertext, encrypted.tag)

def wrap_key_aes_kw(wrapping_key: bytes, key_to_wrap: bytes) -> bytes:
    """Wrap a 256-bit document key using AES-GCM with the derived wrapping key."""
    encrypted = encrypt_aes_gcm(wrapping_key, key_to_wrap, associated_data=b"KEY-WRAP-AUTH")
    # Pack nonce (12) + tag (16) + ciphertext (32)
    return encrypted.nonce + encrypted.tag + encrypted.ciphertext

def unwrap_key_aes_kw(wrapping_key: bytes, wrapped_payload: bytes) -> bytes:
    """Unwrap a 256-bit document key."""
    if len(wrapped_payload) < 28:
        raise ValueError("Wrapped payload is too short")
    nonce = wrapped_payload[:12]
    tag = wrapped_payload[12:28]
    ciphertext = wrapped_payload[28:]
    encrypted = SymmetricCiphertext(
        nonce=nonce,
        tag=tag,
        ciphertext=ciphertext,
        associated_data=b"KEY-WRAP-AUTH"
    )
    return decrypt_aes_gcm(wrapping_key, encrypted)
