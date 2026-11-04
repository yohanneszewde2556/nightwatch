"""Nightwatch FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.storage import get_repository, seed_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle handler."""
    # Ensure database initialized and seed with initial data if empty
    storage = get_repository()
    services = storage.list_services()
    if not services:
        seed_database(storage)
    yield


app = FastAPI(
    title="Nightwatch - AI On-Call Engineer API",
    description="Backend API powering the autonomous AI on-call SRE agent.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local Vite dev server and tunnel testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Public health probe for Cloud Run and container orchestration."""
    return {"status": "ok", "app": "nightwatch"}
