# -*- coding: utf-8 -*-
import sys
import tempfile

import django.db.backends.utils as db_utils
from smart_testing.traceback import SmartTraceback

from smart_testing.cursors import TracebackCursorWrapper

import environ

from .base import *  # noqa

from hubspot import HubSpot

import cloudinary
import redis
from urllib.parse import urlparse

ENVIRONMENT_NAME = "Developement"
ENVIRONMENT_COLOR = "Green"

# La barre de débogage ralentit fortement les pages (elle enregistre chaque requête SQL : environ
# 30 fois plus lent mesuré sur le tableau de bord). Elle est donc facultative :
# définir DEBUG_TOOLBAR=1 dans l'environnement du service web pour l'activer.
USE_DEBUG_TOOLBAR = os.environ.get("DEBUG_TOOLBAR") == "1"

if USE_DEBUG_TOOLBAR:
    INSTALLED_APPS += ("debug_toolbar",)  # noqa
SECRET_KEY = os.environ.get("SECRET_KEY", "secretkey-superhot-12345678")  # noqa
ALLOWED_HOSTS = ["*"]
DEBUG = True

# Derrière le proxy HTTPS local (service "https" de docker-compose.override.yml, https://localhost:8443) :
# Django reçoit du HTTP simple et doit croire l'en-tête X-Forwarded-Proto du proxy, sinon les liens des
# e-mails (confirmation, mot de passe oublié) sont écrits en http:// et refusés par le proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Add colors in logs
LOGGING_COLORED = os.environ.get("LOGGING_COLORED", False)
if LOGGING_COLORED:
    for formatter in LOGGING["formatters"].values():
        formatter["()"] = "colorlog.ColoredFormatter"
        formatter["format"] = "%(log_color)s" + formatter["format"]
        formatter["log_colors"] = {
            "DEBUG": "bold_black",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }
    LOGGING["handlers"]["console"]["formatter"] = "colors"  # noqa

# Enable to display queries as they are executed
DEBUG_QUERIES = os.environ.get("DEBUG_QUERIES", False)
if DEBUG_QUERIES:
    LOGGING["loggers"]["django.db.backends"] = {
        "handlers": ["console"],
        "propagate": False,
        "level": "DEBUG",
    }
    LOGGING["handlers"]["console"]["level"] = "DEBUG"

# Force all logger to console
for logger in LOGGING["loggers"].values():  # noqa
    logger["handlers"] = ["console"]
    logger["propagate"] = False

# LOGGING["loggers"][""]["handlers"] = ["console"]

# Middlewares

if USE_DEBUG_TOOLBAR:
    MIDDLEWARE = (
        tuple(
            ["debug_toolbar.middleware.DebugToolbarMiddleware"],
        )
        + MIDDLEWARE
    )

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda x: True,
    # Replié au démarrage : déplié, il recouvre le coin supérieur droit et intercepte des clics
    "SHOW_COLLAPSED": True,
}

# skip captcha tests in dev
SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

try:
    from .local import *  # noqa
except ImportError:
    pass

env = environ.Env()

environ.Env.read_env(os.path.join(BASE_DIR, "settings/.env"))

# Valeurs lues dans mixity/settings/.env (fichier ignoré par git), jamais dans le code.
# base.py est exécuté avant la lecture du .env : on les relit ici.
GOOGLE_API_KEY = env("GOOGLE_API_KEY", default="")
BLOG_API_KEY = env("BLOG_API_KEY", default="")
BLOG_API_URL = "https://blog.mixity.io/ghost/api/v3/content/posts/?key=" + BLOG_API_KEY
GOOGLECHAT_WEBHOOK_URL = env("GOOGLECHAT_WEBHOOK_URL", default="")
GOOGLECHAT_LOGENTRIES_WEBHOOK_URL = env("GOOGLECHAT_LOGENTRIES_WEBHOOK_URL", default="")

# Fichiers : enregistrés sur le disque ; ceux qui n'y sont pas (base copiée depuis la
# production) sont affichés depuis le compte Cloudinary public, sans clé d'API.
DEFAULT_FILE_STORAGE = "mixity.storage_dev.LocalOrCloudinaryStorage"
cloudinary.config(cloud_name=env("CLOUDINARY_CLOUD_NAME", default="mixity"), secure=True)

STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
stripe.api_key = STRIPE_SECRET_KEY
STRIPE_ENDPOINT_SECRET = env("STRIPE_ENDPOINT_SECRET", default="")
STRIPE_PRICE_ID_UNDER_50 = env("STRIPE_PRICE_ID_UNDER_50", default="")
STRIPE_PRICE_ID_OVER_50 = env("STRIPE_PRICE_ID_OVER_50", default="")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = env("EMAIL_HOST", default="mailhog")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_PORT = env("EMAIL_PORT", default="1025")

