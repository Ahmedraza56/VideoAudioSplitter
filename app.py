from flask import Flask, render_template, request, send_file
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
from io import BytesIO
from flask import send_from_directory


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Ensure that the required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def process_video():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return render_template('index.html', error='No file part')

    file = request.files['file']

    # If the user does not select a file, the browser submits an empty file without a filename.
    if file.filename == '':
        return render_template('index.html', error='No selected file')

    # Save the uploaded file to disk
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_video.mp4')
    file.save(video_path)

    video = VideoFileClip(video_path)

    # Extract audio from the video
    audio = video.audio
    audio_filename = os.path.join(app.config['OUTPUT_FOLDER'], "temp.wav")
    audio.write_audiofile(audio_filename)

    # Load audio using PyDub
    audio = AudioSegment.from_wav(audio_filename)

    # Split audio on silence
    chunks = split_on_silence(audio, min_silence_len=1000, silence_thresh=-40)

    # Combine chunks back into a single audio segment
    combined = AudioSegment.empty()
    for chunk in chunks:
        combined += chunk

    # Save combined audio
    combined_filename = os.path.join(app.config['OUTPUT_FOLDER'], "combined.wav")
    combined.export(combined_filename, format="wav")

    # Save the processed video without audio
    processed_filename = os.path.join(app.config['OUTPUT_FOLDER'], "processed_video.mp4")
    video.write_videofile(processed_filename, codec='libx264', audio=False)

    return render_template('index.html', audio=combined_filename, video=processed_filename)
# ... (your existing code)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)
# Add this route to remove the temporary audio file
@app.route('/remove_temp_audio')
def remove_temp_audio():
    temp_audio_filename = os.path.join(app.config['OUTPUT_FOLDER'], "temp.wav")
    if os.path.exists(temp_audio_filename):
        os.remove(temp_audio_filename)
    return "Temporary audio file removed"

if __name__ == '__main__':
    app.run(debug=True)

