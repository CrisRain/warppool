# controller-app/warp_controller.py
import docker
from docker import errors as docker_errors
import logging

client = docker.from_env()
logging.basicConfig(level=logging.INFO)

def execute_command_in_container(container_name, command):
    try:
        container = client.containers.get(container_name)
        exit_code, output = container.exec_run(command)
        if exit_code != 0:
            # This is now handled by ContainerError, but we keep it as a fallback.
            logging.error(f"Command '{command}' in container '{container_name}' failed with exit code {exit_code}: {output.decode().strip()}")
            return None
        return output.decode().strip()
    except docker_errors.ContainerError as e:
        logging.error(f"Failed to execute command in {container_name}. Command: '{command}'. Error: {e}")
        return None
    except docker_errors.APIError as e:
        logging.error(f"Docker API error for container {container_name}. Command: '{command}'. Error: {e}")
        return None
    except docker_errors.NotFound:
        logging.error(f"Container '{container_name}' not found.")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while executing command '{command}' in '{container_name}': {e}")
        return None

def connect(container_name: str) -> bool:
    logging.info(f"Connecting WARP in container {container_name}...")
    output = execute_command_in_container(container_name, "warp-cli connect")
    return output is not None and "Success" in output

def disconnect(container_name: str) -> bool:
    logging.info(f"Disconnecting WARP in container {container_name}...")
    output = execute_command_in_container(container_name, "warp-cli disconnect")
    return output is not None and "Success" in output

def get_status(container_name: str) -> dict:
    output = execute_command_in_container(container_name, "warp-cli status")
    if not output:
        return {"status": "Unknown"}
    # 简单解析
    status_info = {}
    for line in output.split('\n'):
        if ":" in line:
            key, value = line.split(":", 1)
            status_info[key.strip()] = value.strip()
    return status_info