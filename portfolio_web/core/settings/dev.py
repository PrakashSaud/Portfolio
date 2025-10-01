from .base import *  # noqa: F403
from .base import MIDDLEWARE

DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

MIDDLEWARE += ["core.middleware.RateLimitMiddleware"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "DEBUG"},
}
