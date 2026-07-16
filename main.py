import json
import os
import time
import webbrowser
import subprocess
import difflib
import psutil
from datetime import datetime
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from openai import OpenAI
from workspace import WorkspaceManager
from sandbox import LocalSandboxManager

# Global states allocation
LIVE_LOGS = ["🚀 Enterprise System Active. Multi-checkpoint versioning & structural engine online."]
AGENT_STATUS = "System Ready - Monitoring Active Workspace"
METRICS = {"execution_time": "0.0s", "loops_run": 0, "security_score": "N/A", "cpu": "0%", "memory": "0%"}
HISTORY_FILE = "agent_history.json"
DIFF_BUFFER = ""
EXPLANATION_BUFFER = "Click 'Explain & Map Architecture 🧠' to parse active files workspace."
CHECKPOINT_REGISTRY = []

INITIAL_SNAPSHOT = {
    "models/user.py": "class User:\n    def __init__(self, name):\n        self.name = name\n",
    "services/auth.py": "from models.user import User\n\ndef register_user(username):\n    return User(username)\n",
    "tests/test_auth.py": "from services.auth import register_user\nimport pytest\n\ndef test_registration_valid():\n    u = register_user('Arjun')\n    assert u.name == 'Arjun'\n"
}

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump([], f)

def telemetry_daemon():
    while True:
        try:
            METRICS["cpu"] = f"{psutil.cpu_percent()}%"
            METRICS["memory"] = f"{psutil.virtual_memory().percent}%"
        except Exception: pass
        time.sleep(1)

Thread(target=telemetry_daemon, daemon=True).start()

