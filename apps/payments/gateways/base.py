from abc import ABC, abstractmethod


class PaymentProviderError(Exception):
    """Raised when a payment provider request or response cannot be trusted."""


class PaymentConfigurationError(PaymentProviderError):
    """Raised when required server-side payment settings are missing."""


class PaymentGateway(ABC):
    @abstractmethod
    def initialize(self, *, reference, amount_minor, currency, email, callback_url):
        """Create a hosted checkout session and return its URL."""
        ...

    @abstractmethod
    def verify(self, *, reference, amount_minor, currency, transaction_id=""):
        """Verify a transaction with the provider's server API."""
        ...

    @abstractmethod
    def verify_webhook_signature(self, *, raw_body, headers):
        """Validate the signature supplied with a webhook request."""
        ...
