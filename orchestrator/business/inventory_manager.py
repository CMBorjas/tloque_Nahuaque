import sqlite3
import os
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class InventoryItem(BaseModel):
    item_id: str
    name: str
    quantity: int
    threshold: int
    unit: str

class Task(BaseModel):
    task_id: Optional[int] = None
    title: str
    description: str
    status: str = "pending"
    created_at: str

class InventoryManager:
    """Tracks physical or resource inventories and hooks into the task
    generation pipeline to alert or create workflows when stock drops
    below thresholds.
    """
    def __init__(self, db_path="data/inventory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                item_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                threshold INTEGER NOT NULL,
                unit TEXT NOT NULL
            )
        ''')
        
        # Create tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_item(self, item: InventoryItem):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO inventory (item_id, name, quantity, threshold, unit)
            VALUES (?, ?, ?, ?, ?)
        ''', (item.item_id, item.name, item.quantity, item.threshold, item.unit))
        conn.commit()
        conn.close()
        
        # Check if immediately needs restock
        self.check_thresholds(item.item_id)

    def consume_item(self, item_id: str, amount: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE inventory SET quantity = quantity - ? WHERE item_id = ?', (amount, item_id))
        conn.commit()
        conn.close()
        
        self.check_thresholds(item_id)

    def get_all_items(self) -> List[InventoryItem]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT item_id, name, quantity, threshold, unit FROM inventory')
        rows = cursor.fetchall()
        conn.close()
        
        return [InventoryItem(item_id=r[0], name=r[1], quantity=r[2], threshold=r[3], unit=r[4]) for r in rows]

    def create_task(self, title: str, description: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO tasks (title, description, status, created_at)
            VALUES (?, ?, ?, ?)
        ''', (title, description, 'pending', created_at))
        conn.commit()
        conn.close()
        print(f"[TASK CREATED] {title}: {description}")

    def check_thresholds(self, specific_item_id: str = None):
        """Generates procurement tasks if items fall below threshold"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if specific_item_id:
            cursor.execute('SELECT item_id, name, quantity, threshold, unit FROM inventory WHERE item_id = ?', (specific_item_id,))
        else:
            cursor.execute('SELECT item_id, name, quantity, threshold, unit FROM inventory')
            
        rows = cursor.fetchall()
        conn.close()
        
        for r in rows:
            item = InventoryItem(item_id=r[0], name=r[1], quantity=r[2], threshold=r[3], unit=r[4])
            if item.quantity < item.threshold:
                # Trigger Task
                title = f"Restock Required: {item.name}"
                desc = f"{item.name} stock ({item.quantity} {item.unit}) has dropped below threshold ({item.threshold} {item.unit})."
                self.create_task(title, desc)

    def get_all_tasks(self) -> List[Task]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT task_id, title, description, status, created_at FROM tasks')
        rows = cursor.fetchall()
        conn.close()
        
        return [Task(task_id=r[0], title=r[1], description=r[2], status=r[3], created_at=r[4]) for r in rows]

    def update_task_status(self, task_id: int, status: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET status = ? WHERE task_id = ?', (status, task_id))
        conn.commit()
        conn.close()

inventory_mgr = InventoryManager()
