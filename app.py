import base64
from threading import Thread
from time import perf_counter_ns
from typing import Literal
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from flask.wrappers import Response
from werkzeug.utils import secure_filename
import subprocess
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
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file() -> tuple[Response, Literal[400]] | tuple[Response, Literal[200]]:
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename) # type: ignore
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

def convertImage(filepath)  -> None:
    # Save converted image
    startTime = perf_counter_ns()
    convName, img = convert2.convertOptimized(filepath)
    totTime = (perf_counter_ns() - startTime) / 1000000
    print(totTime, "ms")

    #def setEpaper() -> None:
    epaper.setPic(img)

    #thread = Thread(target=setEpaper)
    #thread.start()

@app.route('/converted', methods=['POST'])
def convert():  
    file = request.form.get('cropped_image_data')

    if file:
        filename = secure_filename("cropped")
        file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename + ".jpg")
        save_cropped_image(file, file_path)
        convertImage(file_path)
        return render_template("done.html")
    
    return jsonify({'error': 'Invalid file format '}), 400

@app.route('/done', methods=['GET'] )
def image_set_done():
    return render_template("done.html")

@app.route('/uploads/<filename>')
def get_uploaded_file(filename) -> Response:
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/shutdown', methods=['GET'])
def shutdown() -> tuple[Response, Literal[200]]:  
    command = "sudo shutdown now -h"
    subprocess.call(command.split())
    return jsonify({'Shutting down'}), 200


if __name__ == '__main__':
    from werkzeug import Request
    Request.max_form_parts = 50000
    app.run(host="0.0.0.0", port=443, debug=False, ssl_context=('cert.pem', 'key.pem'))
