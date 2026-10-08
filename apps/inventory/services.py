from django.core.exceptions import ValidationError
from django.db import transaction

from .models import StockLevel, StockMovement


@transaction.atomic
def adjust_stock(*, variant, delta, reason, actor=None):
    stock = StockLevel.objects.select_for_update().get(variant=variant)
    if delta == 0 or stock.quantity + delta < stock.reserved:
        raise ValidationError(
            "Stock adjustment would invalidate available inventory."
        )

    stock.quantity += delta
    stock.save(update_fields=["quantity", "updated_at"])
    StockMovement.objects.create(
        stock=stock,
        delta=delta,
        reason=reason[:120],
        actor=actor if getattr(actor, "is_authenticated", False) else None,
    )
    return stock


@transaction.atomic
def reserve(*, variant, quantity):
    if not isinstance(quantity, int) or not 1 <= quantity <= 20:
        raise ValidationError("Choose between 1 and 20 units.")

    stock = StockLevel.objects.select_for_update().get(variant=variant)
    if stock.available < quantity:
        raise ValidationError("Not enough stock is available.")

    stock.reserved += quantity
    stock.save(update_fields=["reserved", "updated_at"])
    return stock
