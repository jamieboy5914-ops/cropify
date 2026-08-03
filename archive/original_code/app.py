from flask import Flask, request, jsonify, render_template,redirect,url_for
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = r'static\uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('home.html')
@app.route('/aboutapp')
def aboutapp():
    return render_template('aboutapp.html')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/prediction')
def Prediction():
    return jsonify('This logic is under development it will be functional once the API is tested')

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)