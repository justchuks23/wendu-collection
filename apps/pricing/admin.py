from django.contrib import admin
from django.utils import timezone

from .models import PricingTier, TierPrice, UserPricingTier


class TierPriceInline(admin.TabularInline):
    model = TierPrice
    extra = 0


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TierPriceInline]


@admin.register(UserPricingTier)
class UserPricingTierAdmin(admin.ModelAdmin):
    list_display = ("user", "tier", "status", "reviewed_by", "reviewed_at")
    list_filter = ("status", "tier")
    search_fields = ("user__username", "user__email", "tier__name")
    readonly_fields = ("reviewed_by", "reviewed_at", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if obj.status == UserPricingTier.Status.PENDING:
            obj.reviewed_by = None
            obj.reviewed_at = None
        else:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
