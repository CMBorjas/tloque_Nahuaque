from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from orchestrator.business.inventory_manager import inventory_mgr, InventoryItem
from orchestrator.ai.nlp_agent import sysadmin_agent

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

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
def process_chat_command(req: ChatRequest):
    """Sends user string to NLP sysadmin agent and returns action context"""
    response_msg = sysadmin_agent.process_command(req.message)
    return {"status": "success", "agent_reply": response_msg}
