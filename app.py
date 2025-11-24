from flask import Flask, render_template, request, flash, send_from_directory
import os
import uuid  # For unique filenames
import cv2  # ✅ Added to get video info
from steg.embed import embed_video
from steg.extract import extract_video

app = Flask(__name__)
app.secret_key = "your-secret-key"
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/encode', methods=['POST'])
def encode():
    if 'video' not in request.files:
        flash("No video uploaded")
        return render_template("index.html")
    video = request.files['video']
    if not video.filename:
        flash("No file selected")
        return render_template("index.html")
    message = request.form.get('message', '').strip()
    password = request.form.get('password', '')
    if not message or not password:
        flash("Message and password are required")
        return render_template("index.html")
    # Save uploaded video
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    video.save(input_path)
    # ✅ Extract video information
    cap = cv2.VideoCapture(input_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    total_capacity_bits = frame_count * width * height * 3
    total_capacity_bytes = total_capacity_bits // 8
    used_bytes = len(message.encode('utf-8'))
    remaining_bytes = total_capacity_bytes - used_bytes
    max_chars = total_capacity_bytes // 2
    remaining_chars = max_chars - len(message)
    # UNIQUE OUTPUT FILENAME
    unique_id = uuid.uuid4().hex[:8]
    output_filename = f"stego_{unique_id}.avi"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    try:
        final_path = embed_video(input_path, output_path, message, password)
        flash("Encoded successfully!")
        return render_template(
            "index.html",
            download_link=final_path.replace('\\', '/'),
            stego_filename=output_filename,
            frame_count=frame_count,
            resolution=f"{width} × {height}",
            total_capacity=f"{total_capacity_bytes / 1024:.2f} KB",
            used=f"{used_bytes} bytes",
            remaining=f"{remaining_bytes / 1024:.2f} KB",
            max_chars=max_chars,
            remaining_chars=remaining_chars
        )
    except Exception as e:
        flash(f"Error: {str(e)}")
        return render_template("index.html")
@app.route('/decode', methods=['POST'])
def decode():
    if 'video' not in request.files:
        flash("No video uploaded")
        return render_template("index.html")
    video = request.files['video']
    if not video.filename.lower().endswith(('.avi', '.mkv')):
        flash("Please upload the encoded .avi or .mkv file only!")
        return render_template("index.html")
    password = request.form.get('password', '')
    if not password:
        flash("Password required")
        return render_template("index.html")
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    video.save(input_path)
    try:
        message = extract_video(input_path, password)
        # PRINT TO TERMINAL
        print("\n" + "="*70)
        print("DECODED MESSAGE (TERMINAL OUTPUT):")
        print("="*70)
        print(message)
        print("="*70 + "\n")
        flash("Message decoded successfully!")
        return render_template("index.html", decoded_message=message)
    except Exception as e:
        error_msg = f"Decoding failed: {str(e)}"
        print(f"\nERROR: {error_msg}\n")
        flash(error_msg)
        return render_template("index.html")
if __name__ == '__main__':
    app.run(debug=True)