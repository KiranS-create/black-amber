import os
from typing import Optional, Tuple
from Crypto.Cipher import AES
from core.crypto.models import SymmetricCiphertext

def generate_symmetric_key() -> bytes:
    """Generate a cryptographically secure random 256-bit (32 bytes) key for AES-256-GCM."""
    return os.urandom(32)

def encrypt_aes_gcm(
    key: bytes,
    plaintext: bytes,
    associated_data: Optional[bytes] = None,
    nonce: Optional[bytes] = None
) -> SymmetricCiphertext:
    """
    Encrypt plaintext using AES-256-GCM (NIST SP 800-38D).
    Returns nonce (12 bytes), ciphertext, and 16-byte authentication tag.
    """
    if len(key) != 32:
        raise ValueError(f"AES-256 key must be exactly 32 bytes, got {len(key)}")
    
    if nonce is None:
        nonce = os.urandom(12)  # Standard 96-bit unique nonce for GCM
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
    Raises ValueError if authentication fails or tag is invalid.
    """
    if len(key) != 32:
        raise ValueError(f"AES-256 key must be exactly 32 bytes, got {len(key)}")
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=encrypted.nonce)
    if encrypted.associated_data:
        cipher.update(encrypted.associated_data)
    
    return cipher.decrypt_and_verify(encrypted.ciphertext, encrypted.tag)

def wrap_key_aes_kw(
    wrapping_key: bytes,
    key_to_wrap: bytes,
    associated_data: Optional[bytes] = b"SIH26237-KEY-WRAP-AUTH"
) -> bytes:
    """
    Wrap a 256-bit document key using AES-GCM with the derived wrapping key.
    Packs: nonce (12 bytes) || tag (16 bytes) || ciphertext (32 bytes). Total: 60 bytes.
    """
    if len(key_to_wrap) != 32:
        raise ValueError(f"Key to wrap must be 32 bytes (256-bit), got {len(key_to_wrap)}")
    encrypted = encrypt_aes_gcm(wrapping_key, key_to_wrap, associated_data=associated_data)
    return encrypted.nonce + encrypted.tag + encrypted.ciphertext

def unwrap_key_aes_kw(
    wrapping_key: bytes,
    wrapped_payload: bytes,
    associated_data: Optional[bytes] = b"SIH26237-KEY-WRAP-AUTH"
) -> bytes:
    """
    Unwrap a 256-bit document key.
    Validates payload integrity and checks the 16-byte authentication tag.
    """
    if len(wrapped_payload) < 28:
        raise ValueError("Wrapped payload is too short (< 28 bytes)")
    nonce = wrapped_payload[:12]
    tag = wrapped_payload[12:28]
    ciphertext = wrapped_payload[28:]
    encrypted = SymmetricCiphertext(
        nonce=nonce,
        tag=tag,
        ciphertext=ciphertext,
        associated_data=associated_data
    )
    return decrypt_aes_gcm(wrapping_key, encrypted)
