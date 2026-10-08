import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import PaymentProviderError


MAX_RESPONSE_BYTES = 1_000_000


def request_json(url, *, secret, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise PaymentProviderError(
            "Payment provider is temporarily unavailable."
        ) from exc

    if len(body) > MAX_RESPONSE_BYTES:
        raise PaymentProviderError("Payment provider returned an oversized response.")

    try:
        result = json.loads(body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise PaymentProviderError("Payment provider returned an invalid response.") from exc

    if not isinstance(result, dict):
        raise PaymentProviderError("Payment provider returned an invalid response.")
    return result
