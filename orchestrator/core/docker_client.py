import docker
import yaml
import os
from orchestrator.core.network_manager import network_mgr

class DockerClientManager:
    """Interacts safely with the Docker SDK to handle container lifecycle,
    volumes, and persistent storage.
    """
    def __init__(self, catalog_path="services/catalog.yml"):
        self.catalog_path = catalog_path
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            print(f"Error connecting to Docker Daemon: {e}")
            self.client = None

    def _load_catalog(self):
        if not os.path.exists(self.catalog_path):
            print(f"Failure: Catalog file not found at {self.catalog_path}")
            return {}
        with open(self.catalog_path, 'r') as file:
            return yaml.safe_load(file)

    def list_containers(self):
        if not self.client:
            return []
        try:
            containers = self.client.containers.list(all=True)
            return [{"id": c.short_id, "name": c.name, "status": c.status} for c in containers]
        except Exception as e:
            print(f"Failed to list containers: {e}")
            return []

    def deploy_stack(self):
        """Orchestrates deployment of all services defined in catalog.yml"""
        if not self.client:
            return {"status": "error", "message": "Docker SDK offline"}
        
        # Ensure underlying isolated network is active
        network_mgr.initialize_mesh()
        
        catalog = self._load_catalog()
        services = catalog.get('services', {})
        results = []
        
        for name, config in services.items():
            res = self.start_service(name, config)
            results.append(res)
            
        return {"status": "success", "deployments": results}

    def start_service(self, service_name, config):
        """Starts a target service based on config parameters"""
        if not self.client:
            return {"service": service_name, "status": "failed", "reason": "Docker SDK offline"}
            
        print(f"Deploying {service_name}...")
        image = config.get('image')
        port_bindings = {}
        environment = config.get('environment', [])
        volumes = config.get('volumes', [])
        
        # Map Ports "8080:80" -> {"80/tcp": 8080}
        for port_map in config.get('ports', []):
            host_port, container_port = port_map.split(':')
            port_bindings[f"{container_port}/tcp"] = int(host_port)

        try:
            # Safely detach and run, letting Docker SDK pull locally missing images
            container = self.client.containers.run(
                image,
                name=service_name,
                detach=True,
                network=network_mgr.network_name,
                ports=port_bindings,
                environment=environment,
                volumes=volumes,
                restart_policy={"Name": "always"}
            )
            print(f"[OK] {service_name} up and running (ID: {container.short_id})")
            return {"service": service_name, "status": "running", "id": container.short_id}
            
        except docker.errors.APIError as e:
            # Often means name already in use or port binding failure
            print(f"[WARN] Failed starting {service_name}: {str(e)}")
            return {"service": service_name, "status": "failed", "reason": str(e)}

    def restart_service(self, service_name):
        """Restarts a specific container"""
        if not self.client: return False
        try:
            container = self.client.containers.get(service_name)
            container.restart()
            return True
        except docker.errors.NotFound:
            return False

docker_mgr = DockerClientManager()
