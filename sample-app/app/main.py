"""Main FastAPI application for demo-shop.

Monitored e-commerce API with in-memory state, structured logging,
chaos injection modes, and background traffic simulation.
"""
import asyncio
import random
import secrets
import time
import traceback
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from app.checkout import process_checkout
from app.config import settings
from app.discounts import SAMPLE_CODES
from app.logs import log_buffer
from app.models import (
    AdminStateResponse,
    ChaosRequest,
    CheckoutRequest,
    CheckoutResponse,
    DeployRequest,
    HealthResponse,
    LogEntry,
    Product,
)
from app.products import get_all_products, get_product
from app.state import state


async def run_traffic_simulator(app: FastAPI) -> None:
    """Simulate realistic user traffic in the background.

    Makes periodic requests to products, health, and checkout endpoints.
    In v2, picks from discount codes, triggering intentional 500 errors
    on roughly 70% of checkouts.
    """
    await asyncio.sleep(0.5)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://demo-shop.local",
    ) as client:
        while True:
            try:
                await asyncio.sleep(settings.TRAFFIC_INTERVAL_SECONDS)
                roll = random.random()

                if roll < 0.40:
                    # Catalog browse
                    await client.get("/products")
                elif roll < 0.65:
                    # Product detail view
                    prod_id = random.randint(1, 8)
                    await client.get(f"/products/{prod_id}")
                elif roll < 0.80:
                    # Health probe
                    await client.get("/health")
                else:
                    # Checkout attempt
                    prod_id = random.randint(1, 8)
                    qty = random.randint(1, 2)
                    payload = {"items": [{"product_id": prod_id, "quantity": qty}]}

                    if state.version == "v2":
                        # Sample codes have 7 unknown out of 10 -> 70% failure
                        payload["discount_code"] = random.choice(SAMPLE_CODES)

                    await client.post("/checkout", json=payload)

            except asyncio.CancelledError:
                break
            except Exception:
                # Keep the background simulator resilient to any transport error
                pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """App lifespan context manager: manages background traffic simulator."""
    traffic_task = None
    if settings.TRAFFIC_ENABLED and settings.TRAFFIC_INTERVAL_SECONDS > 0:
        traffic_task = asyncio.create_task(run_traffic_simulator(app))

    try:
        yield
    finally:
        if traffic_task and not traffic_task.done():
            traffic_task.cancel()
            try:
                await traffic_task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="demo-shop",
    description="Monitored e-commerce API for Nightwatch on-call demo",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def logging_and_chaos_middleware(request: Request, call_next) -> Response:
    """Middleware for request ID injection, chaos latency, and structured logging."""
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    start_time = time.perf_counter()
    path = request.url.path

    # Apply growing latency if chaos mode is slow (exclude admin routes)
    if state.chaos_mode == "slow" and not path.startswith("/admin"):
        delay = state.next_slow_delay()
        await asyncio.sleep(delay)

    try:
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Log request (exclude /logs endpoint itself to prevent buffer recursion)
        if path != "/logs":
            level = "INFO"
            if response.status_code >= 500:
                level = "ERROR"
            elif response.status_code >= 400:
                level = "WARN"

            log_buffer.add(
                level=level,
                request_id=request_id,
                route=path,
                status=response.status_code,
                latency_ms=latency_ms,
                version=state.version,
                exception=None,
            )

        response.headers["X-Request-ID"] = request_id
        return response

    except Exception:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        tb_str = traceback.format_exc()

        log_buffer.add(
            level="ERROR",
            request_id=request_id,
            route=path,
            status=500,
            latency_ms=latency_ms,
            version=state.version,
            exception=tb_str,
        )

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )


# ============================================================================
# Public Endpoints
# ============================================================================


@app.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse | JSONResponse:
    """Return application health, version label, and uptime.

    Returns HTTP 503 when the app is in the 'down' chaos mode.
    """
    uptime = round(state.uptime_seconds, 2)
    if state.chaos_mode == "down":
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": state.version,
                "uptime_seconds": uptime,
                "error": "Chaos mode: down",
            },
        )

    return HealthResponse(
        status="healthy",
        version=state.version,
        uptime_seconds=uptime,
    )


@app.get("/products", response_model=list[Product])
def list_products() -> list[Product]:
    """Return the e-commerce product catalog."""
    return get_all_products()


@app.get("/products/{product_id}", response_model=Product)
def get_product_by_id(product_id: int) -> Product:
    """Return a single product by ID."""
    product = get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


@app.post("/checkout", response_model=CheckoutResponse)
def checkout(request: CheckoutRequest) -> CheckoutResponse:
    """Process an order checkout.

    Calculates subtotal, applies discount (in v2), and returns order ID.
    Raises ValueError (HTTP 400) if product is not found.
    In v2, unknown discount codes trigger a TypeError (HTTP 500).
    """
    try:
        return process_checkout(request, version=state.version)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Note: TypeError and other exceptions propagate to middleware for traceback capture


@app.get("/logs", response_model=list[LogEntry])
def get_logs(
    level: str | None = Query(None, description="Filter by log level (INFO, WARN, ERROR)"),
    since: str | None = Query(None, description="Filter entries after this ISO timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
) -> list[LogEntry]:
    """Return recent structured JSON logs from the ring buffer."""
    return log_buffer.query(level=level, since=since, limit=limit)


# ============================================================================
# Admin Endpoints (Require X-Admin-Token header)
# ============================================================================


def verify_admin_token(x_admin_token: str | None = Header(None, alias="X-Admin-Token")) -> str:
    """Validate admin authentication token."""
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Token")
    return x_admin_token


@app.get("/admin/state", response_model=AdminStateResponse, dependencies=[Depends(verify_admin_token)])
def get_admin_state() -> AdminStateResponse:
    """Return current deployed version, chaos mode, and commit label."""
    return AdminStateResponse(
        version=state.version,
        chaos_mode=state.chaos_mode,
        commit_label=state.commit_label,
    )


@app.post("/admin/deploy", response_model=AdminStateResponse, dependencies=[Depends(verify_admin_token)])
def deploy_version(payload: DeployRequest) -> AdminStateResponse:
    """Simulate deploying a new version (v1 or v2)."""
    state.deploy(payload.version)
    return AdminStateResponse(
        version=state.version,
        chaos_mode=state.chaos_mode,
        commit_label=state.commit_label,
    )


@app.post("/admin/rollback", response_model=AdminStateResponse, dependencies=[Depends(verify_admin_token)])
def rollback_version() -> AdminStateResponse:
    """Roll back to v1."""
    state.rollback()
    return AdminStateResponse(
        version=state.version,
        chaos_mode=state.chaos_mode,
        commit_label=state.commit_label,
    )


@app.post("/admin/chaos", response_model=AdminStateResponse, dependencies=[Depends(verify_admin_token)])
def set_chaos_mode(payload: ChaosRequest) -> AdminStateResponse:
    """Inject or clear chaos mode ('none', 'slow', 'down')."""
    state.set_chaos(payload.mode)
    return AdminStateResponse(
        version=state.version,
        chaos_mode=state.chaos_mode,
        commit_label=state.commit_label,
    )
