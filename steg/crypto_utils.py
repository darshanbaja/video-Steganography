import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from . import config



def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=config.PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode())

def encrypt_message(message: str, password: str):
    salt = os.urandom(config.SALT_SIZE)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(config.NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, message.encode(), None)
    return salt, nonce, ciphertext

def decrypt_message(password: str, salt: bytes, nonce: bytes, ciphertext: bytes) -> str:
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()
