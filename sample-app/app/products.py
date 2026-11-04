"""Hardcoded product catalog for the demo-shop."""
from app.models import Product


PRODUCT_CATALOG: dict[int, Product] = {
    1: Product(id=1, name="Wireless Mouse", price=29.99, category="Electronics"),
    2: Product(id=2, name="Mechanical Keyboard", price=89.99, category="Electronics"),
    3: Product(id=3, name="USB-C Hub", price=34.99, category="Electronics"),
    4: Product(id=4, name="Laptop Stand", price=49.99, category="Accessories"),
    5: Product(id=5, name="Noise-Cancelling Headphones", price=149.99, category="Electronics"),
    6: Product(id=6, name="Webcam HD", price=59.99, category="Electronics"),
    7: Product(id=7, name="Desk Lamp", price=39.99, category="Home Office"),
    8: Product(id=8, name="Cable Management Kit", price=19.99, category="Accessories"),
}


def get_all_products() -> list[Product]:
    """Return all products in the catalog."""
    return list(PRODUCT_CATALOG.values())


def get_product(product_id: int) -> Product | None:
    """Return a single product by ID, or None if not found."""
    return PRODUCT_CATALOG.get(product_id)
