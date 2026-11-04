"""Tests for demo-shop checkout endpoint."""
from fastapi.testclient import TestClient

from app.discounts import SAMPLE_CODES
from app.logs import log_buffer
from app.state import state


def test_checkout_v1_success(client: TestClient) -> None:
    """In v1, checkout with valid items succeeds and calculates total."""
    state.deploy("v1")
    payload = {
        "items": [
            {"product_id": 1, "quantity": 2},  # Wireless Mouse: 29.99 * 2 = 59.98
            {"product_id": 2, "quantity": 1},  # Mechanical Keyboard: 89.99
        ]
    }
    response = client.post("/checkout", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["items_count"] == 3
    assert data["subtotal"] == 149.97
    assert data["discount_applied"] == 0.0
    assert data["total"] == 149.97
    assert data["version"] == "v1"
    assert data["order_id"].startswith("ORD-")


def test_checkout_v1_ignores_discount_code(client: TestClient) -> None:
    """In v1, discount codes are not supported so they are ignored without failure."""
    state.deploy("v1")
    payload = {
        "items": [{"product_id": 1, "quantity": 1}],
        "discount_code": "SAVE10",
    }
    response = client.post("/checkout", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["discount_applied"] == 0.0
    assert data["total"] == 29.99


def test_checkout_invalid_product(client: TestClient) -> None:
    """Checkout with non-existent product ID returns 400 Bad Request."""
    payload = {"items": [{"product_id": 999, "quantity": 1}]}
    response = client.post("/checkout", json=payload)
    assert response.status_code == 400
    assert "Product 999 not found" in response.json()["detail"]


def test_checkout_v2_known_discount_success(client: TestClient) -> None:
    """In v2, a known discount code calculates discount and succeeds."""
    state.deploy("v2")
    payload = {
        "items": [{"product_id": 2, "quantity": 1}],  # Mechanical Keyboard: 89.99
        "discount_code": "SAVE10",  # 10% off
    }
    response = client.post("/checkout", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v2"
    assert data["subtotal"] == 89.99
    assert data["discount_applied"] == 9.00
    assert data["total"] == 80.99


def test_checkout_v2_unknown_discount_fails_with_500_and_traceback(client: TestClient) -> None:
    """In v2, an unknown discount code raises TypeError and returns HTTP 500.

    The structured log entry must contain a real traceback pointing to
    app/checkout.py and apply_discount.
    """
    state.deploy("v2")
    payload = {
        "items": [{"product_id": 1, "quantity": 1}],
        "discount_code": "EXPIRED50",
    }
    response = client.post("/checkout", json=payload)
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]

    # Check that error is in the log buffer with full traceback
    logs = log_buffer.query(level="ERROR", limit=1)
    assert len(logs) == 1
    err_log = logs[0]
    assert err_log.status == 500
    assert err_log.route == "/checkout"
    assert err_log.exception is not None
    assert "TypeError" in err_log.exception
    assert "checkout.py" in err_log.exception
    assert "apply_discount" in err_log.exception


def test_checkout_v2_failure_rate_on_sample_codes(client: TestClient) -> None:
    """In v2, cycling through SAMPLE_CODES yields roughly 70% failure rate (7 of 10 fail)."""
    state.deploy("v2")
    failures = 0
    successes = 0

    for code in SAMPLE_CODES:
        payload = {
            "items": [{"product_id": 1, "quantity": 1}],
            "discount_code": code,
        }
        res = client.post("/checkout", json=payload)
        if res.status_code == 500:
            failures += 1
        elif res.status_code == 200:
            successes += 1

    assert len(SAMPLE_CODES) == 10
    assert failures == 7
    assert successes == 3
    # Exactly 70% failure rate
    assert failures / len(SAMPLE_CODES) == 0.70
