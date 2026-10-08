import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.inventory.models import StockLevel, StockMovement
from apps.orders.models import Order
from .gateways.base import PaymentConfigurationError, PaymentProviderError
from .gateways.flutterwave import FlutterwaveGateway
from .gateways.paystack import PaystackGateway
from .models import Payment, WebhookEvent


def configured_provider():
    provider = getattr(settings, "PAYMENT_PROVIDER", "").lower()
    if provider in {"paystack", "flutterwave"}:
        return provider
    raise PaymentConfigurationError(
        "Choose PAYMENT_PROVIDER=paystack or flutterwave."
    )


def gateway_for(provider=None):
    provider = provider or configured_provider()
    if provider == "paystack":
        return PaystackGateway(getattr(settings, "PAYSTACK_SECRET_KEY", ""))
    if provider == "flutterwave":
        return FlutterwaveGateway(
            getattr(settings, "FLUTTERWAVE_SECRET_KEY", ""),
            getattr(settings, "FLUTTERWAVE_SECRET_HASH", ""),
        )
    raise PaymentConfigurationError("Unsupported payment provider.")


def checkout_callback(order):
    base_url = getattr(settings, "PAYMENT_RETURN_BASE_URL", "").rstrip("/")
    parsed_url = urlparse(base_url)
    invalid_url = (
        not parsed_url.netloc
        or parsed_url.path not in ("", "/")
        or parsed_url.query
        or parsed_url.fragment
        or parsed_url.scheme not in ("http", "https")
        or parsed_url.username
        or parsed_url.password
    )
    if invalid_url:
        raise PaymentConfigurationError(
            "Set PAYMENT_RETURN_BASE_URL to the public storefront origin."
        )
    if not settings.DEBUG and parsed_url.scheme != "https":
        raise PaymentConfigurationError(
            "Payment callback URL must use HTTPS in production."
        )
    if base_url not in settings.FRONTEND_ORIGINS:
        raise PaymentConfigurationError(
            "PAYMENT_RETURN_BASE_URL must match an allowlisted FRONTEND_ORIGINS entry."
        )
    return f"{base_url}/pay/{order.public_id}"


def provider_ready(provider=None):
    try:
        provider = provider or configured_provider()
        gateway_for(provider)
        callback_url = getattr(settings, "PAYMENT_RETURN_BASE_URL", "")
        parsed_url = urlparse(callback_url)
        allowed_origins = {
            origin.rstrip("/") for origin in settings.FRONTEND_ORIGINS
        }
        return bool(
            parsed_url.netloc
            and parsed_url.path in ("", "/")
            and not parsed_url.query
            and not parsed_url.fragment
            and not parsed_url.username
            and not parsed_url.password
            and callback_url.rstrip("/") in allowed_origins
            and parsed_url.scheme in (("http", "https") if settings.DEBUG else ("https",))
        )
    except PaymentProviderError:
        return False


@transaction.atomic
def initialize_payment(*, user, order_public_id):
    order = (
        Order.objects.select_for_update()
        .filter(public_id=order_public_id, user=user)
        .first()
    )
    if not order:
        raise ValidationError("Order not found.")
    if order.status != Order.Status.PENDING or order.expires_at <= timezone.now():
        raise ValidationError("This order is no longer payable.")
    if not user.email:
        raise ValidationError("Add an email address to your account before paying.")

    provider = configured_provider()
    gateway = gateway_for(provider)
    callback_url = checkout_callback(order)
    amount_minor = int(order.total * 100)
    if amount_minor < 1 or order.currency != "NGN":
        raise ValidationError("Order amount or currency is not supported.")

    payment = Payment.objects.filter(
        order=order,
        provider=provider,
        status=Payment.Status.PENDING,
        checkout_url__gt="",
    ).first()
    if payment:
        return payment

    payment = Payment.objects.create(
        order=order,
        provider=provider,
        reference=f"w{uuid.uuid4().hex}",
        amount_minor=amount_minor,
        currency=order.currency,
    )
    try:
        checkout_url = gateway.initialize(
            reference=payment.reference,
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            email=user.email,
            callback_url=callback_url,
        )
        parsed_url = urlparse(checkout_url)
        if (
            parsed_url.scheme != "https"
            or parsed_url.hostname != gateway.checkout_host
            or parsed_url.username
            or parsed_url.password
        ):
            raise PaymentProviderError(
                "Payment provider returned an untrusted checkout URL."
            )
        payment.checkout_url = checkout_url
        payment.save(update_fields=["checkout_url", "updated_at"])
    except Exception:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
        raise
    return payment


