from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import pandas as pd

app = Flask(__name__)
CORS(app)

# Define the directory where JSON files will be stored
DATA_DIRECTORY = os.path.join(os.getcwd(), 'data')

# Create the directory if it doesn't exist
if not os.path.exists(DATA_DIRECTORY):
    os.makedirs(DATA_DIRECTORY)

# Helper function to save JSON data
def save_json(file_name, data):
    file_path = os.path.join(DATA_DIRECTORY, file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return {'message': 'File saved successfully!'}
    except Exception as e:
        return {'message': f'Error saving file: {str(e)}'}

# Helper function to load JSON data
def load_json(file_name):
    file_path = os.path.join(DATA_DIRECTORY, file_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data
        except Exception as e:
            return {'message': f'Error loading file: {str(e)}'}, 500
    else:
        return {'message': 'File not found'}, 404

# Endpoint to save JSON data
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

# Endpoint to load JSON data
@app.route('/load', methods=['GET'])
def load_file():
    file_name = request.args.get('fileName')
    if not file_name:
        return jsonify({'message': 'File name is required'}), 400

    data = load_json(file_name)
    return jsonify(data)

# Endpoint to export data to Excel
@app.route('/export-excel', methods=['GET'])
def export_to_excel():
    file_name = request.args.get('fileName')
    if not file_name:
        return jsonify({'message': 'File name is required'}), 400

    data = load_json(file_name)
    if isinstance(data, tuple):  # Error response
        return jsonify(data[0]), data[1]

    try:
        # Flatten the JSON data for Excel export
        rows = []
        for order in data:
            for item in order.get('cart_items', []):
                row = {
                    'Invoice Number': order.get('invoice_number', ''),
                    'Customer Name': order.get('customer_name', ''),
                    'Phone Number': order.get('phone_number', ''),
                    'Order Date': order.get('order_date', ''),
                    'Order Status': order.get('order_status', ''),
                    'Payment Method': order.get('payment_method', ''),
                    'Item Title': item.get('title', ''),
                    'Item Price': item.get('price', ''),
                    'Total Price': order.get('total_price', '')
                }
                rows.append(row)

        # Create a DataFrame and save it as an Excel file
        df = pd.DataFrame(rows)
        excel_file = os.path.join(DATA_DIRECTORY, 'orders.xlsx')
        df.to_excel(excel_file, index=False)

        # Just return a success message without sending the file
        return jsonify({'message': 'Excel file saved on the server as orders.xlsx'})

    except Exception as e:
        return jsonify({'message': f'Error exporting to Excel: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(port=5300, debug=True)
