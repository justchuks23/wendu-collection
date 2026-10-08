from django.conf import settings
from django.db import models

from apps.catalog.models import Variant


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("cart", "variant"),
                name="unique_variant_per_cart",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1, quantity__lte=20),
                name="cart_qty_1_to_20",
            ),
        ]
