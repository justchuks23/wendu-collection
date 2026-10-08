from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart
from apps.inventory.models import StockLevel, StockMovement
from apps.pricing.services import get_price_for, tier_price_prefetch
from .models import Order, OrderItem


@transaction.atomic
def create_pending_order(*, user):
    cart = Cart.objects.select_for_update().filter(user=user).first()
    if not cart:
        raise ValidationError("Your cart is empty.")

    cart_items = cart.items.select_related("variant__product").order_by("variant_id")
    tier_prefetch = tier_price_prefetch(user, lookup="variant__tier_prices")
    if tier_prefetch is not None:
        cart_items = cart_items.prefetch_related(tier_prefetch)
    items = list(cart_items)
    if not items:
        raise ValidationError("Your cart is empty.")

    variant_ids = [item.variant_id for item in items]
    stocks = {
        stock.variant_id: stock
        for stock in StockLevel.objects.select_for_update()
        .filter(variant_id__in=variant_ids)
        .order_by("variant_id")
    }

    total = Decimal("0.00")
    unit_prices = {}
    for item in items:
        stock = stocks.get(item.variant_id)
        if (
            not item.variant.is_active
            or not item.variant.product.is_active
            or not stock
            or stock.available < item.quantity
        ):
            raise ValidationError("An item in your cart is no longer available.")
        unit_price = get_price_for(user, item.variant, item.quantity)
        unit_prices[item.pk] = unit_price
        total += unit_price * item.quantity

    order = Order.objects.create(
        user=user,
        total=total,
        expires_at=timezone.now() + timedelta(minutes=30),
    )
    for item in items:
        stock = stocks[item.variant_id]
        stock.reserved += item.quantity
        stock.save(update_fields=["reserved", "updated_at"])
        StockMovement.objects.create(
            stock=stock,
            delta=-item.quantity,
            reason=f"Reserved order {order.public_id}",
            actor=user,
        )
        OrderItem.objects.create(
            order=order,
            sku=item.variant.sku,
            product_name=item.variant.product.name,
            unit_price=unit_prices[item.pk],
            quantity=item.quantity,
        )

    cart.items.all().delete()
    return order


@transaction.atomic
def expire_pending_orders():
    expired_orders = list(
        Order.objects.select_for_update()
        .filter(status=Order.Status.PENDING, expires_at__lte=timezone.now())
        .order_by("pk")
    )

    for order in expired_orders:
        items = list(order.items.all())
        skus = [item.sku for item in items]
        stocks = {
            stock.variant.sku: stock
            for stock in StockLevel.objects.select_for_update()
            .filter(variant__sku__in=skus)
            .select_related("variant")
            .order_by("variant_id")
        }

        for item in items:
            stock = stocks.get(item.sku)
            if not stock:
                continue

            stock.reserved = max(0, stock.reserved - item.quantity)
            stock.save(update_fields=["reserved", "updated_at"])
            StockMovement.objects.create(
                stock=stock,
                delta=item.quantity,
                reason=f"Released expired order {order.public_id}",
            )

        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])

    return len(expired_orders)