ENVIRONMENT_DOMAIN = "localhost:8080"

HUBSPOT_API_CLIENT = HubSpot(api_key=env("HUBSPOT_API_KEY", default=""))
DEEPL_API_KEY = env("DEEPL_API_KEY", default="")
OPEN_AI_API_KEY = env("OPEN_AI_API_KEY", default="")

# Better traceback
sys.excepthook = SmartTraceback(
    hide_external_files=True,
    absolute_paths=False,
    verbose_level=1,
    call_pdb=False,
    root=None,
)
db_utils.CursorDebugWrapper = TracebackCursorWrapper

# REDIS

RQ_QUEUES["default"]["SSL"] = False


NAMSOR_API_KEY = env("NAMSOR_API_KEY", default="")
SEGMENT_KEY = env("SEGMENT_KEY", default="")

WEBFLOW_COLLECTION_ID = env("WEBFLOW_COLLECTION_ID", default="")
WEBFLOW_API_KEY = env("WEBFLOW_API_KEY", default="")

HUBSPOT_API_KEY = env("HUBSPOT_API_KEY", default="")

EMAIL_ENCRYPTION_KEY = env(
    "EMAIL_ENCRYPTION_KEY", default="czv37e6zzIOINs0QNBCMo1biYKpe2SyAZlVH5bO7AH8="
)

ADP_CREDENTIALS_ENCRYPTION_KEY = env(
    "ADP_CREDENTIALS_ENCRYPTION_KEY", default="bFLnTobVJeFRdYeC3ZImtTF5"
)

