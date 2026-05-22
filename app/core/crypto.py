import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.conf.app_config import conf

_NONCE_SIZE = 12


def _get_key() -> bytes:
    key_b64 = conf.crypto.aes_key
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise ValueError("AES key must be 32 bytes (256-bit)")
    return key


def encrypt(plaintext: str) -> str:
    key = _get_key()
    nonce = os.urandom(_NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt(encrypted: str) -> str:
    key = _get_key()
    raw = base64.b64decode(encrypted)
    nonce = raw[:_NONCE_SIZE]
    ciphertext = raw[_NONCE_SIZE:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def generate_key() -> str:
    key = AESGCM.generate_key(bit_length=256)
    return base64.b64encode(key).decode("utf-8")
