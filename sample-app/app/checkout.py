"""Checkout logic for demo-shop.

v1: straightforward total calculation, no discounts.
v2: adds discount code support via discounts.py -- contains a bug.
"""
import uuid
from app.models import CheckoutRequest, CheckoutResponse
from app.products import get_product


def process_checkout(request: CheckoutRequest, version: str) -> CheckoutResponse:
    """Process a checkout request.

    Args:
        request: The checkout request with items and optional discount code.
        version: Current app version ("v1" or "v2").

    Returns:
        CheckoutResponse with order details.

    Raises:
        ValueError: If a product ID is not found in the catalog.
        TypeError: In v2, if an unknown discount code is used (this is the intentional bug).
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
    discount_applied = 0.0

    if version == "v2" and request.discount_code:
        from app.discounts import apply_discount
        discount_applied = apply_discount(subtotal, request.discount_code)

    total = round(max(0.0, subtotal - discount_applied), 2)

    return CheckoutResponse(
        order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        items_count=items_count,
        subtotal=subtotal,
        discount_applied=discount_applied,
        total=total,
        version=version,
    )
