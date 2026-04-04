import docker

class NetworkManager:
    """Manages isolated Docker networks and proxy configurations
    for the Service Mesh (e.g. Traefik/Nginx).
    """
    def __init__(self):
        self.network_name = "tloque_mesh"
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            print(f"NetworkManager Error connecting to Docker Daemon: {e}")
            self.client = None
    
    def initialize_mesh(self):
        """Creates the internal secure network if it doesn't exist"""
        if not self.client:
            print("Cannot initialize mesh: Docker client offline.")
            return False

        try:
            # Check if network exists
            self.client.networks.get(self.network_name)
            print(f"Network '{self.network_name}' already active.")
            return True
        except docker.errors.NotFound:
            print(f"Creating isolated network: {self.network_name}...")
            try:
                self.client.networks.create(self.network_name, driver="bridge")
                return True
            except docker.errors.APIError as e:
                print(f"Failed to create network: {e}")
                return False

network_mgr = NetworkManager()
