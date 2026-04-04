from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Tloque Nahuaque API", version="1.0.0")

class HealthResponse(BaseModel):
    status: str
    services_running: int

@app.get("/health", response_model=HealthResponse)
def get_health():
    """Returns the orchestrator engine health"""
    return {"status": "healthy", "services_running": 0}
