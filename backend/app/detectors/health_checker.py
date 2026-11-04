"""HTTP probes for service health endpoints and structured log streaming."""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("nightwatch.detectors.health_checker")


def extract_base_url(health_url: str) -> str:
    """Derive service base origin URL from its health URL."""
    parsed = urlparse(health_url)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc or parsed.path.split("/")[0]
    return f"{scheme}://{netloc}"


async def probe_service_health(
    health_url: str,
    timeout: float = 5.0,
) -> Tuple[int, float, Optional[str]]:
    """Probe a service's health endpoint and measure round-trip latency.

    Args:
        health_url: Full URL to the health check endpoint.
        timeout: Maximum request timeout in seconds.

    Returns:
        Tuple of (http_status_code, latency_ms, error_message).
        http_status_code is 0 if connection failed, timed out, or network error.
    """
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(health_url)
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            error_msg = None
            if resp.status_code >= 400:
                try:
                    data = resp.json()
                    error_msg = data.get("detail") or data.get("error") or resp.text[:200]
                except Exception:
                    error_msg = resp.text[:200]
            return resp.status_code, latency_ms, error_msg

    except httpx.TimeoutException:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return 0, latency_ms, f"Request timed out after {timeout}s"
    except httpx.ConnectError as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return 0, latency_ms, f"Connection refused or unreachable: {exc}"
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return 0, latency_ms, f"Probe error: {exc}"


async def probe_service_logs(
    health_url: str,
    since: Optional[str] = None,
    limit: int = 50,
    timeout: float = 4.0,
) -> List[Dict[str, Any]]:
    """Attempt to pull recent structured error logs from the monitored service.

    Args:
        health_url: Service health URL (used to derive base origin).
        since: Optional ISO timestamp to query logs since.
        limit: Max log entries to retrieve.
        timeout: Request timeout in seconds.

    Returns:
        List of structured error log dicts.
    """
    base_url = extract_base_url(health_url)
    logs_url = f"{base_url}/logs"
    params: Dict[str, Any] = {"level": "ERROR", "limit": limit}
    if since:
        params["since"] = since

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(logs_url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
            return []
    except Exception as exc:
        logger.debug("Could not fetch remote logs from %s: %s", logs_url, exc)
        return []
