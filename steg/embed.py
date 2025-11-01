# steg/embed.py
import cv2
import os
import subprocess
from .crypto_utils import encrypt_message
from .bit_utils import bytes_to_bits, embed_bits_into_frame
from .header_utils import build_header
from . import config

def embed_video(input_path, output_base, message, password):
    message += "<<<END>>>"

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError("Cannot open input video.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Encrypt
    salt, nonce, ciphertext = encrypt_message(message, password)
    header = build_header(salt, nonce, len(ciphertext))
    header = header.ljust(config.HEADER_SIZE, b'\x00')
    payload = header + ciphertext

    total_bits = len(payload) * 8
    capacity = width * height * 3 * frame_count
    if total_bits > capacity:
        raise ValueError("Message too large for video")

    bits_list = list(bytes_to_bits(payload))
    bit_iter = iter(bits_list)

    # Write lossless video
    temp_avi = output_base.replace('.avi', '_temp.avi')
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')
    out = cv2.VideoWriter(temp_avi, fourcc, fps, (width, height))
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
        os.remove(temp_avi)
        raise ValueError("Ran out of frames")

    # Final AVI with audio
    final_avi = output_base.replace('.avi', '_with_audio.avi')
    cmd = [
        'ffmpeg', '-y',
        '-i', temp_avi,
        '-i', input_path,
        '-c:v', 'copy', '-c:a', 'copy',
        '-map', '0:v:0', '-map', '1:a:0?',
        '-shortest', final_avi
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    os.remove(temp_avi)

    # Optional: Lossless MP4
    mp4_path = final_avi.replace('.avi', '.mp4')
    subprocess.run([
        'ffmpeg', '-i', final_avi,
        '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '0',
        '-c:a', 'copy', mp4_path
    ], check=True, capture_output=True)

    print(f"Final: {final_avi}")
    return final_avi, mp4_path