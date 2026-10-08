from decimal import Decimal, ROUND_HALF_UP


def to_minor_units(amount: Decimal) -> int:
    return int(
        (amount * Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )
