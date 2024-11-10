from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# Helper function to save JSON data
def save_json(file_name, data):
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return {'message': 'File saved successfully!'}
    except Exception as e:
        return {'message': f'Error saving file: {str(e)}'}

# Helper function to load JSON data
def load_json(file_name):
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data
        except Exception as e:
            return {'message': f'Error loading file: {str(e)}'}, 500
    else:
        return {'message': 'File not found'}, 404

# Endpoint to save JSON data (shared by both Response Changer and Product Manager)
@app.route('/save', methods=['POST'])
def save_file():
    data = request.json
    if not data:
        return jsonify({'message': 'No data received'}), 400

    file_name = data.get('fileName')
    content = data.get('data')

    if not file_name or not content:
        return jsonify({'message': 'Invalid data format'}), 400

    result = save_json(file_name, content)
    return jsonify(result)

# Endpoint to load JSON data (shared by both managers)
@app.route('/load', methods=['GET'])
def load_file():
    file_name = request.args.get('fileName')
    if not file_name:
        return jsonify({'message': 'File name is required'}), 400

    data = load_json(file_name)
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=5300, debug=True)
