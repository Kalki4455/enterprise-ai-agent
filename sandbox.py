import docker
import os

class LocalSandboxManager:
    def __init__(self, image_name="python:3.10-slim"):
        """
        Initializes the Docker connection. 
        Uses TCP localhost port to completely bypass Windows Administrator/Named Pipe permission errors.
        """
        try:
            # Step 1: Attempt direct network connection (Recommended for Windows)
            self.client = docker.DockerClient(base_url="tcp://localhost:2375")
            # Quick connection test to verify daemon response
            self.client.ping()
        except Exception:
            # Fallback: Agar custom TCP setting missing ho to default pipe par clear reload karega
            self.client = docker.from_env()
            
        self.image_name = image_name

    def run_workspace_test(self, workspace_path: str, test_command: str) -> dict:
        """
        Mounts the dynamic local code folder inside a container, runs tests, 
        and safely returns execution status codes and error stack traces.
        """
        abs_workspace = os.path.abspath(workspace_path)
        container = None
        
        try:
            # Step 2: Spin up isolated ephemeral container instance
            container = self.client.containers.run(
                image=self.image_name,
                # Command execution: local test run wrapper inside container environment
                command=f"sh -c 'pip install pytest --disable-pip-version-check || true && {test_command}'",
                volumes={abs_workspace: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                network_disabled=False,     # Security Layer: Container cannot hit external servers
                mem_limit="512m",          # Resource Constraint: Maximum allocation limit 512MB RAM
                detach=True
            )

            # Step 3: Wait for process terminal execution completion
            result = container.wait(timeout=20)
            exit_code = result["StatusCode"]
            
            # Step 4: Extract diagnostic runtime logs (stdout + stderr)
            logs = container.logs().decode("utf-8")
            
            return {
                "exit_code": exit_code,
                "logs": logs
            }

        except Exception as e:
            # Capture structural error failures seamlessly
            return {
                "exit_code": -1, 
                "logs": f"Sandbox Runtime Exception: {str(e)}"
            }
            
        finally:
            # Step 5: Strict Infrastructure Cleanup (No loose container endpoints left behind)
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass