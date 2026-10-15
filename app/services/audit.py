import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any

DB_FILE = "audit_ledger.db"

def init_db():
    """Initializes the database schema if it doesn't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                caller_role TEXT,
                tool_name TEXT,
                arguments TEXT,
                status TEXT,
                reason TEXT
            )
        ''')

def log_audit_event(caller_role: str, tool_name: str, arguments: dict, status: str, reason: str = ""):
    """Appends an execution attempt to the immutable ledger."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO audit_logs (timestamp, caller_role, tool_name, arguments, status, reason) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), caller_role, tool_name, json.dumps(arguments), status, reason)
        )

def get_recent_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent audit logs for security review."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]