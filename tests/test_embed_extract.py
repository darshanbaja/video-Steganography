from steg.embed import embed_video
from steg.extract import extract_message

input_video = "uploads/input_video.avi"
output_video = "uploads/output_stego.avi"
message = "Hello from the hidden world!"
password = "secure123"

embed_video(input_video, output_video, message, password)
print("✅ Encoding done")

decoded = extract_message(output_video, password)
print("✅ Decoded message:", decoded)
