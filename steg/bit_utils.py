# steg/bit_utils.py
import numpy as np
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

def embed_bits_into_frame(frame: np.ndarray, bit_iter: Iterator[int]) -> tuple[np.ndarray, bool]:
    """
    Embed bits from bit_iter into this frame's LSBs.
    Returns (new_frame, done_flag)
    where done_flag=True if all bits have been embedded.
    """
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
            flat[pixel_idx, channel] = (flat[pixel_idx, channel] & ~1) | bit
            idx += 1
    except StopIteration:
        done = True  # all bits were written

    new_frame = flat.reshape(frame.shape)
    return new_frame, done



def extract_bits_from_frame(frame: np.ndarray, num_bits: int) -> List[int]:
    """
    Extract up to num_bits bits from the frame's LSBs in the same order used by embed_bits_into_frame.
    Returns a list of bits (0/1). If num_bits is larger than frame capacity, returns as many as available.
    """
    if frame is None:
        return []

    flat = frame.reshape(-1, frame.shape[2])
    total_slots = flat.size
    bits = []
    # iterate scalar-wise
    for scalar_index in range(min(num_bits, total_slots)):
        pixel_idx = scalar_index // frame.shape[2]
        channel = scalar_index % frame.shape[2]
        val = int(flat[pixel_idx, channel])
        bits.append(val & 1)
    return bits
