import struct

MAGIC = b"STEGOV1"

def build_header(salt, nonce, ciphertext_len):
    return MAGIC + struct.pack(">16s12sI", salt, nonce, ciphertext_len)

def parse_header(data):
    if not data.startswith(MAGIC):
        raise ValueError("Invalid magic header")

    header_size = len(MAGIC) + 16 + 12 + 4
    salt, nonce, clen = struct.unpack(">16s12sI", data[len(MAGIC):header_size])
    return salt, nonce, clen, header_size