ADP_CERTIFICATE = env(
    "ADP_CERTIFICATE",
    default="LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUZkekNDQkYrZ0F3SUJBZ0lSQUpVM3VwaWh5Q2xYckp3TElpd1JpcnN3RFFZSktvWklodmNOQVFFTEJRQXcKZ2NneEN6QUpCZ05WQkFZVEFsVlRNU2d3SmdZRFZRUUtFeDlCZFhSdmJXRjBhV01nUkdGMFlTQlFjbTlqWlhOegphVzVuTENCSmJtTXVNUmN3RlFZRFZRUUxFdzVYWldJZ1ZHbGxjaUJIY205MWNERTFNRE1HQTFVRUN4TXNLRU1wCklESXdNVFlnUVVSUUxDQkpibU11SUMwZ1JtOXlJR0YxZEdodmNtbDZaV1FnZFhObElHOXViSGt4UHpBOUJnTlYKQkFNVE5rRjFkRzl0WVhScFl5QkVZWFJoSUZCeWIyTmxjM05wYm1jZ1FYQndiR2xqWVhScGIyNGdVMlZ5ZG1sagpaWE1nUTBFZ0xTQkhNekFlRncweU16QTJNakF3TURBd01EQmFGdzB5TlRBMk1Ua3lNelU1TlRsYU1Ib3hIVEFiCkJna3Foa2lHOXcwQkNRRVdEblJsWTJoQWJXbDRhWFI1TG1Odk1ROHdEUVlEVlFRS0V3Wk5hWGhwZEhreEdUQVgKQmdOVkJBZ1RFRXh2YVhKbElFRjBiR0Z1ZEdseGRXVXhEekFOQmdOVkJBY1RCazVoYm5SbGN6RUxNQWtHQTFVRQpCaE1DUmxJeER6QU5CZ05WQkFNVEJrMXBlR2wwZVRDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDCkFRb0NnZ0VCQU1rd1hxc3htV1Y4QjV2R1A5RjZNZXE1VW40RHA2OCtWSFJsdUJrTEh2MDJYMElUekd1RmoyaGgKUDJmbmJoRjFEanBkSXdxLzN1dkpWbU45VE5qNC9ESnFjYmxvWWhsL1ByU3JZdDNrS3k3YmI5S0plaWwzbXV4ZgpVY09ESm40bSszS1ZKandBQkw3QVRLdFZTOXZrVGprY1ZQam13YTZGRkRQWHRYNVBISjFjOTl2aUY3cHk3TGZHCnJMZU5jMWRGYWVySEJISGluOVM3bTVCSzRjMjZoQUlCZVlGUFl5YW9MMkxqNUtXTVBBeW5mcjNMZVJ5L1VTZE0KY1JobzBYNTE1VmwxN0h3SU9HclJIU1VNYWovNndGaGUxL1RvZU9wYnpXaWFxOS9pY2x5bzc3L2dJTTlpaERGWgp6by9MT3JHZXRLZW5sNzlyajFUdTAyYyt2dGpVWlpNQ0F3RUFBYU9DQWFjd2dnR2pNQjhHQTFVZEl3UVlNQmFBCkZLNWVyRFhnalJBWlMwa2tJc1BKQkZoYko3YkNNQjBHQTFVZERnUVdCQlRaQmFxMDlLOEVsOGJqMEJoSXRXbmIKc1RnUHB6QU9CZ05WSFE4QkFmOEVCQU1DQjRBd0RBWURWUjBUQVFIL0JBSXdBREFmQmdOVkhTVUVHREFXQmdncgpCZ0VGQlFjREFnWUtLd1lCQkFHQ054UUNBakE5QmdOVkhTQUVOakEwTURJR0NTc0dBUVFCZzNRTUFUQWxNQ01HCkNDc0dBUVVGQndJQkZoZG9kSFJ3Y3pvdkwyTndjeTVoWkhBdVkyOXRMME5RVXpCWkJnTlZIUjhFVWpCUU1FNmcKVEtCS2hraG9kSFJ3T2k4dlkzSnNWMU11WVdSd0xtTnZiUzlCZFhSdmJXRjBhV05FWVhSaFVISnZZMlZ6YzJsdQpaMEZ3Y0d4cFkyRjBhVzl1VTJWeWRtbGpaWE5EUVMxSE15NWpjbXd3Z1ljR0NDc0dBUVVGQndFQkJIc3dlVEJVCkJnZ3JCZ0VGQlFjd0FvWklhSFIwY0RvdkwyTnlkRmRUTG1Ga2NDNWpiMjB2UVhWMGIyMWhkR2xqUkdGMFlWQnkKYjJObGMzTnBibWRCY0hCc2FXTmhkR2x2YmxObGNuWnBZMlZ6UTBFdFJ6TXVZM0owTUNFR0NDc0dBUVVGQnpBQgpoaFZvZEhSd09pOHZiMk56Y0ZkVExtRmtjQzVqYjIwd0RRWUpLb1pJaHZjTkFRRUxCUUFEZ2dFQkFPdkxjWnd4CldpbDRmM041RC9UajVDQytMd2NPOWtGMVAvVk1uYXp4KzhuRlgrcXNlMHJwMHNPVXFqSHBwdmpodFp1MVh1N0cKSGJUcXYya003YkpwMkwxUjdKV05TSktzUXZKVDZyMDNRMS9hYWtha253SDhFNkRZVnZCV3B4K0FzeUl0cWtNSApjcjJOMFR4Y0hRZjl4R21TQmdPN2hGN0JxTjVKWG9OdzFkWkxrMkNISml5VmNDUDVEdzJVbkV2OEJ3cHVwQ0Z4Clg5ZnEzeDVzNnFUUFdSclVqazFvSnJrQUphdFpjSVZyTzZaVmlxalZVbEZ6UHpmRWcrcGcrMVh1YmR0aEw5V3oKQnpoL1JKZGc1R1JZRU5rZkRqenA1TTN5Z1FZUkpCREhzbktwUXlaakhJNnpNc09ydnRHYjdGZGUrOG5DdEhoNQowN0IvcDZjaFZMZ0NsMEE9Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0=",
)
if ADP_CERTIFICATE:
    ADP_CERTIFICATE_STR = base64.b64decode(ADP_CERTIFICATE)
    ADP_CERTIFICATE = tempfile.NamedTemporaryFile(delete=False)
    ADP_CERTIFICATE.write(ADP_CERTIFICATE_STR)
    ADP_CERTIFICATE.close()
