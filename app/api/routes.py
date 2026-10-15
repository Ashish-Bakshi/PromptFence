import jwt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from app.models.schemas import ToolCallRequest
from app.core.security import ROLE_PERMISSIONS, TOOL_REGISTRY
from app.core.auth import get_caller_role, SECRET_KEY, ALGORITHM
from app.services.audit import log_audit_event, get_recent_audit_logs
from app.services.rate_limit import check_rate_limit

router = APIRouter()

# 
@router.get("/generate-token")
async def generate_token(role: str):
    """Mints a temporary JWT for testing purposes."""
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="Unknown role")
    token = jwt.encode({"role": role}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "role": role}

@router.post("/execute-tool")
async def execute_tool(request: ToolCallRequest, caller_role: str = Depends(get_caller_role),):
    # 0. Check Redis Rate Limits (Drops traffic immediately if over limit)
    await check_rate_limit(caller_role)

    # 1. RBAC Authorization Check
    allowed_tools = ROLE_PERMISSIONS.get(caller_role, [])
    if request.tool_name not in allowed_tools:
        await log_audit_event(caller_role, request.tool_name, request.arguments, "blocked", "RBAC Unauthorized")
        raise HTTPException(
            status_code=403, 
            detail=f"RBAC Blocked: Role '{caller_role}' is not authorized to execute '{request.tool_name}'"
        )

    # 2. Tool Existence Check
    if request.tool_name not in TOOL_REGISTRY:
        await log_audit_event(caller_role, request.tool_name, request.arguments, "blocked", "Unrecognized Tool")
        raise HTTPException(status_code=404, detail=f"Unrecognized tool: {request.tool_name}")
    
    schema = TOOL_REGISTRY[request.tool_name]
    
    # 3. Schema Validation Check
    try:
        validated_args = schema(**request.arguments)
    except ValidationError as e:
        await log_audit_event(caller_role, request.tool_name, request.arguments, "blocked", "Schema Validation Failed")
        raise HTTPException(status_code=400, detail=e.errors())
    
    # 4. Success Logging
    await log_audit_event(caller_role, request.tool_name, request.arguments, "permitted", "Validation Passed")
    
    return {
        "status": "permitted",
        "role": caller_role,
        "tool": request.tool_name,
        "validated_arguments": validated_args.model_dump()
    }

@router.get("/audit-logs")
async def view_audit_logs():
    return get_recent_audit_logs()