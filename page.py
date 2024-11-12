from threading import Thread
import base64
from time import perf_counter_ns
from typing import Literal
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    Request
)
from flask.wrappers import Response
from werkzeug import Response
from werkzeug.utils import secure_filename
import os
import convert2, epaper

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
PIC_FOLDER = "pic"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PIC_FOLDER"] = PIC_FOLDER
folder = ""
app.config['MAX_CONTENT_LENGTH'] = 510 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowedFile(filename) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def uploadFile() -> Response | str:
    if request.method == "POST":
        file = request.files["file"]
        if file and allowedFile(file.filename):
            filename = secure_filename(file.filename)  # type: ignore
            global folder
            folder = "UPLOAD_FOLDER"
            filepath = os.path.join(app.config[folder], filename)
            file.save(filepath)
            return redirect(url_for("uploadedFile", filename=filename))
    return render_template("upload.html")


@app.route("/uploads/<filename>")
def uploadedFile(filename) -> str:
    return render_template("uploaded_file.html", filename=filename)


@app.route("/display/<filename>")
def display_image(filename) -> Response:
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def convertImage(filepath) -> str:
    # Save converted image
    startTime = perf_counter_ns()
    convName, img = convert2.convertOptimized(filepath)
    totTime = (perf_counter_ns() - startTime) / 1000000
    print(totTime, "ms")
    convPath = os.path.join(app.config["PIC_FOLDER"], convName)

    def setEpaper():
        epaper.setPic(img)

    thread = Thread(target=setEpaper)
    thread.start()
    return convName

def save_cropped_image(data_url, filename):
    # Decode the base64 image data
    header, encoded = data_url.split(',', 1)
    binary_data = base64.b64decode(encoded)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(filepath)
    # Save the cropped image to a file
    with open(filepath, 'wb') as f:
        f.write(binary_data)
    return filepath

@app.route('/convert/<filename>', methods=['POST'])
def convert(filename):
    print(filename,  "2")
    cropped_image_data = request.form.get('cropped_image_data')
    
    if cropped_image_data:
        # Save the cropped image
        cropped_filename = f"cropped_{filename}"
        save_cropped_image(cropped_image_data, cropped_filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], cropped_filename)
        print(filepath,  "1")
        convertImage(filepath)
        # Redirect to a new page showing the cropped and converted image
        return redirect(url_for('show_converted', filename=cropped_filename))

    return "Error: No image data received", 400


@app.route("/pic/<filename>")
def show_converted(filename):
    return render_template("converted_file.html", filename=filename)


if __name__ == "__main__":
    from werkzeug import Request
    Request.max_form_parts = 50000
    app.run(host="0.0.0.0", port=80, debug=False)
