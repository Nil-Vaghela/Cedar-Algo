from flask import Flask, request, jsonify, flash, redirect, url_for, render_template
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret123'
EXCEL_FILE_trading = 'trading_data.xlsx'
EXCEL_FILE_Users = "UserData.xlsx"

def save_to_excel(data, sheet_name,FileName):
    # Check if the file exists
    try:
        # Try to read existing data
        old_data = pd.read_excel(FileName, sheet_name=sheet_name, engine='openpyxl')
        new_data = pd.concat([old_data, data], ignore_index=True)
    except (FileNotFoundError, ValueError):
        # If the file or sheet doesn't exist, use new data
        new_data = data

    # Write the combined data back to the Excel file
    with pd.ExcelWriter(FileName, engine='openpyxl', mode='w') as writer:
        new_data.to_excel(writer, sheet_name=sheet_name, index=False)

def read_from_excel(sheet_name,FileName):
    try:
        df = pd.read_excel(FileName, sheet_name=sheet_name, engine='openpyxl')
        return df
    except (FileNotFoundError, ValueError) as e:
        print(f"Error reading sheet: {e}")
        return pd.DataFrame()

@app.route('/api/trading_signal', methods=['POST'])
def add_trading_signal():
    data = request.json
    df = pd.DataFrame([{
        'Name': data['name'],
        'Buy': data['buy'],
        'Target': data['target'],
        'Stop Loss': data['sl'],
        'Status': data['Status'],
        'Index Name': data['indexName'],
        'Index Token': data['IndexToken'],
        'Created At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }])
    save_to_excel(df, 'Trading Signals',EXCEL_FILE_trading)
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'message': 'Trading signal added to Excel'}), 201
    else:
        flash('Trading signal added successfully!', 'success')
        return redirect(url_for('home'))

@app.route('/api/user', methods=['POST'])
def add_user():
    data = request.form
    df = pd.DataFrame([{
        'Username': data.get('username'),
        'Email': data.get('email'),
        'Created At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }])
    save_to_excel(df, 'Users',EXCEL_FILE_Users)
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'message': 'User added to Excel'}), 201
    else:
        flash('User added successfully!', 'success')
        return redirect(url_for('home'))

@app.route('/api/trading_signals', methods=['GET'])
def get_trading_signals():
    df = read_from_excel('Trading Signals',EXCEL_FILE_trading)
    return jsonify(df.to_dict(orient='records')), 200

@app.route('/api/users', methods=['GET'])
def get_users():
    df = read_from_excel('Users',EXCEL_FILE_Users)
    return jsonify(df.to_dict(orient='records')), 200

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
