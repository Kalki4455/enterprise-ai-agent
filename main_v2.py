from flask import Flask, request, jsonify
# Galti se bhi hardcoded paths mat use karo, hamesha tmp use karo
import tempfile
import os

# AGAR FILE LIKHNI HAI:
# path = os.path.join(tempfile.gettempdir(), 'data.txt')
import os
import psutil
import json

app = Flask(__name__)

# --- ENTERPRISE AGENT CORE CONFIGURATION ---
class AgentEngine:
    def __init__(self):
        self.version = "2.0.0"
        self.workspace_root = os.getcwd()

    def get_system_telemetry(self):
        """Fetches real-time system metrics for the dashboard."""
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "ram_usage": psutil.virtual_memory().percent,
            "status": "online"
        }

# Initialize Engine
agent = AgentEngine()

# --- VERCEL/FLASK API HANDLERS ---

@app.route('/', methods=['GET'])
def index():
    """Default entry point for the Web Dashboard."""
    return jsonify({
        "message": "Enterprise Autonomous Agent Suite Active",
        "version": agent.version,
        "telemetry": agent.get_system_telemetry()
    })

@app.route('/api/execute', methods=['POST'])
def execute_task():
    """Internal API endpoint for agent task execution."""
    data = request.json
    task = data.get('task', 'no-task-provided')
    
    # Yahan apna main execution logic (sandbox/patcher) call karo
    response = {
        "status": "success",
        "executed_task": task,
        "output": "Task processed successfully in sandbox environment."
    }
    return jsonify(response)

# --- VERCEL REQUIRED HANDLER ---
# Vercel needs this 'app' instance to route requests correctly
if __name__ == '__main__':
    app.run(debug=True)