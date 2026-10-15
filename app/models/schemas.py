from pydantic import BaseModel
from typing import Dict, Any

# Specific schemas for the tools your AI is allowed to use
class QueryDatabaseArgs(BaseModel):
    table_name: str
    limit: int
    
class SendEmailArgs(BaseModel):
    recipient: str
    subject: str
    body: str

# The master payload expected from the LLM or AI Agent
class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]