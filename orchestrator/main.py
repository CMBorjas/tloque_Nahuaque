import uvicorn
from orchestrator.api.server import app

def start():
    """Starts the Orchestrator API Backend"""
    print("Starting Tloque Nahuaque Orchestrator Engine...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()
