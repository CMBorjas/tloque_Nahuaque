from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

from orchestrator.business.inventory_manager import inventory_mgr, InventoryItem, Task
from orchestrator.ai.nlp_agent import sysadmin_agent
from orchestrator.core.docker_client import docker_mgr
from orchestrator.monitor.telemetry import telemetry_collector
from orchestrator.backup.snapshot_manager import snapshot_manager
from orchestrator.compliance.audit_logger import audit_logger

app = FastAPI(title="Tloque Nahuaque API", version="1.0.0")

class HealthResponse(BaseModel):
    status: str
    services_running: int

class ConsumeRequest(BaseModel):
    item_id: str
    amount: int

@app.get("/health", response_model=HealthResponse)
def get_health():
    """Returns the orchestrator engine health"""
    return {"status": "healthy", "services_running": 0}

@app.get("/api/inventory", response_model=List[InventoryItem])
def list_inventory():
    """Returns all items in the inventory"""
    return inventory_mgr.get_all_items()

@app.post("/api/inventory")
def add_new_item(item: InventoryItem):
    """Adds or updates an inventory item"""
    inventory_mgr.add_item(item)
    return {"status": "success", "message": f"Item {item.name} added"}

@app.post("/api/inventory/consume")
def consume_inventory_item(req: ConsumeRequest):
    """Consumes an amount of an item, triggering tasks if threshold is crossed"""
    inventory_mgr.consume_item(req.item_id, req.amount)
    return {"status": "success", "message": f"Consumed {req.amount} of {req.item_id}"}

@app.get("/api/inventory/tasks", response_model=List[Task])
def list_tasks():
    """Returns all procurement tasks"""
    return inventory_mgr.get_all_tasks()

class TaskUpdateRequest(BaseModel):
    status: str

@app.patch("/api/inventory/tasks/{task_id}")
def update_task(task_id: int, req: TaskUpdateRequest):
    """Updates the status of a specific task"""
    inventory_mgr.update_task_status(task_id, req.status)
    return {"status": "success", "message": f"Task {task_id} updated to {req.status}"}

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
def process_chat_command(req: ChatRequest):
    """Sends user string to NLP sysadmin agent and returns action context"""
    response_msg = sysadmin_agent.process_command(req.message)
    return {"status": "success", "agent_reply": response_msg}

@app.post("/api/orchestration/deploy")
def deploy_stack():
    """Triggers the backend engine to build and run all services in the catalog"""
    res = docker_mgr.deploy_stack()
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

@app.get("/api/orchestration/status")
def get_orchestration_status():
    """Returns the live running state of all containers managed by the engine"""
    containers = docker_mgr.list_containers()
    return {"status": "success", "containers": containers}

@app.get("/api/system/telemetry")
def get_system_telemetry():
    """Returns real-time hardware status metrics"""
    metrics = telemetry_collector.get_system_metrics()
    return {"status": "success", "metrics": metrics}

class BackupRequest(BaseModel):
    volume_name: str

@app.post("/api/orchestration/backup")
def create_backup(req: BackupRequest):
    """Backs up a specific Docker volume to the backup target"""
    res = snapshot_manager.backup_volume(req.volume_name)
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

@app.get("/api/compliance/audit")
def get_audit_logs(limit: int = 100):
    """Returns recent audit logs for compliance tracking"""
    logs = audit_logger.get_recent_logs(limit)
    return {"status": "success", "logs": logs}
