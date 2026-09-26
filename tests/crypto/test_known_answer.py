import pytest
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import generate_symmetric_key, encrypt_aes_gcm, decrypt_aes_gcm

def test_fips203_known_dimensions():
    """
    NIST FIPS 203 ML-KEM-768 parameter invariants:
    - k = 3
    - eta_1 = 2, eta_2 = 2
    - d_u = 10, d_v = 4
    - Public key length: 1184 bytes
    - Secret key length: 2400 bytes
    - Ciphertext length: 1088 bytes
    - Shared secret length: 32 bytes (256-bit)
    """
    kp = MLKEM768.generate_keypair()
    assert len(kp.public_key_bytes) == 1184
    assert len(kp.private_key_bytes) == 2400

    enc = MLKEM768.encapsulate(kp.public_key_bytes)
    assert len(enc.ciphertext) == 1088
    assert len(enc.shared_secret) == 32

    ss = MLKEM768.decapsulate(kp.private_key_bytes, enc.ciphertext)
    assert ss == enc.shared_secret

def test_fips204_known_dimensions():
    """
    NIST FIPS 204 ML-DSA-65 parameter invariants:
    - (k, l) = (6, 5)
    - eta = 4, tau = 49, beta = 196, gamma_1 = 2^19, gamma_2 = (q-1)/32
    - Public key length: 1952 bytes
    - Secret key length: 4000 bytes
    - Signature length: 3293 bytes
    """
    kp = MLDSA65.generate_keypair()
    assert len(kp.public_key_bytes) == 1952
    assert len(kp.private_key_bytes) == 4000

    sig = MLDSA65.sign(kp.private_key_bytes, b"FIPS 204 KAT Test Vector Payload")
    assert len(sig) == 3293

    assert MLDSA65.verify(kp.public_key_bytes, b"FIPS 204 KAT Test Vector Payload", sig) is True

def test_nist_sp800_38d_aes_gcm_dimensions():
    """
    NIST SP 800-38D AES-GCM invariants:
    - Key size: 256 bits (32 bytes)
    - Nonce size: 96 bits (12 bytes)
    - Tag size: 128 bits (16 bytes)
    """
    key = generate_symmetric_key()
    assert len(key) == 32
    
    enc = encrypt_aes_gcm(key, b"Known plaintext for GCM")
    assert len(enc.nonce) == 12
    assert len(enc.tag) == 16
    assert decrypt_aes_gcm(key, enc) == b"Known plaintext for GCM"
