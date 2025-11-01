import cv2
from steg.bit_utils import extract_bits_from_frame

cap = cv2.VideoCapture("uploads/encoded_output (2).avi")
ret, frame = cap.read()
cap.release()

if not ret:
    print("❌ Cannot open encoded video")
else:
    bits = extract_bits_from_frame(frame, 64)
    print("✅ First 64 bits extracted:", bits[:32], "...")
