import docker
import os

class AdvancedSandboxManager:
    def __init__(self, image_name="python:3.10-slim"):
        self.client = docker.from_env()
        self.image_name = image_name

    def run_workspace_test(self, workspace_path: str, test_command: str) -> dict:
        abs_workspace = os.path.abspath(workspace_path)
        container = None
        try:
            container = self.client.containers.run(
                image=self.image_name,
                command=f"sh -c 'pip install pytest && {test_command}'",
                volumes={abs_workspace: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                network_disabled=False, # Agar container dependencies load kare to temporarily enable rakhein
                mem_limit="512m",
                detach=True
            )
            result = container.wait(timeout=30)
            logs = container.logs().decode("utf-8")
            return {"exit_code": result["StatusCode"], "logs": logs}
        except Exception as e:
            return {"exit_code": -1, "logs": str(e)}
        finally:
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass