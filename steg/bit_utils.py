# steg/bit_utils.py
import numpy as np
import sys
from typing import Iterable, Iterator, List

def bytes_to_bits(b: bytes) -> Iterator[int]:
    """
    Convert bytes -> sequence of bits (MSB first per byte).
    Example: b'\xA5' -> [1,0,1,0,0,1,0,1]
    """
    for byte in b:
        for i in range(7, -1, -1):
            yield (byte >> i) & 1

def bits_to_bytes(bits: Iterable[int]) -> bytes:
    """
    Convert iterable of bits (MSB first per byte) -> bytes.
    Accepts bits length not multiple of 8 (pads with zeros on the right).
    """
    out = bytearray()
    acc = 0
    count = 0
    for bit in bits:
        acc = (acc << 1) | (1 if bit else 0)
        count += 1
        if count == 8:
            out.append(acc)
            acc = 0
            count = 0
    if count > 0:
        acc = acc << (8 - count)
        out.append(acc)
    return bytes(out)

# steg/bit_utils.py
def embed_bits_into_frame(frame: np.ndarray, bit_iter: Iterator[int]) -> tuple[np.ndarray, bool]:
    if frame is None:
        return frame, True

    h, w, c = frame.shape
    flat = frame.reshape(-1, c).copy()
    total_slots = flat.size
    done = False
    idx = 0

    try:
        while idx < total_slots:
            bit = next(bit_iter)
            pixel_idx = idx // c
            channel = idx % c

            # FIX: Clamp to 0-255 and use int
            val = int(flat[pixel_idx, channel])
            val = max(0, min(255, val))  # Clamp
            new_val = (val & ~1) | bit
            flat[pixel_idx, channel] = new_val

            idx += 1
    except StopIteration:
        done = True

    new_frame = flat.reshape(h, w, c)
    return new_frame, done



def extract_bits_from_frame(frame: np.ndarray, max_bits: int = sys.maxsize) -> List[int]:
    if frame is None:
        return []
    flat = frame.reshape(-1, frame.shape[2])
    total = min(max_bits, flat.size)  # Now safe
    bits = []
    for i in range(total):
        pixel_idx = i // 3
        channel = i % 3
        val = int(flat[pixel_idx, channel])
        val = max(0, min(255, val))
        bits.append(val & 1)
    return bits
