"""
Cotton leaf pest and disease detection - web application.

Run locally in VS Code:
    1. pip install -r requirements.txt
    2. python app.py
    3. open http://127.0.0.1:5000 in a browser

The /prediction route loads the trained model once at start-up and returns
a real prediction. The original repo returned a fixed placeholder string
and never loaded a model.
"""
import json
import os
import time
from datetime import datetime

import requests

import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from tensorflow.keras.utils import img_to_array, load_img

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
IMG_SIZE = 224                       # must match the size used in training
MODEL_PATH = os.path.join("models", "cotton_model.keras")
LABELS_PATH = os.path.join("models", "class_names.json")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = tf.keras.models.load_model(MODEL_PATH)
class_names = json.load(open(LABELS_PATH))
TREATMENT = json.load(open("treatment.json"))

if int(model.output_shape[-1]) != len(class_names):
    raise ValueError("Model outputs do not match the number of labels.")
print("Model loaded from %s. Classes: %s" % (MODEL_PATH, class_names))


def allowed_file(filename):
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def prepare(path):
    """Resize and scale exactly as in training. A mismatch ruins accuracy."""
    img = load_img(path, target_size=(IMG_SIZE, IMG_SIZE))
    return np.expand_dims(img_to_array(img) / 255.0, axis=0)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/aboutapp")
def aboutapp():
    return render_template("aboutapp.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")



@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    if request.method == "GET":
        return render_template("prediction.html")

    upload = (request.files.get("file")
              or request.files.get("image")
              or next(iter(request.files.values()), None))

    if upload is None or upload.filename == "" or not allowed_file(upload.filename):
        return render_template("prediction.html"), 400

    filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + \
        os.path.basename(upload.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    upload.save(path)

    probs = model.predict(prepare(path), verbose=0)[0]
    index = int(np.argmax(probs))
    label = class_names[index]
    confidence = float(probs[index])

    cure = TREATMENT.get(label, "")
    if confidence < 0.60:
        cure = ("Confidence %.1f percent, below the 60 percent threshold, so "
                "confirm by inspection. " % (confidence * 100)) + cure

    return render_template("result.html",
                           filename=filename,
                           prediction=label,
                           Cure=cure)


# The ESP32 writes its readings to this path every 15 seconds.
FIREBASE_URL = ("https://cropify-9980a-default-rtdb.asia-southeast1"
                ".firebasedatabase.app/sensors.json")

# Used to spot a node that has stopped uploading. The board reports its own
# uptime, so if that figure stops advancing between polls the board is silent.
_last_uptime = {"value": None, "seen_at": 0.0}


@app.route("/data")
def data():
    """
    Live sensor readings, fetched from Firebase.

    Firebase holds only the most recent reading, because the board sends a PUT
    rather than an append. If the board goes offline that last value stays in
    the database indefinitely, which would show as live data on the dashboard.
    The stale_for figure below guards against that.
    """
    try:
        response = requests.get(FIREBASE_URL, timeout=5)
        response.raise_for_status()
        reading = response.json() or {}
    except Exception as exc:                       # noqa: BLE001
        return jsonify(ok=False, error=str(exc))

    if not reading:
        return jsonify(ok=False, error="No readings in the database yet")

    now = time.time()
    uptime = reading.get("uptime_s")
    if uptime != _last_uptime["value"]:
        _last_uptime["value"] = uptime
        _last_uptime["seen_at"] = now
    stale_for = int(now - _last_uptime["seen_at"])

    return jsonify(
        ok=True,
        temperature=reading.get("temperature"),
        humidity=reading.get("humidity"),
        soil_moisture=reading.get("soil_moisture"),
        soil_raw=reading.get("soil_raw"),
        uptime_s=uptime,
        stale_for=stale_for,
    )


@app.route("/health")
def health():
    return jsonify(model_loaded=True,
                   model_path=MODEL_PATH,
                   img_size=IMG_SIZE,
                   classes=class_names,
                   parameters=int(model.count_params()))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
