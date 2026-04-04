import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.business.inventory_manager import inventory_mgr, InventoryItem
import sqlite3

def test_inventory():
    print("--- [1] Adding new item 'Printer Paper' (qty 10, threshold 5) ---")
    item = InventoryItem(
        item_id="paper_01",
        name="Printer Paper",
        quantity=10,
        threshold=5,
        unit="boxes"
    )
    inventory_mgr.add_item(item)
    
    print("--- [2] Generating tasks... (None expected) ---")
    inventory_mgr.check_thresholds()
    
    print("--- [3] Consuming 6 boxes... ---")
    inventory_mgr.consume_item("paper_01", 6)
    
    print("--- [4] Verifying state in tasks DB ---")
    conn = sqlite3.connect("data/inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    
    print(f"Tasks found: {len(tasks)}")
    for t in tasks:
        print(f"  - {t[1]}: {t[2]}")
    conn.close()

if __name__ == "__main__":
    test_inventory()
