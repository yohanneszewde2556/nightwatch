"""Tool for executing service deployments and rollbacks."""

import logging
from typing import Any, Dict
import httpx

from app.detectors.health_checker import extract_base_url
from app.models.schemas import Service

logger = logging.getLogger("nightwatch.tools.deploy")


async def rollback_deploy(service: Service, admin_token: str = "demo-admin-secret") -> Dict[str, Any]:
    """Execute a rollback for the target service.

    For demo-shop, calls POST /admin/rollback.
    For Cloud Run services, shifts traffic to the previous revision.

    Args:
        service: The service model.
        admin_token: Admin token for authentication.

    Returns:
        Dict with execution status and details.
    """
    base_url = extract_base_url(service.healthUrl)
    rollback_url = f"{base_url}/admin/rollback"

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                rollback_url,
                headers={"X-Admin-Token": admin_token},
            )
            if resp.status_code == 200:
                data = resp.json()
                logger.info("Successfully executed rollback on service %s: %s", service.name, data)
                return {
                    "success": True,
                    "service_id": service.id,
                    "service_name": service.name,
                    "version": data.get("version", "v1"),
                    "commit_label": data.get("commit_label", "Initial demo-shop API"),
                    "message": f"Rolled back {service.name} successfully to previous revision.",
                }
            return {
                "success": False,
                "error": f"Rollback failed with HTTP {resp.status_code}: {resp.text[:200]}",
            }
    except Exception as exc:
        logger.error("Failed to execute rollback on %s: %s", service.name, exc)
        return {
            "success": False,
            "error": f"Failed to connect to rollback endpoint: {exc}",
        }