# ----------------------------------------------------------------
# 1. Advanced Web IDE, UI Component, & Architecture Mapping Server
# ----------------------------------------------------------------
class LiveLogHandler(SimpleHTTPRequestHandler):
    def generate_interactive_tree(self, path):
        html = ""
        try:
            for item in os.listdir(path):
                if item.startswith('.') or item == "__pycache__": continue
                full_item_path = os.path.join(path, item)
                rel_path = os.path.relpath(full_item_path, workspace.base_dir).replace("\\", "/")
                if os.path.isdir(full_item_path):
                    html += f"<div style='margin-left:10px; font-weight:bold; color:#ffa657;'>📁 {item}</div>"
                    html += self.generate_interactive_tree(full_item_path)
                else:
                    html += f"""<div class='tree-file-node' onclick="loadFileToEditor('{rel_path}')" style='margin-left:20px; font-size:12px; color:#58a6ff; cursor:pointer; padding:2px;'>📄 {item}</div>"""
        except Exception: pass
        return html

    def do_GET(self):
        url_parts = urlparse(self.path)
        
        if url_parts.path == "/api/get-file":
            query = parse_qs(url_parts.query)
            file_rel_path = query.get('path', [''])[0]
            target_full_path = os.path.join(workspace.base_dir, file_rel_path)
            
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            content = ""
            if os.path.exists(target_full_path) and os.path.isfile(target_full_path):
                with open(target_full_path, "r", encoding="utf-8") as f: content = f.read()
            self.wfile.write(json.dumps({"content": content}).encode("utf-8"))
            return
        
        if url_parts.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            log_html = "".join([f"<div class='line'>{line}</div>" for line in LIVE_LOGS])
            
            checkpoint_html = "<h4>💾 Snapshot Rollback Matrix:</h4>"
            if not CHECKPOINT_REGISTRY:
                checkpoint_html += "<div style='font-size:11px; color:#8b949e;'>No rollback points.</div>"
            for cp in reversed(CHECKPOINT_REGISTRY):
                checkpoint_html += f"""<div style='font-size:11px; margin-bottom:6px; display:flex; justify-content:space-between;'>
                    <span>⏱️ {cp['time']}</span>
                    <a href='/restore-checkpoint?id={cp['id']}' style='color:#58a6ff; text-decoration:none; font-weight:bold;'>[Restore]</a>
                </div>"""

            response_data = {
                "status": AGENT_STATUS, "logs": log_html, "checkpoints": checkpoint_html,
                "tree": self.generate_interactive_tree(workspace.base_dir),
                "metrics": METRICS, "diff": DIFF_BUFFER, "explanation": EXPLANATION_BUFFER
            }
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        if url_parts.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Autonomous Web IDE Agent Control-Room</title>
                <style>
                    body {{ background: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin:0; padding:0; height:100vh; display:flex; flex-direction:column; }}
                    .top-bar {{ background: #161b22; border-bottom: 1px solid #30363d; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }}
                    .main-frame {{ display: flex; flex: 1; overflow: hidden; }}
                    .sidebar {{ width: 260px; background: #161b22; border-right: 1px solid #30363d; padding: 15px; overflow-y: auto; }}
                    .workspace-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; flex: 1; padding: 15px; overflow-y: auto; }}
                    .panel {{ background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 6px; display: flex; flex-direction: column; }}
                    .full-width {{ grid-column: 1 / -1; }}
                    textarea {{ width: 100%; box-sizing: border-box; height: 50px; background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; padding: 10px; border-radius: 6px; font-family: inherit; resize: none; margin-bottom: 8px; }}
                    .editor-textarea {{ width: 100%; height: 200px; background: #010409; color: #7ee787; border: 1px solid #30363d; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 13px; }}
                    input[type="text"] {{ width: 100%; box-sizing: border-box; background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; padding: 8px; border-radius: 6px; font-family: monospace; margin-bottom: 8px; }}
                    button {{ background: #238636; color: white; border: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; cursor: pointer; }}
                    .btn-danger {{ background: #da3637; margin-left: 8px; }}
                    .btn-info {{ background: #1f6feb; margin-left: 8px; }}
                    .console {{ background: #010409; border: 1px solid #30363d; padding: 12px; border-radius: 6px; height: 240px; overflow-y: auto; font-family: monospace; font-size: 12px; }}
                    .line {{ margin-bottom: 3px; color: #8b949e; white-space: pre-wrap; }}
                    .diff-added {{ background-color: rgba(46, 160, 67, 0.15); color: #7ee787; }}
                    .diff-removed {{ background-color: rgba(248, 81, 73, 0.15); color: #f85149; }}
                    .diff-file {{ font-weight: bold; color: #58a6ff; margin-top: 8px; border-bottom: 1px solid #30363d; }}
                    .metrics-row {{ display: flex; gap: 12px; font-size: 11px; }}
                    .metric-tag {{ background: #21262d; border: 1px solid #30363d; padding: 4px 8px; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div class="top-bar">
                    <div style="font-weight:bold; font-size:15px;">🤖 Enterprise Local Agent IDE Suite</div>
                    <div class="metrics-row">
                        <div class="metric-tag">💻 CPU: <span id="m-cpu">0%</span></div>
                        <div class="metric-tag">📟 RAM: <span id="m-mem">0%</span></div>
                        <div class="metric-tag">⏳ Speed: <span id="m-time">0.0s</span></div>
                        <div class="metric-tag">🔄 Loops: <span id="m-loops">0</span></div>
                        <div class="metric-tag">🛡️ Sandbox: <span id="m-safety">N/A</span></div>
                    </div>
                </div>
                
                <div class="main-frame">
                    <div class="sidebar">
                        <h4 style="margin-top:0; color:#58a6ff; font-size:12px;">📁 PROJECT Explorer</h4>
                        <div id="file-tree-root" style="margin-bottom:20px;">Scanning files...</div>
                        <hr style="border:0; border-top:1px solid #30363d; margin:15px 0;">
                        <div id="checkpoint-box">Loading checkpoints...</div>
                    </div>
                    
                    <div class="workspace-grid">
                        <div class="panel full-width">
                            <div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#8b949e;">Agent Status: <span id="status-text" style="color:#ffa657;">{AGENT_STATUS}</span></div>
                            <form action="/run-task" method="POST" style="display:flex; flex-direction:column;">
                                <textarea name="task" placeholder="Inject functional code feature specifications..." required></textarea>
                                <div style="display:flex; align-items:center; margin-top:5px;">
                                    <input type="text" name="test_cmd" value="python -m pytest tests/" style="margin-bottom:0; flex:1;" required />
                                    <button type="submit" id="submit-btn" style="margin-left:8px;">Fire Build Sequence 🚀</button>
                                    <button type="button" class="button btn-info" onclick="location.href='/explain-architecture'">Explain Architecture 🧠</button>
                                    <button type="button" class="button btn-danger" onclick="location.href='/reset-workspace'">Reset Core 🔄</button>
                                </div>
                            </form>
                        </div>

                        <div class="panel">
                            <h3>📋 Live Runtime Logging Window</h3>
                            <div class="console" id="console-logs">Establishing streams...</div>
                        </div>

                        <div class="panel">
                            <h3>🛠️ Interactive Code Editor</h3>
                            <form action="/save-file" method="POST" style="display:flex; flex-direction:column; flex:1;">
                                <input type="hidden" name="filepath" id="hidden-file-path" value="">
                                <textarea class="editor-textarea" name="filecontent" id="editor-textarea-field" placeholder="// Select a file from the tree to begin structural updates..."></textarea>
                                <button type="submit" style="margin-top:10px; background:#21262d; border:1px solid #30363d; font-size:12px;">Save File Changes 💾</button>
                            </form>
                        </div>

                        <div class="panel" style="max-height: 250px; overflow-y: auto;">
                            <h3>📊 Code Changes Diff Map</h3>
                            <div id="diff-box" style="font-family:monospace; font-size:12px; white-space:pre-wrap; background:#010409; padding:10px; border-radius:6px; border:1px solid #30363d;">No recent modifications.</div>
                        </div>

                        <div class="panel" style="max-height: 250px; overflow-y: auto;">
                            <h3>🧠 Active Workspace Architecture Explainer</h3>
                            <div id="explanation-box" style="font-size:12px; white-space:pre-wrap; background:#010409; padding:10px; border-radius:6px; border:1px solid #30363d; color: #ffa657; line-height: 1.4;">Click map architecture to invoke local explanation stack.</div>
                        </div>
                    </div>
                </div>

                <script>
                    async function loadFileToEditor(relPath) {{
                        document.getElementById("hidden-file-path").value = relPath;
                        try {{
                            const res = await fetch('/api/get-file?path=' + encodeURIComponent(relPath));
                            const data = await res.json();
                            document.getElementById("editor-textarea-field").value = data.content;
                        }} catch (e) {{}}
                    }}

                    setInterval(async () => {{
                        try {{
                            const res = await fetch('/api/status');
                            const data = await res.json();
                            document.getElementById("console-logs").innerHTML = data.logs;
                            document.getElementById("checkpoint-box").innerHTML = data.checkpoints;
                            document.getElementById("file-tree-root").innerHTML = data.tree;
                            document.getElementById("status-text").innerText = data.status;
                            document.getElementById("diff-box").innerHTML = data.diff || "No changes recorded.";
                            document.getElementById("explanation-box").innerText = data.explanation;
                            
                            document.getElementById("m-time").innerText = data.metrics.execution_time;
                            document.getElementById("m-loops").innerText = data.metrics.loops_run;
                            document.getElementById("m-safety").innerText = data.metrics.security_score;
                            document.getElementById("m-cpu").innerText = data.metrics.cpu;
                            document.getElementById("m-mem").innerText = data.metrics.memory;
                        }} catch (e) {{}}
                    }}, 800);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode("utf-8"))
        else: self.send_error(404)

    def do_POST(self):
        url_parts = urlparse(self.path)
        if url_parts.path == "/save-file":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            parsed_data = parse_qs(post_data)
            
            file_rel_path = parsed_data.get('filepath', [''])[0]
            file_content = parsed_data.get('filecontent', [''])[0]
            
            if file_rel_path:
                target_full_path = os.path.join(workspace.base_dir, file_rel_path)
                os.makedirs(os.path.dirname(target_full_path), exist_ok=True)
                with open(target_full_path, "w", encoding="utf-8") as f: f.write(file_content)
                    
            self.send_response(303); self.send_header('Location', '/'); self.end_headers()
            return

        if url_parts.path == "/run-task":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            parsed_data = parse_qs(post_data)
            
            user_task = parsed_data.get('task', [''])[0]
            test_cmd = parsed_data.get('test_cmd', ['python -m pytest tests/'])[0]
            
            Thread(target=async_agent_orchestration, args=(user_task, test_cmd)).start()
            self.send_response(303); self.send_header('Location', '/'); self.end_headers()

def start_browser_server():
    server = HTTPServer(("localhost", 8080), LiveLogHandler)
    server.serve_forever()

def log_to_both(message, log_type="normal"):
    print(message)
    if log_type == "success": LIVE_LOGS.append(f"<span class='success'>{message}</span>")
    elif log_type == "error": LIVE_LOGS.append(f"<span class='error'>{message}</span>")
    elif log_type == "info": LIVE_LOGS.append(f"<span class='info'>{message}</span>")
    else: LIVE_LOGS.append(f"<span>{message}</span>")

# ----------------------------------------------------------------
# 2. Connectors & Automation Infrastructure
# ----------------------------------------------------------------
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
workspace = WorkspaceManager("./local_workspace")
sandbox = LocalSandboxManager()

workspace.apply_workspace_changes(INITIAL_SNAPSHOT)

def capture_current_snapshot():
    snapshot = {}
    for root, _, files in os.walk(workspace.base_dir):
        for file in files:
            if file.endswith('.py'):
                rel = os.path.relpath(os.path.join(root, file), workspace.base_dir).replace("\\", "/")
                with open(os.path.join(root, file), "r", encoding="utf-8") as f: snapshot[rel] = f.read()
    return snapshot

def compute_visual_diffs(old_state, new_state):
    global DIFF_BUFFER
    diff_output = ""
    for path, new_content in new_state.items():
        old_content = old_state.get(path, "")
        if old_content != new_content:
            diff_output += f"<div class='diff-file'>📄 modified: {path}</div>"
            diff = difflib.unified_diff(
                old_content.splitlines(), new_content.splitlines(),
                fromfile='Before Patch', tofile='After AI Action', lineterm=''
            )
            for line in diff:
                if line.startswith('+') and not line.startswith('+++'): diff_output += f"<div class='diff-added'>{line}</div>"
                elif line.startswith('-') and not line.startswith('---'): diff_output += f"<div class='diff-removed'>{line}</div>"
                else: diff_output += f"<div>{line}</div>"
    DIFF_BUFFER = diff_output if diff_output else "No functional changes mapped."

def run_async_explanation():
    global EXPLANATION_BUFFER
    EXPLANATION_BUFFER = "Analyzing codebase structural metrics... Please wait."
    try:
        current_state = capture_current_snapshot()
        prompt = f"Review this codebase structure and write a very concise technical brief detailing what the modules do and how they interact:\n{json.dumps(current_state)}"
        response = client.chat.completions.create(
            model="qwen2.5-coder:1.5b",
            messages=[
                {"role": "system", "content": "You are an enterprise software architect. Provide direct, highly concise summaries of the structure without chatty intros or generic summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        EXPLANATION_BUFFER = response.choices[0].message.content.strip()
    except Exception as e:
        EXPLANATION_BUFFER = f"Failed to map structural logs: {str(e)}"

def async_agent_orchestration(user_task, test_cmd):
    global AGENT_STATUS, LIVE_LOGS, METRICS, CHECKPOINT_REGISTRY
    start_time = time.time()
    AGENT_STATUS = "Running Pipeline Matrix... ⚡"
    LIVE_LOGS.clear()
    
    pre_task_snapshot = capture_current_snapshot()
    cp_id = str(int(time.time()))
    CHECKPOINT_REGISTRY.append({"id": cp_id, "time": datetime.now().strftime("%H:%M:%S"), "snapshot": pre_task_snapshot})

    METRICS["security_score"] = "Auditing..."
    error_context = None

    for loop in range(1, 4):
        METRICS["loops_run"] = loop
        log_to_both(f"🔄 --- Orchestration Loop {loop} ---", "info")
        old_repo_snapshot = capture_current_snapshot()
        repo_state = workspace.generate_directory_tree()
        
        try:
            log_to_both("Generating source updates via Local LLM...")
            
            # Simple manual format check bypass instruction injection
            system_instruction = (
                "You are an elite software agent. Analyze repo changes.\n"
                "Return ONLY a valid JSON matching this schema:\n"
                "{\n  \"modified_files\": {\n    \"models/user.py\": \"code...\"\n  }\n}\n"
                "No markdown code-block wrapping formatting allowed."
            )
            user_content = f"Task: {user_task}\nCurrent Repos:\n{json.dumps(repo_state, indent=2)}"
            if error_context: user_content += f"\nSandbox Validation Errors:\n{error_context}"

            response = client.chat.completions.create(
                model="qwen2.5-coder:1.5b",
                messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": user_content}],
                response_format={"type": "json_object"}, temperature=0.1
            )
            ai_payload = json.loads(response.choices[0].message.content)
            modifications = ai_payload.get("modified_files", {})
            workspace.apply_workspace_changes(modifications)
            
            new_repo_snapshot = capture_current_snapshot()
            compute_visual_diffs(old_repo_snapshot, new_repo_snapshot)

            log_to_both("🛡️ Static Security Vulnerability Audit active...")
            security_check = sandbox.run_workspace_test(workspace.base_dir, "pip install bandit --disable-pip-version-check || true && bandit -r models/ services/ -x tests/")
            
            if "CRITICAL" in security_check["logs"] or "High severities encountered" in security_check["logs"]:
                log_to_both("⚠️ SAFETY SHIELD BREACHED. Self-healing active...", "error")
                METRICS["security_score"] = "FAIL 🚨"
                error_context = f"Security Flaw:\n{security_check['logs']}"
                continue
            else:
                log_to_both("✅ Security Audit Clean: Pass.", "success")
                METRICS["security_score"] = "SECURE 🟢"

            log_to_both(f"⚙️ Running test compilation parameters: '{test_cmd}'")
            test_run = sandbox.run_workspace_test(workspace.base_dir, test_cmd)
            for line in test_run['logs'].split('\n'):
                if line.strip(): log_to_both(line)
            
            METRICS["execution_time"] = f"{round(time.time() - start_time, 1)}s"
            
            if test_run["exit_code"] == 0:
                log_to_both("\n🎉 PIPELINE PASS!", "success")
                AGENT_STATUS = "Pipeline Passed Successfully! ✅"
                return
            else:
                log_to_both("❌ Testing assertions failed. Sending diagnostics...", "error")
                error_context = test_run["logs"]
                time.sleep(0.5)
                
        except Exception as e:
            log_to_both(f"❌ Core Exception Failure: {str(e)}", "error")
            break

    AGENT_STATUS = "Pipeline Run Finished - Verification Failed ⚠️"
    METRICS["execution_time"] = f"{round(time.time() - start_time, 1)}s"

if __name__ == "__main__":
    def reset_hook(handler):
        workspace.apply_workspace_changes(INITIAL_SNAPSHOT)
        global DIFF_BUFFER, CHECKPOINT_REGISTRY, EXPLANATION_BUFFER
        DIFF_BUFFER = "Workspace reset."; CHECKPOINT_REGISTRY.clear(); EXPLANATION_BUFFER = "Cleared."
        handler.send_response(303); handler.send_header('Location', '/'); handler.end_headers()

    def restore_hook(handler, cp_id):
        global DIFF_BUFFER
        target_cp = next((cp for cp in CHECKPOINT_REGISTRY if cp["id"] == cp_id), None)
        if target_cp:
            for root, _, files in os.walk(workspace.base_dir):
                for f in files:
                    if f.endswith('.py'): os.remove(os.path.join(root, f))
            workspace.apply_workspace_changes(target_cp["snapshot"])
            DIFF_BUFFER = f"Reverted to: {target_cp['time']}"
        handler.send_response(303); handler.send_header('Location', '/'); handler.end_headers()
        
    LiveLogHandler.do_GET_orig = LiveLogHandler.do_GET
    def do_GET_patched(self):
        url_p = urlparse(self.path)
        if url_p.path == "/reset-workspace": reset_hook(self); return
        if url_p.path == "/explain-architecture":
            Thread(target=run_async_explanation).start()
            self.send_response(303); self.send_header('Location', '/'); self.end_headers(); return
        if url_p.path == "/restore-checkpoint":
            q = parse_qs(url_p.query); restore_hook(self, q.get('id', [''])[0]); return
        self.do_GET_orig()
    LiveLogHandler.do_GET = do_GET_patched

    server_thread = Thread(target=start_browser_server, daemon=True)
    server_thread.start()
    
    log_to_both("🌍 Opening Interactive Telemetry IDE at http://localhost:8080 ...", "info")
    time.sleep(1)
    webbrowser.open("http://localhost:8080")
    
    while True: time.sleep(1)