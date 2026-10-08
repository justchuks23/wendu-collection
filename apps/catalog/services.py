from django.db.models import Prefetch

from apps.pricing.services import tier_price_prefetch
from .models import Product, Variant


def get_saleable_products(user=None):
    """Return active products with their active variants and stock loaded."""
    variant_prefetches = ["stock"]
    tier_prefetch = tier_price_prefetch(user)
    if tier_prefetch is not None:
        variant_prefetches.append(tier_prefetch)
    active_variants = Variant.objects.filter(is_active=True).prefetch_related(
        *variant_prefetches
    )
    return (
        Product.objects.filter(is_active=True, variants__is_active=True)
        .select_related("category")
        .prefetch_related(Prefetch("variants", queryset=active_variants))
        .distinct()
    )
