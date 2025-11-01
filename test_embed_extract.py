from steg.embed import embed_video
from steg.extract import extract_video

input_video = "uploads/input_video.avi"
output_video = "uploads/output_stego.avi"

message = "Hello from the hidden world!"
password = "mypassword123"

embed_video(input_video, output_video, message, password)
print("✅ Encoding done")

decoded = extract_video(output_video, password)
print("✅ Decoded message:", decoded)



embed.py
import cv2
import numpy as np
from .crypto_utils import encrypt_message
from .bit_utils import bytes_to_bits, embed_bits_into_frame
from .header_utils import build_header
from . import config
import os
import subprocess


def embed_video(input_path, output_path, message, password):
    message += "<<<END>>>"

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError("Cannot open input video.")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    salt, nonce, ciphertext = encrypt_message(message, password)
    header = build_header(salt, nonce, len(ciphertext))
    payload = header + ciphertext
    total_bits = len(payload) * 8
    capacity_bits = frame_count * height * width * 3 * config.BITS_PER_CHANNEL

    if total_bits > capacity_bits:
        raise ValueError("Message too large for this video.")

    bit_iter = bytes_to_bits(payload)

    # Step 1 — create silent AVI with hidden message
    temp_silent_video = os.path.splitext(output_path)[0] + "_noaudio.avi"
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(temp_silent_video, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = embed_bits_into_frame(frame, bit_iter)
        out.write(frame)

    cap.release()
    out.release()

    # 🔊 Step 2 — merge original audio losslessly (do NOT touch video pixels)
    final_output = output_path  # overwrite user path
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", temp_silent_video,       # video with hidden message
            "-i", input_path,              # original video with audio
            "-c:v", "copy",                # keep video untouched
            "-c:a", "copy",                # copy audio directly
            "-map", "0:v:0",               # video from first input
            "-map", "1:a:0?",              # audio from original input (optional)
            "-shortest",                    # stop at shortest stream
            final_output
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ Encoded video now includes original audio (lossless).")
    except subprocess.CalledProcessError as e:
        print("⚠️ Audio merge failed, using silent video:", e)
        # fallback
        os.replace(temp_silent_video, final_output)
    finally:
        if os.path.exists(temp_silent_video):
            os.remove(temp_silent_video)

    return final_output


