import os
import json
import subprocess
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Path to the JSON file storing database configurations
DB_CONFIG_FILE = 'db_config.json'

# Ensure the JSON file exists
if not os.path.exists(DB_CONFIG_FILE):
    with open(DB_CONFIG_FILE, 'w') as f:
        json.dump([], f)

# Load database configurations from file
def load_db_configs():
    with open(DB_CONFIG_FILE, 'r') as f:
        return json.load(f)

# Save database configurations to file
def save_db_configs(configs):
    with open(DB_CONFIG_FILE, 'w') as f:
        json.dump(configs, f, indent=4)

@app.route('/adddb', methods=['POST'])
def add_db():
    data = request.json
    db_type = data.get('type')
    container_name = data.get('container_name')
    db_name = data.get('db_name')  # Add db_name here
    username = data.get('username')
    password = data.get('password')

    if not all([db_type, container_name, db_name, username, password]):
        return jsonify({'error': 'Missing required fields'}), 400

    db_configs = load_db_configs()
    db_id = len(db_configs) + 1
    db_configs.append({
        'id': db_id,
        'type': db_type,
        'container_name': container_name,
        'db_name': db_name,  # Save db_name in the config
        'username': username,
        'password': password
    })
    save_db_configs(db_configs)

    return jsonify({'message': 'Database configuration added successfully', 'id': db_id}), 201

@app.route('/getdb', methods=['GET'])
def get_db():
    db_configs = load_db_configs()
    return jsonify(db_configs), 200

@app.route('/backup', methods=['POST'])
def backup_db():
    data = request.json
    db_id = data.get('id')

    if not db_id:
        return jsonify({'error': 'Missing database ID'}), 400

    db_configs = load_db_configs()
    db_config = next((db for db in db_configs if db['id'] == db_id), None)

    if not db_config:
        return jsonify({'error': 'Database configuration not found'}), 404

    db_type = db_config['type']
    container_name = db_config['container_name']
    db_name = db_config['db_name']  # Get db_name from config
    username = db_config['username']
    password = db_config['password']
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_file = f"backup_{db_type}_{db_id}_{timestamp}.sql"

    try:
        if db_type == 'mysql':
            command = [
                'docker', 'exec', container_name, 'mysqldump', '-u', username, f'-p{password}', db_name  # Use db_name here
            ]
        elif db_type == 'postgres':
            command = [
                'docker', 'exec', container_name, 'pg_dump', db_name, '-U', username  # Use db_name here
            ]
        else:
            return jsonify({'error': 'Unsupported database type'}), 400

        with open(backup_file, 'w') as f:
            subprocess.run(command, stdout=f, check=True)

        return jsonify({'message': 'Backup completed successfully', 'backup_file': backup_file}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Backup failed: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
