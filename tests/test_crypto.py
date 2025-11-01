from steg.crypto_utils import encrypt_message, decrypt_message

message = "Test AES encryption"
password = "strongpass123"

cipher = encrypt_message(message, password)
print("Encrypted:", cipher)

plain = decrypt_message(cipher, password)
print("Decrypted:", plain)
