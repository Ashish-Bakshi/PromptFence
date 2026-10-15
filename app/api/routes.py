from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.models.schemas import ToolCallRequest
from app.core.security import ROLE_PERMISSIONS, TOOL_REGISTRY
from app.services.audit import log_audit_event, get_recent_audit_logs

router = APIRouter()

@router.post("/execute-tool")
async def execute_tool(request: ToolCallRequest):
    # 1. RBAC Authorization Check
    allowed_tools = ROLE_PERMISSIONS.get(request.caller_role, [])
    if request.tool_name not in allowed_tools:
        await log_audit_event(request.caller_role, request.tool_name, request.arguments, "blocked", "RBAC Unauthorized")
        raise HTTPException(
            status_code=403, 
            detail=f"RBAC Blocked: Role '{request.caller_role}' is not authorized to execute '{request.tool_name}'"
        )

    # 2. Tool Existence Check
    if request.tool_name not in TOOL_REGISTRY:
        await log_audit_event(request.caller_role, request.tool_name, request.arguments, "blocked", "Unrecognized Tool")
        raise HTTPException(status_code=404, detail=f"Unrecognized tool: {request.tool_name}")
    
    schema = TOOL_REGISTRY[request.tool_name]
    
    # 3. Schema Validation Check
    try:
        validated_args = schema(**request.arguments)
    except ValidationError as e:
        await log_audit_event(request.caller_role, request.tool_name, request.arguments, "blocked", "Schema Validation Failed")
        raise HTTPException(status_code=400, detail=e.errors())
    
    # 4. Success Logging
    await log_audit_event(request.caller_role, request.tool_name, request.arguments, "permitted", "Validation Passed")
    
    return {
        "status": "permitted",
        "role": request.caller_role,
        "tool": request.tool_name,
        "validated_arguments": validated_args.model_dump()
    }

@router.get("/audit-logs")
async def view_audit_logs():
    return get_recent_audit_logs()