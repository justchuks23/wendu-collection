from django import forms
from django.contrib import admin

from .models import StockLevel, StockMovement
from .services import adjust_stock


class StockLevelAdminForm(forms.ModelForm):
    class Meta:
        model = StockLevel
        fields = ("quantity",)

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if self.instance.pk:
            current = StockLevel.objects.select_for_update().get(pk=self.instance.pk)
            if quantity < current.reserved:
                raise forms.ValidationError(
                    "Available stock cannot be reduced below the units reserved "
                    "for pending orders."
                )
        return quantity


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    form = StockLevelAdminForm
    list_display = ("variant", "quantity", "reserved", "updated_at")
    list_filter = ("variant__product__category",)
    search_fields = ("variant__sku", "variant__product__name")
    readonly_fields = ("variant", "reserved", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            raise forms.ValidationError(
                "Stock rows are created with product variants."
            )
        current = StockLevel.objects.get(pk=obj.pk)
        delta = obj.quantity - current.quantity
        if not delta:
            return

        updated = adjust_stock(
            variant=current.variant,
            delta=delta,
            reason="Admin inventory adjustment",
            actor=request.user,
        )
        obj.quantity = updated.quantity
        obj.updated_at = updated.updated_at


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("stock", "delta", "reason", "actor", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "stock__variant__sku",
        "stock__variant__product__name",
        "reason",
    )
    readonly_fields = ("stock", "delta", "reason", "actor", "created_at")

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("inventory.view_stockmovement") or request.user.has_perm(
            "inventory.change_stockmovement"
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
