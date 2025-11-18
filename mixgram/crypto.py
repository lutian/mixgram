
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets

def encrypt_aes_gcm(key: bytes, plaintext: bytes, associated_data: bytes = b'') -> bytes:
    aes = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aes.encrypt(nonce, plaintext, associated_data)
    return nonce + ct

def decrypt_aes_gcm(key: bytes, blob: bytes, associated_data: bytes = b'') -> bytes:
    aes = AESGCM(key)
    nonce = blob[:12]
    ct = blob[12:]
    return aes.decrypt(nonce, ct, associated_data)
