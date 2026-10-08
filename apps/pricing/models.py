from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.catalog.models import Variant


class PricingTier(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TierPrice(models.Model):
    tier = models.ForeignKey(
        PricingTier,
        on_delete=models.CASCADE,
        related_name="prices",
    )
    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
        related_name="tier_prices",
    )
    minimum_quantity = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["tier_id", "variant_id", "minimum_quantity"]
        constraints = [
            models.UniqueConstraint(
                fields=("tier", "variant", "minimum_quantity"),
                name="unique_tier_variant_min_qty",
            ),
            models.CheckConstraint(
                condition=Q(minimum_quantity__gte=1),
                name="tier_price_min_qty_gte_1",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gt=0),
                name="tier_price_positive",
            ),
        ]

    def __str__(self):
        return f"{self.tier} · {self.variant.sku} · {self.minimum_quantity}+"


class UserPricingTier(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pricing_assignment",
    )
    tier = models.ForeignKey(
        PricingTier,
        on_delete=models.PROTECT,
        related_name="user_assignments",
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_pricing_assignments",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "user pricing tier assignment"
        verbose_name_plural = "user pricing tier assignments"

    def __str__(self):
        return f"{self.user} · {self.tier} ({self.get_status_display()})"
