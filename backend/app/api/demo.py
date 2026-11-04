"""Demo chaos engineering endpoints for live scenario validation."""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
import httpx

from app.api.deps import get_storage
from app.core.auth import verify_dashboard_auth
from app.detectors.health_checker import extract_base_url
from app.models.schemas import ChaosRequest
from app.storage.base import BaseRepository

logger = logging.getLogger("nightwatch.api.demo")

router = APIRouter(
    prefix="/api/demo",
    tags=["demo"],
    dependencies=[Depends(verify_dashboard_auth)],
)


@router.post("/chaos")
async def inject_chaos(
    request: ChaosRequest,
    storage: BaseRepository = Depends(get_storage),
) -> Dict[str, Any]:
    """Inject a controlled failure (crash, slow, bad_deploy, reset) into the target sample app."""
    service_id = request.serviceId or "svc-demo-shop"
    service = storage.get_service(service_id)
    if not service:
        # Fallback to local default demo-shop
        health_url = "http://127.0.0.1:8001/health"
    else:
        health_url = service.healthUrl

    base_url = extract_base_url(health_url)
    headers = {"X-Admin-Token": "demo-admin-secret"}
    scenario = request.scenario.lower().strip()

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            if scenario in ("bad_deploy", "v2", "deploy_v2"):
                # Deploy v2 with checkout discount bug
                resp = await client.post(
                    f"{base_url}/admin/deploy",
                    json={"version": "v2"},
                    headers=headers,
                )
                msg = "Deployed v2 release with buggy discount calculations (~70% error spike on checkouts)."

            elif scenario in ("slow", "latency", "leak"):
                # Inject growing synthetic latency up to ~6s
                resp = await client.post(
                    f"{base_url}/admin/chaos",
                    json={"mode": "slow"},
                    headers=headers,
                )
                msg = "Injected growing latency chaos mode (synthetic response delay up to ~6s)."

            elif scenario in ("crash", "down", "outage"):
                # Make /health fail with HTTP 503
                resp = await client.post(
                    f"{base_url}/admin/chaos",
                    json={"mode": "down"},
                    headers=headers,
                )
                msg = "Triggered service outage: /health returns HTTP 503."

            elif scenario in ("reset", "none", "recover", "rollback"):
                # Clear chaos and rollback to v1
                await client.post(
                    f"{base_url}/admin/chaos",
                    json={"mode": "none"},
                    headers=headers,
                )
                resp = await client.post(
                    f"{base_url}/admin/rollback",
                    headers=headers,
                )
                msg = "Reset chaos to none and rolled back app to v1 (healthy)."

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown scenario '{request.scenario}'. Valid options: bad_deploy, slow, crash, reset.",
                )

            # Query current admin state
            state_resp = await client.get(f"{base_url}/admin/state", headers=headers)
            current_state = state_resp.json() if state_resp.status_code == 200 else {}

            return {
                "success": (resp.status_code == 200),
                "scenario": scenario,
                "message": msg,
                "remote_status": resp.status_code,
                "current_state": current_state,
            }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to inject chaos against %s: %s", base_url, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with demo service at {base_url}: {exc}",
        )
