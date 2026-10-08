import os

from .base import *  # noqa: F403

DEBUG = os.getenv("DEBUG", "True").lower() == "true"
if not SECRET_KEY:  # noqa: F405
    raise RuntimeError("Set SECRET_KEY in local environment")
if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
