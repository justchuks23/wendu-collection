from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.catalog.models import Variant


class StockLevel(models.Model):
    variant = models.OneToOneField(
        Variant,
        on_delete=models.CASCADE,
        related_name="stock",
    )
    quantity = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available(self):
        return max(0, self.quantity - self.reserved)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=F("reserved")),
                name="stock_reserved_lte_quantity",
            ),
        ]


class StockMovement(models.Model):
    stock = models.ForeignKey(
        StockLevel,
        on_delete=models.PROTECT,
        related_name="movements",
    )
    delta = models.IntegerField()
    reason = models.CharField(max_length=120)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
