import django_heroku
from .base import *  # noqa
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from hubspot import HubSpot

SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENV = os.getenv("SENTRY_ENV")

ENVIRONMENT_NAME = SENTRY_ENV


if ENVIRONMENT_NAME.lower() == "staging":
    ENVIRONMENT_COLOR = "Orange"
    ENVIRONMENT_DOMAIN = "staging.mixity.co"
    DEBUG = bool(int(os.environ.get("DEBUG", "0")))
    if DEBUG:
        INSTALLED_APPS += ("debug_toolbar",)
        MIDDLEWARE = ("debug_toolbar.middleware.DebugToolbarMiddleware",) + MIDDLEWARE
        DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda x: True}
else:
    ENVIRONMENT_COLOR = "Red"
    ENVIRONMENT_DOMAIN = "www.app.mixity.co"
    DEBUG = False

SENTRY_TRACE_SAMPLE_RATE = float(os.getenv("SENTRY_TRACE_SAMPLE_RATE", 0.2))

# Sentry
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[DjangoIntegration()],
    environment=SENTRY_ENV,
    send_default_pii=True,
    release=VERSION,
    traces_sample_rate=SENTRY_TRACE_SAMPLE_RATE,  # Warning: this must be lowered if performances are deteriorating
)

# Security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_HTTPONLY = True
ALLOWED_HOSTS = ["www.app.mixity.co"]
BASICAUTH_USERNAME = os.getenv("BASICAUTH_USERNAME")
BASICAUTH_PASSWORD = os.getenv("BASICAUTH_PASSWORD")
# if BASICAUTH_USERNAME and BASICAUTH_PASSWORD:
#    MIDDLEWARE = (
#        'mixity.middlewares.BasicAuthMiddleware',
#    ) + MIDDLEWARE


# Suppose we are using HTTPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
SECURE_SSL_REDIRECT = True
MEDIA_ACCEL_REDIRECT = False

# Activate Django-Heroku.
django_heroku.settings(locals())

# Mails
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = os.getenv("SENDGRID_API_KEY")
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Medias
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
MEDIA_URL = "/media/"
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# analytics
GOOGLE_ANALYTICS_KEY = os.environ.get("GOOGLE_ANALYTICS_KEY")
GTAG = os.environ.get("GTAG")

# hotjar
HOTJAR_SCRIPT = os.environ.get("HOTJAR_SCRIPT")

# crisp
CRISP_ID = os.environ.get("CRISP_ID")

# screeb
SCREEB_KEY = os.environ.get("SCREEB_KEY")

# user guiding
USER_GUIDING_KEY = os.environ.get("USER_GUIDING_KEY")

STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY
STRIPE_ENDPOINT_SECRET = os.environ.get("STRIPE_ENDPOINT_SECRET")
STRIPE_PRICE_ID_UNDER_50 = os.environ.get("STRIPE_PRICE_ID_UNDER_50")
STRIPE_PRICE_ID_OVER_50 = os.environ.get("STRIPE_PRICE_ID_OVER_50")

HUBSPOT_API_CLIENT = HubSpot(api_key=os.environ.get("HUBSPOT_API_KEY"))
