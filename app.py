# app.py
from flask import Flask, render_template, request, flash, send_from_directory
import os
from steg.embed import embed_video
from steg.extract import extract_video

app = Flask(__name__)
app.secret_key = "your-secret-key"
app.config['UPLOAD_FOLDER'] = 'uploads'

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

    message = request.form.get('message', '')
    password = request.form.get('password', '')

    if not message or not password:
        flash("Message and password required")
        return render_template("index.html")

    input_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    video.save(input_path)

    output_base = os.path.join(app.config['UPLOAD_FOLDER'], 'encoded_output.avi')

    try:
        avi_path, mp4_path = embed_video(input_path, output_base, message, password)
        flash("Message encoded successfully!")
        return render_template(
            "index.html",
            avi_download=avi_path.replace('\\', '/'),
            mp4_download=mp4_path.replace('\\', '/')
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
    password = request.form.get('password', '')

    if not video.filename or not password:
        flash("Video and password required")
        return render_template("index.html")

    input_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    video.save(input_path)

    try:
        message = extract_video(input_path, password)
        flash("Message decoded!")
        return render_template("index.html", decoded_message=message)
    except Exception as e:
        flash(f"Error: {str(e)}")
        return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)