import json
import os
from openai import OpenAI
from workspace import WorkspaceManager
from sandbox_v2 import AdvancedSandboxManager

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-key-here"))
workspace = WorkspaceManager("./my_project_workspace")
sandbox = AdvancedSandboxManager()

# Pre-seeding workspace with structure for demonstration
workspace.apply_workspace_changes({
    "models/user.py": "class User:\n    def __init__(self, username):\n        self.username = username",
    "services/auth.py": "from models.user import User\ndef register_user(name):\n    return User(name)",
    "tests/test_auth.py": "from services.auth import register_user\ndef test_registration():\n    u = register_user('Arjun')\n    assert u.username == 'Arjun'"
})

def ask_llm_multi_file(prompt: str, current_workspace: dict, error_logs: str = None) -> dict:
    system_instruction = (
        "You are an elite multi-file architecture AI assistant.\n"
        "Analyze the repository map and provide code updates.\n"
        "You MUST respond ONLY with a raw JSON object mapped exactly as:\n"
        "{\n  \"modified_files\": {\n    \"path/to/file.py\": \"complete file code contents string\"\n  }\n}\n"
        "Do not include markdown or wrapping blocks outside valid JSON raw objects."
    )
    
    user_content = f"Task: {prompt}\n\nCurrent Repository Structure:\n{json.dumps(current_workspace, indent=2)}"
    if error_logs:
        user_content += f"\n\n[SANDBOX SYSTEM TEST ERRORS]:\n{error_logs}"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ],
        response_format={"type": "json_object"}, # Strict json mode force enforcement
        temperature=0.1
    )
    
    return json.loads(response.choices[0].message.content)

# Execution Pipeline Setup
def run_workspace_loop():
    user_task = "Modify the registration code to prevent names shorter than 3 characters by throwing a ValueError. Update the user model if necessary and add a new test case in test_auth.py checking this constraint."
    error_context = None

    for loop in range(1, 3):
        print(f"\n⚡ --- System Workspace Iteration Loop {loop} ---")
        
        # 1. Map current file layouts
        repo_state = workspace.generate_directory_tree()
        
        # 2. Get AI changes response package
        ai_payload = ask_llm_multi_file(user_task, repo_state, error_context)
        
        # 3. Apply changes seamlessly across files
        print("Applying dynamic workspace multi-file sync updates...")
        workspace.apply_workspace_changes(ai_payload.get("modified_files", {}))
        
        # 4. Sandbox verification execution run
        print("Spinning workspace testing runner sandbox container instances...")
        test_run = sandbox.run_workspace_test(workspace.base_dir, "pytest tests/")
        
        print(f"Execution Terminal Output Traces:\n{test_run['logs']}")
        
        if test_run["exit_code"] == 0:
            print("\n🎉 ARCHITECTURE CONSTRAINTS VERIFIED: Workspace configuration optimized successfully!")
            return
        else:
            print("❌ Workspace Test Failures encountered. Preparing feedback matrices...")
            error_context = test_run["logs"]

if __name__ == "__main__":
    run_workspace_loop()