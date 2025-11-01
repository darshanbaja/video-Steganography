# steg/extract.py
import cv2
import struct
from .crypto_utils import decrypt_message
from .bit_utils import extract_bits_from_frame, bits_to_bytes
from . import config

MAGIC = b"STEGOV1"

def extract_video(input_path, password):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError("Cannot open video")

    bit_buffer = []

    def get_bits(n):
        nonlocal bit_buffer
        while len(bit_buffer) < n:
            ret, frame = cap.read()
            if not ret:
                raise ValueError("Ran out of frames")
            bit_buffer.extend(extract_bits_from_frame(frame, float('inf')))
        bits, bit_buffer = bit_buffer[:n], bit_buffer[n:]
        return bits

    # Extract header
    header_bits = get_bits(config.HEADER_SIZE * 8)
    header_bytes = bits_to_bytes(header_bits)

    magic = header_bytes[:7].rstrip(b"\x00")
    if magic != MAGIC:
        raise ValueError(f"Magic mismatch: {magic!r}")

    salt = header_bytes[7:23]
    nonce = header_bytes[23:35]
    clen = struct.unpack(">I", header_bytes[35:39])[0]

    # Extract ciphertext
    ciphertext = bits_to_bytes(get_bits(clen * 8))
    cap.release()

    plaintext = decrypt_message(password, salt, nonce, ciphertext)
    return plaintext.replace("<<<END>>>", "").strip()