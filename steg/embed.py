# steg/embed.py
import cv2
import os
import subprocess
from .crypto_utils import encrypt_message
from .bit_utils import bytes_to_bits, embed_bits_into_frame
from .header_utils import build_header
from . import config

def embed_video(input_path, output_path, message, password):
    message += "<<<END>>>"

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError("Cannot open input video.")

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # --- Encrypt & Payload ---
    salt, nonce, ciphertext = encrypt_message(message, password)
    header = build_header(salt, nonce, len(ciphertext))
    header = header.ljust(config.HEADER_SIZE, b'\x00')
    payload = header + ciphertext
    bit_iter = iter(list(bytes_to_bits(payload)))

    # --- Step 1: Write FFV1 video (lossless) ---
    temp_video = output_path.replace('.mkv', '_temp.avi')
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    if not out.isOpened():
        raise RuntimeError("FFV1 not supported. Install OpenCV with FFmpeg.")

    done = False
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if not done:
            frame, done = embed_bits_into_frame(frame, bit_iter)
            if done:
                print(f"Embedded at frame {frame_idx}")
        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    if not done:
        os.remove(temp_video)
        raise ValueError("Ran out of frames")

    # --- Step 2: Mux with audio → MKV (100% safe copy) ---
    final_mkv = output_path.replace('.avi', '.mkv')  # Use .mkv
    cmd = [
        'ffmpeg', '-y',
        '-i', temp_video,
        '-i', input_path,
        '-c:v', 'copy', '-c:a', 'copy',
        '-map', '0:v:0', '-map', '1:a:0?',
        '-fflags', '+genpts',
        final_mkv
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(temp_video)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    print(f"FINAL: {final_mkv} → PLAYABLE IN VLC + DECODABLE")
    return final_mkv