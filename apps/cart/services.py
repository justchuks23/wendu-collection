from django.db import transaction

from apps.catalog.models import Variant
from apps.inventory.models import StockLevel
from apps.pricing.services import tier_price_prefetch
from .models import Cart, CartItem

MAX_CART_QUANTITY = 20


class CartOperationError(Exception):
    """Base exception for cart operations that cannot be completed."""

    status_code = 400


class CartVariantNotFound(CartOperationError):
    status_code = 404


class CartItemNotFound(CartOperationError):
    status_code = 404


class CartQuantityUnavailable(CartOperationError):
    status_code = 409


class InvalidCartQuantity(CartOperationError):
    status_code = 400


def get_cart_items(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    prefetches = ["variant__stock"]
    tier_prefetch = tier_price_prefetch(user, lookup="variant__tier_prices")
    if tier_prefetch is not None:
        prefetches.append(tier_prefetch)
    return cart.items.select_related("variant__product").prefetch_related(*prefetches)


@transaction.atomic
def add_item(*, user, variant_public_id, quantity):
    _validate_quantity(quantity)

    variant = (
        Variant.objects.select_related("product")
        .filter(
            public_id=variant_public_id,
            is_active=True,
            product__is_active=True,
        )
        .first()
    )
    if variant is None:
        raise CartVariantNotFound("Saleable product variant not found.")

    cart, _ = Cart.objects.select_for_update().get_or_create(user=user)
    stock = StockLevel.objects.select_for_update().filter(variant=variant).first()
    if stock is None:
        raise CartVariantNotFound("Inventory is not available for this variant.")

    item = CartItem.objects.filter(cart=cart, variant=variant).first()
    current_quantity = item.quantity if item else 0
    new_quantity = current_quantity + quantity
    if new_quantity > MAX_CART_QUANTITY or new_quantity > stock.available:
        raise CartQuantityUnavailable("Requested quantity is unavailable.")

    if item is None:
        item = CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=new_quantity,
        )
    else:
        item.quantity = new_quantity
        item.save(update_fields=["quantity"])
    return item


@transaction.atomic
def update_item(*, user, item_id, quantity):
    _validate_quantity(quantity)

    cart = Cart.objects.select_for_update().filter(user=user).first()
    if cart is None:
        raise CartItemNotFound("Cart item not found.")

    item = (
        CartItem.objects.select_for_update()
        .select_related("variant")
        .filter(pk=item_id, cart=cart)
        .first()
    )
    if item is None:
        raise CartItemNotFound("Cart item not found.")

    stock = StockLevel.objects.select_for_update().filter(variant=item.variant).first()
    if stock is None:
        raise CartVariantNotFound("Inventory is not available for this variant.")
    if quantity > stock.available:
        raise CartQuantityUnavailable("Requested quantity is unavailable.")

    item.quantity = quantity
    item.save(update_fields=["quantity"])
    return item


@transaction.atomic
def remove_item(*, user, item_id):
    cart = Cart.objects.select_for_update().filter(user=user).first()
    if cart is not None:
        CartItem.objects.filter(pk=item_id, cart=cart).delete()


def _validate_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise InvalidCartQuantity("Quantity must be a whole number.")
    if not 1 <= quantity <= MAX_CART_QUANTITY:
        raise InvalidCartQuantity(
            f"Quantity must be between 1 and {MAX_CART_QUANTITY}."
        )
