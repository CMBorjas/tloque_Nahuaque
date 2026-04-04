import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.core.docker_client import docker_mgr

def test_deploy():
    print("--- 1. Testing YAML Catalog Parse ---")
    catalog = docker_mgr._load_catalog()
    print(f"Loaded Catalog Services: {list(catalog.get('services', {}).keys())}")
    
    print("\n--- 2. Connecting to Docker SDK... ---")
    if docker_mgr.client:
        print("[OK] Docker Engine is online.")
        print("\n--- 3. Checking Live Containers ---")
        live = docker_mgr.list_containers()
        for l in live:
            print(f"Container: {l['name']} (Status: {l['status']})")
    else:
        print("[WARN] Local Docker Daemon offline or unreachable. " 
              "This is expected if running outside a linux docker group environment.")
        
if __name__ == "__main__":
    test_deploy()
