"""Tool for fetching recent logs from monitored services."""

import logging
from typing import Any, Dict, List
import httpx

from app.detectors.health_checker import extract_base_url
from app.models.schemas import Service

logger = logging.getLogger("nightwatch.tools.logs")


async def fetch_logs(service: Service, limit: int = 50, level: str = "ERROR") -> List[Dict[str, Any]]:
    """Fetch recent structured logs from the service's log endpoint.

    Args:
        service: The service model.
        limit: Max number of log entries.
        level: Optional log level filter (ERROR, WARN, INFO).

    Returns:
        List of structured log dictionaries.
    """
    base_url = extract_base_url(service.healthUrl)
    logs_url = f"{base_url}/logs"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                logs_url,
                params={"limit": limit, "level": level},
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
            logger.warning("Service %s returned HTTP %d for logs", service.name, resp.status_code)
            return []
    except Exception as exc:
        logger.error("Failed to fetch logs for service %s: %s", service.name, exc)
        return []
