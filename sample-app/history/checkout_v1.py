"""Checkout logic for demo-shop (v1).

Initial version: straightforward total calculation, no discount codes.
"""
import uuid
from app.models import CheckoutRequest, CheckoutResponse
from app.products import get_product


def process_checkout(request: CheckoutRequest, version: str = "v1") -> CheckoutResponse:
    """Process a checkout request without discounts.

    Args:
        request: The checkout request with items.
        version: App version string (default "v1").

    Returns:
        CheckoutResponse with order details.

    Raises:
        ValueError: If a product ID is not found.
    """
    subtotal = 0.0
    items_count = 0

    for item in request.items:
        product = get_product(item.product_id)
        if product is None:
            raise ValueError(f"Product {item.product_id} not found")
        subtotal += product.price * item.quantity
        items_count += item.quantity

    subtotal = round(subtotal, 2)
    total = subtotal

    return CheckoutResponse(
        order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        items_count=items_count,
        subtotal=subtotal,
        discount_applied=0.0,
        total=total,
        version=version,
    )