def _release_order_reservation(order, reason):
    items = list(order.items.all().order_by("sku"))
    skus = [item.sku for item in items]
    stocks = {
        stock.variant.sku: stock
        for stock in StockLevel.objects.select_for_update()
        .filter(variant__sku__in=skus)
        .select_related("variant")
        .order_by("variant_id")
    }
    for item in items:
        stock = stocks.get(item.sku)
        if not stock or not stock.reserved:
            continue
        released = min(stock.reserved, item.quantity)
        stock.reserved -= released
        stock.save(update_fields=["reserved", "updated_at"])
        StockMovement.objects.create(
            stock=stock,
            delta=released,
            reason=f"{reason} {order.public_id}",
        )


def apply_verified_payment(*, payment, verification):
    is_valid = (
        verification.get("successful")
        and verification.get("reference") == payment.reference
        and str(verification.get("amount_minor")) == str(payment.amount_minor)
        and verification.get("currency") == payment.currency
    )
    if not is_valid:
        raise PaymentProviderError("Payment could not be verified.")

    with transaction.atomic():
        payment = Payment.objects.select_for_update().select_related("order").get(
            pk=payment.pk
        )
        if payment.status == Payment.Status.SUCCEEDED:
            return payment.order, False

        order = Order.objects.select_for_update().get(pk=payment.order_id)
        if order.status != Order.Status.PENDING or order.expires_at <= timezone.now():
            payment.status = Payment.Status.REFUND_REQUIRED
            payment.provider_transaction_id = str(
                verification.get("transaction_id", "")
            )
            payment.save(
                update_fields=["status", "provider_transaction_id", "updated_at"]
            )
            if order.status == Order.Status.PENDING:
                _release_order_reservation(
                    order, "Expired payment reservation released"
                )
                order.status = Order.Status.CANCELLED
                order.save(update_fields=["status"])
            return order, False

        items = list(order.items.all().order_by("sku"))
        skus = [item.sku for item in items]
        stocks = {
            stock.variant.sku: stock
            for stock in StockLevel.objects.select_for_update()
            .filter(variant__sku__in=skus)
            .select_related("variant")
            .order_by("variant_id")
        }
        for item in items:
            stock = stocks.get(item.sku)
            if (
                not stock
                or stock.reserved < item.quantity
                or stock.quantity < item.quantity
            ):
                raise PaymentProviderError(
                    "Reserved inventory could not be committed; order requires review."
                )

        for item in items:
            stock = stocks[item.sku]
            stock.quantity -= item.quantity
            stock.reserved -= item.quantity
            stock.save(update_fields=["quantity", "reserved", "updated_at"])
            StockMovement.objects.create(
                stock=stock,
                delta=-item.quantity,
                reason=f"Paid order {order.public_id}",
                actor=order.user,
            )

        order.status = Order.Status.PAID
        order.save(update_fields=["status"])
        payment.status = Payment.Status.SUCCEEDED
        payment.provider_transaction_id = str(
            verification.get("transaction_id", "")
        )
        payment.save(
            update_fields=["status", "provider_transaction_id", "updated_at"]
        )
        return order, True


def verify_user_payment(*, user, reference, transaction_id=""):
    payment = (
        Payment.objects.filter(reference=reference, order__user=user)
        .select_related("order")
        .first()
    )
    if not payment:
        raise ValidationError("Payment not found.")
    if payment.status == Payment.Status.SUCCEEDED:
        return payment.order, payment
    if payment.status != Payment.Status.PENDING:
        raise ValidationError("This payment can no longer be verified.")

    gateway = gateway_for(payment.provider)
    verification = gateway.verify(
        reference=payment.reference,
        amount_minor=payment.amount_minor,
        currency=payment.currency,
        transaction_id=transaction_id,
    )
    order, _ = apply_verified_payment(payment=payment, verification=verification)
    payment.refresh_from_db()
    return order, payment


def process_webhook(*, provider, event_type, reference, transaction_id, event_key):
    if WebhookEvent.objects.filter(provider=provider, event_key=event_key).exists():
        return "duplicate"

    payment = (
        Payment.objects.filter(provider=provider, reference=reference)
        .select_related("order")
        .first()
    )
    if not payment:
        return "unknown"
    if payment.status == Payment.Status.SUCCEEDED:
        return "duplicate"

    gateway = gateway_for(provider)
    verification = gateway.verify(
        reference=reference,
        amount_minor=payment.amount_minor,
        currency=payment.currency,
        transaction_id=transaction_id,
    )
    if verification.get("successful"):
        apply_verified_payment(payment=payment, verification=verification)

    try:
        WebhookEvent.objects.create(
            provider=provider,
            event_key=event_key[:180],
            event_type=event_type[:80],
            payment=payment,
            processed_at=timezone.now(),
        )
    except IntegrityError:
        return "duplicate"
    return "processed"
