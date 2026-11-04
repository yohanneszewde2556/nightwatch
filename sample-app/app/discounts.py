"""Discount code logic -- introduced in v2.

The bug: `DISCOUNT_RATES` maps known codes to their rate.
Unknown or expired codes return None from `dict.get()`, and
`apply_discount` multiplies by `None`, raising TypeError.
About 70% of realistic discount codes will be unknown,
triggering the bug.
"""

# Known discount codes and their rates (fraction off)
DISCOUNT_RATES: dict[str, float] = {
    "SAVE10": 0.10,
    "WELCOME": 0.15,
    "VIP20": 0.20,
}

# Codes that the traffic simulator picks from -- most are unknown
SAMPLE_CODES: list[str] = [
    "SAVE10",      # known -- works
    "WELCOME",     # known -- works
    "EXPIRED50",   # unknown -- triggers bug
    "SUMMER30",    # unknown -- triggers bug
    "BLACKFRI",    # unknown -- triggers bug
    "LOYALTY25",   # unknown -- triggers bug
    "NEWUSER",     # unknown -- triggers bug
    "FLASH15",     # unknown -- triggers bug
    "HOLIDAY10",   # unknown -- triggers bug
    "VIP20",       # known -- works
]


def apply_discount(subtotal: float, code: str) -> float:
    """Apply a discount code to a subtotal.

    Bug: when the code is not in DISCOUNT_RATES, `rate` is None.
    The multiplication `subtotal * rate` then raises TypeError.
    This is intentional -- it simulates a real production bug.
    """
    rate = DISCOUNT_RATES.get(code)
    # BUG: no check for None before arithmetic
    discount_amount = subtotal * rate  # TypeError when rate is None
    return round(discount_amount, 2)
