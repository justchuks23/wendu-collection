import hashlib
import hmac
from urllib.parse import quote

from .base import PaymentConfigurationError, PaymentGateway, PaymentProviderError
from .http import request_json


class PaystackGateway(PaymentGateway):
    base_url = "https://api.paystack.co"
    checkout_host = "checkout.paystack.com"

    def __init__(self, secret):
        if not secret:
            raise PaymentConfigurationError(
                "Paystack is not configured. Add PAYSTACK_SECRET_KEY on the server."
            )
        self.secret = secret

    def initialize(self, *, reference, amount_minor, currency, email, callback_url):
        result = request_json(
            f"{self.base_url}/transaction/initialize",
            secret=self.secret,
            method="POST",
            payload={
                "reference": reference,
                "amount": str(amount_minor),
                "currency": currency,
                "email": email,
                "callback_url": callback_url,
            },
        )
        data = result.get("data") or {}
        if (
            not result.get("status")
            or not data.get("authorization_url")
            or data.get("reference") != reference
        ):
            raise PaymentProviderError("Paystack could not initialize this payment.")
        return data["authorization_url"]

    def verify(self, *, reference, amount_minor, currency, transaction_id=""):
        result = request_json(
            f"{self.base_url}/transaction/verify/{quote(reference, safe='')}",
            secret=self.secret,
        )
        data = result.get("data") or {}
        successful = bool(
            result.get("status")
            and data.get("status") == "success"
            and data.get("reference") == reference
            and str(data.get("amount")) == str(amount_minor)
            and data.get("currency") == currency
        )
        if transaction_id and str(data.get("id")) != str(transaction_id):
            successful = False

        return {
            "successful": successful,
            "reference": data.get("reference", ""),
            "transaction_id": str(data.get("id", "")),
            "amount_minor": data.get("amount"),
            "currency": data.get("currency"),
        }

    def verify_webhook_signature(self, *, raw_body, headers):
        supplied = headers.get("x-paystack-signature", "")
        expected = hmac.new(self.secret.encode(), raw_body, hashlib.sha512).hexdigest()
        return bool(supplied) and hmac.compare_digest(supplied, expected)
