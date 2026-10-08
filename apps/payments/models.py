from django.db import models

from apps.orders.models import Order


class Payment(models.Model):
    class Provider(models.TextChoices):
        PAYSTACK = "paystack", "Paystack"
        FLUTTERWAVE = "flutterwave", "Flutterwave"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REFUND_REQUIRED = "refund_required", "Refund required"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    provider = models.CharField(max_length=16, choices=Provider.choices)
    reference = models.CharField(max_length=64, unique=True)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="NGN")
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING,
    )
    checkout_url = models.URLField(max_length=600, blank=True)
    provider_transaction_id = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class WebhookEvent(models.Model):
    provider = models.CharField(max_length=16, choices=Payment.Provider.choices)
    event_key = models.CharField(max_length=180)
    event_type = models.CharField(max_length=80, blank=True)
    payment = models.ForeignKey(
        Payment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="webhook_events",
    )
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "event_key"),
                name="unique_provider_webhook_event",
            ),
        ]
