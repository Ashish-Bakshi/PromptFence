import os
import json
import psycopg
from psycopg.rows import dict_row
from datetime import datetime
from typing import List, Dict, Any

# Fetch the URL from docker-compose, default to local if not found
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/promptfence")

def get_connection():
    return psycopg.connect(DATABASE_URL)

async def init_db():
    """Initializes the PostgreSQL database schema if it doesn't exist."""
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT,
                    caller_role TEXT,
                    tool_name TEXT,
                    arguments TEXT,
                    status TEXT,
                    reason TEXT
                )
            ''')
        await conn.commit()

async def log_audit_event(caller_role: str, tool_name: str, arguments: dict, status: str, reason: str = ""):
    """Appends an execution attempt to the immutable ledger."""
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO audit_logs (timestamp, caller_role, tool_name, arguments, status, reason) VALUES (%s, %s, %s, %s, %s, %s)",
                (datetime.utcnow().isoformat(), caller_role, tool_name, json.dumps(arguments), status, reason)
            )
        await conn.commit()

async def get_recent_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent audit logs for security review."""
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        # psycopg 3 uses row_factory=dict_row instead of RealDictCursor
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT %s", (limit,))
            rows = await cursor.fetchall()
            return list(rows)