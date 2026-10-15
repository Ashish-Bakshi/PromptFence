from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import router
from app.services.audit import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database schema when the server starts
    await init_db()
    yield
    # Any cleanup code (like closing connection pools) would go here

# Initialize the FastAPI application
app = FastAPI(
    title="PromptFence",
    version="0.2.0",
    description="A security gateway and RBAC proxy for LLM tool execution.",
    lifespan=lifespan
)

# Attach our endpoints from the API router. 
# We add the /v1 prefix here so we don't have to repeat it in routes.py.
app.include_router(router, prefix="/v1")