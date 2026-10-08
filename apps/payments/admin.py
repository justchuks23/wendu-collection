from django.contrib import admin

from .models import Payment, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "order",
        "provider",
        "amount_minor",
        "currency",
        "status",
        "created_at",
    )
    list_filter = ("provider", "status", "created_at")
    search_fields = ("reference", "order__public_id", "provider_transaction_id")
    readonly_fields = tuple(field.name for field in Payment._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("payments.view_payment") or request.user.has_perm(
            "payments.change_payment"
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_type", "payment", "received_at", "processed_at")
    list_filter = ("provider", "event_type", "received_at")
    readonly_fields = tuple(field.name for field in WebhookEvent._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm(
            "payments.view_webhookevent"
        ) or request.user.has_perm("payments.change_webhookevent")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
