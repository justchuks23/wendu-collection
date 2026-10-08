from django.core.exceptions import ValidationError

from .models import TierPrice, UserPricingTier


def get_price_for(user, variant, qty):
    """Return the server-calculated unit price for a user and variant.

    Approved active tier prices may define quantity breaks. If the user has no
    approved tier price for this variant and quantity, use the catalog price.
    """
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValidationError("Quantity must be a positive whole number.")

    tier = get_approved_tier(user)
    if tier is None:
        return variant.price

    prefetched_prices = getattr(variant, "_approved_tier_prices", None)
    if prefetched_prices is not None:
        return next(
            (price.unit_price for price in prefetched_prices if price.minimum_quantity <= qty),
            variant.price,
        )

    tier_price = (
        TierPrice.objects.filter(
            tier=tier,
            variant=variant,
            minimum_quantity__lte=qty,
        )
        .order_by("-minimum_quantity")
        .values_list("unit_price", flat=True)
        .first()
    )
    return tier_price if tier_price is not None else variant.price


def get_approved_tier(user):
    if not getattr(user, "is_authenticated", False):
        return None

    cache_attribute = "_approved_pricing_tier"
    if hasattr(user, cache_attribute):
        return getattr(user, cache_attribute)

    assignment = (
        UserPricingTier.objects.filter(
            user=user,
            status=UserPricingTier.Status.APPROVED,
            tier__is_active=True,
        )
        .select_related("tier")
        .first()
    )
    tier = assignment.tier if assignment else None
    setattr(user, cache_attribute, tier)
    return tier


def tier_price_prefetch(user, lookup="tier_prices"):
    """Build an optional prefetch for the user’s approved tier prices."""
    from django.db.models import Prefetch

    tier = get_approved_tier(user)
    if tier is None:
        return None
    return Prefetch(
        lookup,
        queryset=TierPrice.objects.filter(tier=tier).order_by("-minimum_quantity"),
        to_attr="_approved_tier_prices",
    )
