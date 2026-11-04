"""Pydantic v2 models for the demo-shop API."""
from pydantic import BaseModel, field_validator


class Product(BaseModel):
    """A product in the catalog."""

    id: int
    name: str
    price: float
    category: str
    in_stock: bool = True


class CartItem(BaseModel):
    """A single item in a checkout cart."""

    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("quantity must be >= 1")
        return v


class CheckoutRequest(BaseModel):
    """Incoming checkout request."""

    items: list[CartItem]
    discount_code: str | None = None


class CheckoutResponse(BaseModel):
    """Response after processing a checkout."""

    order_id: str
    items_count: int
    subtotal: float
    discount_applied: float
    total: float
    version: str


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str
    version: str
    uptime_seconds: float
    error: str | None = None


class LogEntry(BaseModel):
    """A single structured log entry."""

    timestamp: str
    level: str
    request_id: str
    route: str
    status: int
    latency_ms: float
    version: str
    exception: str | None = None


class DeployRequest(BaseModel):
    """Request to change the deployed version."""

    version: str

    @field_validator("version")
    @classmethod
    def version_must_be_valid(cls, v: str) -> str:
        if v not in ("v1", "v2"):
            raise ValueError('version must be "v1" or "v2"')
        return v


class ChaosRequest(BaseModel):
    """Request to change the chaos mode."""

    mode: str

    @field_validator("mode")
    @classmethod
    def mode_must_be_valid(cls, v: str) -> str:
        if v not in ("none", "slow", "down"):
            raise ValueError('mode must be "none", "slow", or "down"')
        return v


class AdminStateResponse(BaseModel):
    """Current admin-visible state."""

    version: str
    chaos_mode: str
    commit_label: str
