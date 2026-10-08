import hashlib
import json
import logging

from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .gateways.base import PaymentConfigurationError, PaymentProviderError
from .models import Payment
from .services import (
    configured_provider,
    gateway_for,
    initialize_payment,
    process_webhook,
    provider_ready,
    verify_user_payment,
)

logger = logging.getLogger(__name__)
MAX_WEBHOOK_BYTES = 1_000_000


class PaymentStatusView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            provider = configured_provider()
        except PaymentConfigurationError:
            provider = ""
        return Response(
            {"provider": provider, "configured": provider_ready(provider or None)}
        )


class PaymentInitializeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment_init"

    def post(self, request):
        order_id = request.data.get("order_id", "")
        try:
            payment = initialize_payment(
                user=request.user,
                order_public_id=order_id,
            )
        except (PaymentConfigurationError, PaymentProviderError) as exc:
            return Response({"detail": str(exc)}, status=503)
        except ValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=400)

        return Response(
            {
                "provider": payment.provider,
                "reference": payment.reference,
                "authorization_url": payment.checkout_url,
                "amount": str(payment.order.total),
                "currency": payment.currency,
            }
        )


class PaymentVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment_verify"

    def post(self, request):
        reference = request.data.get("reference", "")
        transaction_id = str(request.data.get("transaction_id", ""))[:80]
        if not reference or len(reference) > 64:
            return Response({"detail": "Invalid payment reference."}, status=400)

        try:
            order, payment = verify_user_payment(
                user=request.user,
                reference=reference,
                transaction_id=transaction_id,
            )
        except PaymentConfigurationError as exc:
            return Response({"detail": str(exc)}, status=503)
        except PaymentProviderError as exc:
            return Response({"detail": str(exc)}, status=502)
        except ValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=400)

        if payment.status == Payment.Status.REFUND_REQUIRED:
            return Response(
                {
                    "detail": (
                        "Payment succeeded after the stock reservation expired. "
                        "Contact support for a refund."
                    ),
                    "status": payment.status,
                },
                status=409,
            )
        if payment.status != Payment.Status.SUCCEEDED:
            return Response(
                {
                    "detail": "Payment is not complete yet.",
                    "status": payment.status,
                },
                status=409,
            )

        return Response(
            {
                "status": "paid",
                "order_id": str(order.public_id),
                "reference": payment.reference,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class PaymentWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment_webhook"

    def post(self, request, provider):
        try:
            gateway = gateway_for(provider)
        except PaymentConfigurationError:
            return Response(status=503)

        raw_body = request.body
        if len(raw_body) > MAX_WEBHOOK_BYTES:
            return Response(status=413)
        content_type = request.headers.get("content-type", "").lower()
        if not content_type.startswith("application/json"):
            return Response(status=415)
        if not gateway.verify_webhook_signature(
            raw_body=raw_body,
            headers=request.headers,
        ):
            logger.warning(
                "Payment webhook signature rejected",
                extra={"provider": provider},
            )
            return Response(status=401)

        try:
            payload = json.loads(raw_body)
        except (ValueError, UnicodeDecodeError):
            return Response(status=400)
        if not isinstance(payload, dict):
            return Response(status=400)

        data = payload.get("data") or {}
        if not isinstance(data, dict):
            return Response(status=400)
        event_type = str(payload.get("event") or payload.get("type") or "")
        reference = str(data.get("reference") or data.get("tx_ref") or "")
        transaction_id = str(data.get("id") or "")
        if not reference or not transaction_id:
            return Response(status=400)

        event_data = f"{event_type}:{reference}:{transaction_id}".encode()
        event_key = hashlib.sha256(event_data).hexdigest()
        try:
            result = process_webhook(
                provider=provider,
                event_type=event_type,
                reference=reference,
                transaction_id=transaction_id,
                event_key=event_key,
            )
        except PaymentProviderError:
            return Response(status=503)
        except Exception:
            logger.exception(
                "Payment webhook processing failed",
                extra={"provider": provider},
            )
            return Response(status=503)

        return Response({"received": True, "result": result}, status=200)
