"""Tool for actively probing a service's health endpoint."""

from typing import Any, Dict
from app.detectors.health_checker import probe_service_health
from app.models.schemas import Service


async def check_health(service: Service) -> Dict[str, Any]:
    """Call the service's health endpoint and measure round-trip latency.

    Args:
        service: The service model.

    Returns:
        Dict with status code, latency in ms, and error details.
    """
    http_status, latency_ms, error_msg = await probe_service_health(service.healthUrl)
    return {
        "service_id": service.id,
        "service_name": service.name,
        "health_url": service.healthUrl,
        "http_status": http_status,
        "latency_ms": latency_ms,
        "error": error_msg,
        "is_healthy": (http_status == 200),
    }
