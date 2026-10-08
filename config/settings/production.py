import os

from .base import *  # noqa: F403

DEBUG = False

if not SECRET_KEY or not os.getenv("JWT_SIGNING_KEY"):  # noqa: F405
    raise RuntimeError("SECRET_KEY and JWT_SIGNING_KEY required")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:  # noqa: F405
    raise RuntimeError("Set explicit ALLOWED_HOSTS")
if not FRONTEND_ORIGINS or not CSRF_TRUSTED_ORIGINS:  # noqa: F405
    raise RuntimeError("Set explicit frontend and CSRF origins")
if not os.getenv("POSTGRES_PASSWORD"):
    raise RuntimeError("POSTGRES_PASSWORD required")

DATABASES["default"]["OPTIONS"]["sslmode"] = os.getenv(  # noqa: F405
    "DATABASE_SSLMODE",
    "require",
)
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "3600"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"

if PAYMENT_PROVIDER not in {"paystack", "flutterwave"}:  # noqa: F405
    raise RuntimeError("Set PAYMENT_PROVIDER to paystack or flutterwave")
allowed_frontend_origins = {origin.rstrip("/") for origin in FRONTEND_ORIGINS}  # noqa: F405
if (
    not PAYMENT_RETURN_BASE_URL.startswith("https://")  # noqa: F405
    or PAYMENT_RETURN_BASE_URL.rstrip("/") not in allowed_frontend_origins  # noqa: F405
):
    raise RuntimeError(
        "PAYMENT_RETURN_BASE_URL must be HTTPS and match FRONTEND_ORIGINS"
    )
if PAYMENT_PROVIDER == "paystack" and not PAYSTACK_SECRET_KEY.startswith("sk_live_"):  # noqa: F405
    raise RuntimeError("Production must use a Paystack live secret key")
if PAYMENT_PROVIDER == "flutterwave" and (
    not FLUTTERWAVE_SECRET_KEY  # noqa: F405
    or "TEST" in FLUTTERWAVE_SECRET_KEY.upper()  # noqa: F405
    or not FLUTTERWAVE_SECRET_HASH  # noqa: F405
):
    raise RuntimeError(
        "Production requires Flutterwave live secret key and webhook hash"
    )
