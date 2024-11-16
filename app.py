import base64
from threading import Thread
from time import perf_counter_ns
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename

import convert2
import epaper

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
CONVERTED_FOLDER = 'static/converted/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 510 * 1024 * 1024

# Ensure the uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({'filename': filename}), 200
    return jsonify({'error': 'File type not allowed'}), 400

def save_cropped_image(data_url, filepath):
    # Decode the base64 image data
    header, encoded = data_url.split(',', 1)
    binary_data = base64.b64decode(encoded)
    print(filepath)
    # Save the cropped image to a file
    with open(filepath, 'wb') as f:
        f.write(binary_data)
    return filepath

def convertImage(filepath) -> str:
    # Save converted image
    startTime = perf_counter_ns()
    convName, img = convert2.convertOptimized(filepath)
    totTime = (perf_counter_ns() - startTime) / 1000000
    print(totTime, "ms")

    def setEpaper():
        epaper.setPic(img)

    thread = Thread(target=setEpaper)
    thread.start()
    return convName

@app.route('/converted', methods=['POST'])
def convert():  
    file = request.form.get('cropped_image_data')

    if file:
        filename = secure_filename("cropped")
        file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename + ".jpg")
        save_cropped_image(file, file_path)
        convertImage(file_path)
        return jsonify({'filename': file_path}), 200
    
    return jsonify({'error': 'Invalid file format '}), 400


@app.route('/uploads/<filename>')
def get_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    from werkzeug import Request
    Request.max_form_parts = 50000
    app.run(host="0.0.0.0", port=8080, debug=False)
