from flask import Flask, render_template, request, jsonify, g
from google.cloud import vision
import os
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['DATABASE'] = 'thai_id_ocr.db'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'your-google-credentials.json'

# Initialize Google Vision API client
client = vision.ImageAnnotatorClient()

# Database initialization
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_ocr', methods=['POST'])
def process_ocr():
    try:
        image = request.files['image']

        # Check if the file size is within limits
        if image.content_length > 2 * 1024 * 1024:
            return jsonify({'error': 'File size exceeds 2MB'})

        content = image.read()
        image = vision.Image(content=content)

        response = client.text_detection(image=image)
        texts = response.text_annotations

        # Extract relevant data from the OCR result
        data = parse_ocr_result(texts)

        # Save OCR data to the database
        status = save_ocr_data(data)

        return jsonify({'status': status, 'data': data})

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_ocr_data', methods=['GET'])
def get_ocr_data():
    try:
        # Retrieve OCR data from the database
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM thai_id_data')
            rows = cursor.fetchall()

        # Convert data to a list of dictionaries
        data = [{'name': row[0], 'last_name': row[1], 'id_number': row[2],
                 'dob': row[3], 'issue_date': row[4], 'expiry_date': row[5], 'timestamp': row[6], 'status': row[7]} for row in rows]

        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)})

def parse_ocr_result(texts):
    # Implement your logic to parse OCR results
    # Extract relevant information such as id number, name, last name, date of birth, date of issue, and date of expiry
    # Return a dictionary with the extracted data

def save_ocr_data(data):
    # Save OCR data to the database
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                'INSERT INTO thai_id_data (name, last_name, id_number, dob, issue_date, expiry_date, timestamp, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (data['name'], data['last_name'], data['id_number'], data['dob'], data['issue_date'], data['expiry_date'], timestamp, 'success'))
            conn.commit()

        return 'success'

    except Exception as e:
        return 'failure'

if __name__ == '__main__':
    app.run(debug=True)
