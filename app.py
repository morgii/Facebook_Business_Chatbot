from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS to allow front-end requests

# Endpoint to save the JSON file
@app.route('/save', methods=['POST'])
def save_file():
    data = request.json
    if not data:
        return jsonify({'message': 'No data received'}), 400

    file_name = data.get('fileName')
    responses = data.get('data')

    if not file_name or not responses:
        return jsonify({'message': 'Invalid data format'}), 400

    try:
        # Save the file in the current directory
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(responses, file, ensure_ascii=False, indent=2)
        return jsonify({'message': 'File saved successfully!'})
    except Exception as e:
        return jsonify({'message': f'Error saving file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(port=5300, debug=True)

#python -m http.server 8000
