from typing import Dict, List
from app.models.schemas import QueryDatabaseArgs, SendEmailArgs

# Maps the string name of a tool to its strict validation schema
TOOL_REGISTRY = {
    "query_database": QueryDatabaseArgs,
    "send_email": SendEmailArgs
}

# The single source of truth for who is allowed to do what
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "admin": ["query_database", "send_email"],
    "analyst": ["query_database"],
    "guest": []
}