ADP_PRIVATE_KEY = env(
    "ADP_PRIVATE_KEY",
    default="LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb3dJQkFBS0NBUUVBeVRCZXF6R1paWHdIbThZLzBYb3g2cmxTZmdPbnJ6NVVkR1c0R1FzZS9UWmZRaFBNCmE0V1BhR0UvWitkdUVYVU9PbDBqQ3IvZTY4bFdZMzFNMlBqOE1tcHh1V2hpR1g4K3RLdGkzZVFyTHR0djBvbDYKS1hlYTdGOVJ3NE1tZmliN2NwVW1QQUFFdnNCTXExVkwyK1JPT1J4VStPYkJyb1VVTTllMWZrOGNuVnozMitJWAp1bkxzdDhhc3Q0MXpWMFZwNnNjRWNlS2YxTHVia0VyaHpicUVBZ0Y1Z1U5akpxZ3ZZdVBrcFl3OERLZCt2Y3Q1CkhMOVJKMHh4R0dqUmZuWGxXWFhzZkFnNGF0RWRKUXhxUC9yQVdGN1g5T2g0Nmx2TmFKcXIzK0p5WEtqdnYrQWcKejJLRU1Wbk9qOHM2c1o2MHA2ZVh2MnVQVk83VFp6NisyTlJsa3dJREFRQUJBb0lCQUFEeTFtOXVNMi8wRHNFZwpSU3JDcmJ1U2xoMzcvRzFxR05IWHJPK0pTdU1jdjRRN1BhcUFIYlg3UjJaQkJCYlcrM013L3pwTXYwdFRUckgzClpFWmRuaXJLcjdDVkdtbE9YVWhTeW91TFNOeldzZ2RIR0tsYlpBS2JUSEpraXVqclhDSWxLK0g2aWdzd011eFgKNFp5dXplT2RDNVdFMlFMdW83Sys0Sjh3MWt5em9sN2cxT3dzY0NYc283eVJYcS9sKzRtd1FMUmdDbWI3VTQ2UgpCTzF5dE83STZQTjg5ajJtNlI4V2N4ZkVaTVhmc1dGQmkyOS81QkZtRzhTcEpYOXN4U041QmMyZi91WDJKMTZYCkZ6bnlkRVZDMlZaK0NCK2IrNk1HK0hhZWYwb3l0bGxocUxHNmRCNElseE1uVnUwN3BwVy9ZY3RWTDFMdlVhYXQKNlR4YWUza0NnWUVBNzR0QmY1VzZhMEUxRU9sZTRYUlZMczdhNEpDalVUR2gwVEtQVlpFTzZ6cmtrKzlpS08xMgpnSDl0dUEyc2MvV2xnSHB2V0pKNWNmL1REQUwvQTZtNTN4bU1hT3BYTVY5cUNXeGs1Y2pqWG8rdXFHdVVsNG9XCmVhTHNncmdKYmtMcHgvcTZ0aklUUlZpaStSelE1VFBKNWt5OEwwb1RBbHYzM25ZYkM3MHFpNWNDZ1lFQTF3S1YKS1I5emViVGhiR2tFNzBoSldHRGNFc3BDempSUE1nUEhrTklaZUE5U0kyQktQZHR6VWhtckRCcGU2MzR1aFZqMgplczdFS0tZVjFzYkhTblU4ek9JcEZBUXdMZ1M3VHNGaTU5bng2NHdjT0Yzd3gvMlgrS0dOY1pMQkVNZTV1eWxpCnFVSU43R3h0QW1ZMUZ1R1pUbkI4eFh2OXM4L1dLU00xL3h2bHBXVUNnWUVBalhQQ0hjRWc4Q3oxVlNNNThCQnUKTE5IaDFqSVMvdU04RnZpd1Eyc0JVRTdhbzdEOFdnYS9yMm1RTk50K05vdWNTNTRCR21DRWJwa08yMHo1b2dRYgp5bTZmeDJSNlVLRnpVRlU5ejZNdEFLNEFDVnhkeG82NGJ1T1NuaTVuQTBGb0k3c2ZmbTliaWR1cGdVbE80Y29QCk0zdWt0SmdkV1l0TmQ0UnV2Q1BjZDhrQ2dZQnEvUU1DRW45Z2lXdytpTWVHMWQ2QlZybEx0RStuMGdteVpvVVEKZ0N0aVBhVnVxd1JtWVdPeDc4bllYT3JzbmI1Q1puRkh6TWw1UEtQVFd0aGlLWkpXbFJkQnVZL0w1bGphS0lxeAp1aGFTVWdiYzJZbnR5amVyNVorL2F2b2RBblZlTjRxN2xIM2ZMbGpULzgzZEUrYzRTK3NhVGNlQmlTTVZGMHRRCkpTNlJyUUtCZ0g4T1BvWHZPeDBCYm43WURaV2lZRTJaQ3ZsbHVHVHpoSEZoRG9HVktyeWZWM0JyZ1cxbU9yUEUKRllWYUQ3TzJEZXFLUnVwbzlwZHRaQ1oxMFdzL3VyWGQ1Q3M4cEpiaWRGSVVwRmhrOWUzd0VaZGJPNEtFY0JZNwptK1RTN0pLUkRqUzFaT1hzU3lwcVAvWXg4Z0sxRkpLODhvOFUxZVZqSVoydEs3QVdxQkRRCi0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg==",
)
if ADP_PRIVATE_KEY:
    ADP_PRIVATE_KEY_STR = base64.b64decode(ADP_PRIVATE_KEY)
    ADP_PRIVATE_KEY = tempfile.NamedTemporaryFile(delete=False)
    ADP_PRIVATE_KEY.write(ADP_PRIVATE_KEY_STR)
    ADP_PRIVATE_KEY.close()

# En local, le worker joint l'application via le conteneur web.
PDF_RENDER_BASE_URL = os.environ.get("PDF_RENDER_BASE_URL", "http://web:8000/")
