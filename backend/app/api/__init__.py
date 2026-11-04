"""API package aggregating all routers."""

from fastapi import APIRouter

from app.api.agent import router as agent_router
from app.api.demo import router as demo_router
from app.api.incidents import router as incidents_router
from app.api.internal import router as internal_router
from app.api.reports import router as reports_router
from app.api.services import router as services_router
from app.api.settings import router as settings_router
from app.api.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(services_router)
api_router.include_router(incidents_router)
api_router.include_router(settings_router)
api_router.include_router(agent_router)
api_router.include_router(reports_router)
api_router.include_router(demo_router)
api_router.include_router(internal_router)
api_router.include_router(webhooks_router)

__all__ = ["api_router"]
