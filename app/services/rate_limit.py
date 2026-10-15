import os
import redis.asyncio as redis
from fastapi import HTTPException

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Create a global Redis connection pool
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Define limits: Requests per minute
RATE_LIMITS = {
    "admin": 100,
    "analyst": 10,
    "guest": 5
}

async def check_rate_limit(caller_role:str):
    """Enforces a requests-per-minute limit using Redis."""
    limit = RATE_LIMITS.get(caller_role, 5)

    # Create a unique key for this role in the current minute
    # e.g., "rate_limit:analyst"
    redis_key = f"rate_limit:{caller_role}"

    # Increment the counter
    current_count = await redis_client.incr(redis_key)

    # If this is the first request, set the key to expire in 60 seconds
    if current_count == 1:
        await redis_client.expire(redis_key, 60)
        
    if current_count > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for role '{caller_role}'. Limit is {limit} requests per minute."
        )