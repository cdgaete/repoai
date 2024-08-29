import json
import docker
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DockerService:
    def __init__(self, project_path: Path):
        self.project_name = project_path.stem
        self.project_path = project_path
        self.client = docker.from_env()
        logger.debug("Docker service initialized")

    def build_image(self, file_path: str, tag: str) -> str:
        path = self.project_path / file_path
        image, _ = self.client.images.build(path=str(path), tag=tag)
        return image.id

    def run_container(self, image: str, **kwargs) -> str:
        container = self.client.containers.run(image, detach=True, **kwargs)
        return container.id

    def stop_container(self, container_id: str):
        container = self.client.containers.get(container_id)
        container.stop()

    def get_container_logs(self, container_id: str) -> str:
        container = self.client.containers.get(container_id)
        return container.logs().decode('utf-8')

    def run_docker_compose(self, compose_file_path: str = None):
        path = self.project_path / compose_file_path
        subprocess.run(["docker", "compose", "-f", str(path), "-p", self.project_name, "up", "-d"], check=True)

    def stop_docker_compose(self, compose_file_path: str = None):
        path = self.project_path / compose_file_path
        subprocess.run(["docker", "compose", "-f", str(path), "-p", self.project_name, "down", "-v"], check=True)

    def get_docker_compose_container_ports(self, compose_file_path):
        ids = self.get_container_ids(compose_file_path)
        info = self.get_docker_compose_containers_info(compose_file_path)
        ports = {}
        for id in ids:
            for container in info:
                if container['id'] == id:
                    name = container['name']
                    ports[name] = container['attr']['NetworkSettings']['Ports']
        return ports


    def get_container_ids(self, compose_file_path):
        path = self.project_path / compose_file_path
        command = [
            "docker", "compose",
            "-f", str(path),  # Convert Path to string
            "-p", self.project_name,
            "ps",
            "-q"
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        container_ids = result.stdout.strip().split('\n')
        return container_ids
        
    def get_docker_compose_containers_info(self, compose_file_path):
        container_ids = self.get_container_ids(compose_file_path)
        containers = []
        for container_id in container_ids:
            container = self.client.containers.get(container_id)
            containers.append({
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "N/A",
                "attr": container.attrs
            })
        return containers
    