import hmac
from decimal import Decimal, InvalidOperation

from .base import PaymentConfigurationError, PaymentGateway, PaymentProviderError
from .http import request_json


class FlutterwaveGateway(PaymentGateway):
    base_url = "https://api.flutterwave.com/v3"
    checkout_host = "checkout.flutterwave.com"

    def __init__(self, secret, webhook_hash):
        if not secret or not webhook_hash:
            raise PaymentConfigurationError(
                "Flutterwave requires FLUTTERWAVE_SECRET_KEY and "
                "FLUTTERWAVE_SECRET_HASH on the server."
            )
        self.secret = secret
        self.webhook_hash = webhook_hash

    def initialize(self, *, reference, amount_minor, currency, email, callback_url):
        amount = (Decimal(amount_minor) / Decimal(100)).quantize(Decimal("0.01"))
        result = request_json(
            f"{self.base_url}/payments",
            secret=self.secret,
            method="POST",
            payload={
                "tx_ref": reference,
                "amount": str(amount),
                "currency": currency,
                "redirect_url": callback_url,
                "customer": {"email": email},
                "customizations": {"title": "Wendu Studio order"},
            },
        )
        data = result.get("data") or {}
        if result.get("status") != "success" or not data.get("link"):
            raise PaymentProviderError("Flutterwave could not initialize this payment.")
        return data["link"]

    def verify(self, *, reference, amount_minor, currency, transaction_id=""):
        if not transaction_id or not str(transaction_id).isdigit():
            raise PaymentProviderError(
                "Flutterwave transaction ID is required for verification."
            )

        result = request_json(
            f"{self.base_url}/transactions/{int(transaction_id)}/verify",
            secret=self.secret,
        )
        data = result.get("data") or {}
        try:
            actual_minor = int(
                (Decimal(str(data.get("amount"))) * 100).quantize(Decimal("1"))
            )
        except (InvalidOperation, ValueError, TypeError):
            actual_minor = -1

        successful = bool(
            result.get("status") == "success"
            and data.get("status") == "successful"
            and data.get("tx_ref") == reference
            and actual_minor == amount_minor
            and data.get("currency") == currency
            and str(data.get("id")) == str(transaction_id)
        )
        return {
            "successful": successful,
            "reference": data.get("tx_ref", ""),
            "transaction_id": str(data.get("id", "")),
            "amount_minor": actual_minor,
            "currency": data.get("currency"),
        }

    def verify_webhook_signature(self, *, raw_body, headers):
        supplied = headers.get("verif-hash", "")
        return bool(supplied) and hmac.compare_digest(supplied, self.webhook_hash)
