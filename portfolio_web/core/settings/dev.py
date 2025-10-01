from .base import BASE_DIR, INSTALLED_APPS, MIDDLEWARE

DEBUG = True

# -------------------------------------------------------------------
# Email backend (prints to console in development)
# -------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# -------------------------------------------------------------------
# Static & media files (dev only)
# -------------------------------------------------------------------
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------------------------
# Extra apps (already added in base: pages, projects, blog, contact)
# -------------------------------------------------------------------
INSTALLED_APPS += [
    # debugging tools you may want in dev
    "django_extensions",
]

# -------------------------------------------------------------------
# Middleware (add rate-limiting)
# -------------------------------------------------------------------
MIDDLEWARE += [
    "core.middleware.RateLimitMiddleware",  # per-IP rate limiting for /contact
]

# -------------------------------------------------------------------
# Logging (optional: console debug)
# -------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}
