from flask import Flask, jsonify, request
import os
import psutil

app = Flask(__name__)

@app.route('/')
def home():
    # Dashboard ko main page par serve karne ke liye
    return "Enterprise Agent API Active"

@app.route('/api/status', methods=['GET'])
def get_status():
    # Dashboard ke liye real-time data
    return jsonify({
        "status": "online",
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "version": "2.0.0"
    })

@app.route('/api/execute', methods=['POST'])
def execute():
    # Yahan se aap commands fire kar sakte ho
    data = request.json
    command = data.get("command", "")
    return jsonify({"result": f"Executing: {command}", "status": "success"})

if __name__ == '__main__':
    app.run()