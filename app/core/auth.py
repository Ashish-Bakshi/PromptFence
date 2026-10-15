import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# In production, this would be an environment variable loaded securely
SECRET_KEY = "promptfence-super-secret-development-key"
ALGORITHM = "HS256"

# FastAPI's built-in Bearer token extractor
security = HTTPBearer()

async def get_caller_role(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Decodes the JWT and extracts the caller's role."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if not role:
            raise HTTPException(status_code=403, detail="Token payload missing 'role' claim.")
        return role
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid cryptographic token.")