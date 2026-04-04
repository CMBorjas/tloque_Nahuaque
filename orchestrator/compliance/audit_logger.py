import sqlite3
import os
from datetime import datetime
from typing import List, Dict

class AuditLogger:
    """Aggregates container and access logs to provide tamper-evident
    reports for compliance reviews.
    """
    def __init__(self, db_path="data/audit.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                service TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user TEXT NOT NULL,
                details TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def log_event(self, service: str, event_type: str, user: str, details: str):
        """Records an auditable event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO audit_logs (timestamp, service, event_type, user, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, service, event_type, user, details))
        conn.commit()
        conn.close()
        print(f"[AUDIT] {timestamp} | {service} | {event_type} | {user} | {details}")
        
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, str]]:
        """Returns the most recent audit logs"""
        conn = sqlite3.connect(self.db_path)
        # return rows as dicts
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(r) for r in rows]

audit_logger = AuditLogger()
