import os
import json

class WorkspaceManager:
    def __init__(self, base_dir="./local_workspace"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def generate_directory_tree(self) -> dict:
        """Pore workspace files ko scan karke AI ke liye map banata hai."""
        workspace_map = {}
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(('.py', '.json', '.md')) and not file.startswith('.'):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, self.base_dir)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        workspace_map[relative_path] = f.read()
        return workspace_map

    def apply_workspace_changes(self, modifications: dict):
        """AI ke diye gaye new code ko files me save karta hai."""
        for rel_path, content in modifications.items():
            target_path = os.path.abspath(os.path.join(self.base_dir, rel_path))
            if not target_path.startswith(self.base_dir):
                raise PermissionError("Security Block: Path traversal detected!")
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding='utf-8') as f:
                f.write(content)