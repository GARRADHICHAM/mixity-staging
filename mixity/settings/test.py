# -*- coding: utf-8 -*-
import sys
import tempfile
import django.db.backends.utils as db_utils
from decouple import config
from smart_testing.cursors import TracebackCursorWrapper
from smart_testing.traceback import SmartTraceback

from .base import *
from hubspot import HubSpot


class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


ENVIRONMENT_NAME = "test"
ENVIRONMENT_COLOR = "blue"

MIGRATION_MODULES = DisableMigrations()

DEBUG = True

SECRET_KEY = "spam-spam-spam-spam"

MEDIA_ROOT = tempfile.mkdtemp()
FILE_UPLOAD_TEMP_DIR = tempfile.mkdtemp()

# Boost perf a little
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# skip captcha tests in tests
SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

# Force every loggers to use null handler only. Note that using 'root'
# logger is not enough if children don't propage.
for logger in six.itervalues(LOGGING["loggers"]):  # noqa
    logger["handlers"] = ["console"]
    logger["propagate"] = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("POSTGRES_DB", "test"),
        "USER": POSTGRES_USER,
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "password"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", 5432),
    }
}
STRIPE_PUBLIC_KEY = "public_key"
STRIPE_SECRET_KEY = "secret_key"
stripe.api_key = STRIPE_SECRET_KEY
STRIPE_ENDPOINT_SECRET = "endpoint_secret"
ENVIRONMENT_DOMAIN = ""
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

try:
    from .local import *  # noqa
except ImportError:
    pass

HUBSPOT_API_CLIENT = HubSpot(api_key="my_hub_spot_api_key")

# Redis
RQ_ASYNC = False
RQ_QUEUES = {
    "default": {
        "URL": REDIS.geturl(),
        "DB": 0,
        "DEFAULT_TIMEOUT": 360,
        "ASYNC": RQ_ASYNC,
        # "OPTIONS": {
        #     "ssl_cert_reqs": None
        # },
    },
}


# Better traceback
db_utils.CursorDebugWrapper = TracebackCursorWrapper

if POSTGRES_USER != "runner":
    # Do not override runner in gitlab
    TEST_RUNNER = "smart_testing.runners.SmartDiscoverRunner"

SMART_TESTING = {
    "CAPTURE_PRINTS": True,
    "SUCCESS_ASCII_FILEPATH": f"{MIXITY_DIR}/static/img/success.txt",
    "ASSERT_NUM_QUERIES_REFERENCE_ENABLED": config(
        "ASSERT_NUM_QUERIES_REFERENCE_ENABLED", default=True, cast=bool
    ),
    "IGNORED_PATH_STACK_PATTERNS": [
        r".*/lib/python.*",
        r".*manage\.py$",
        r".*/smart_testing/.*",
    ],
}

# Better traceback
sys.excepthook = SmartTraceback(
    hide_external_files=True,
    absolute_paths=False,
    verbose_level=1,
    call_pdb=False,
    root=None,
)

# Ignore whitenoise warning during tests
import warnings

warnings.filterwarnings("ignore", message="No directory at", module="whitenoise.base")

# import logging

DEFAULT_LOG_LEVEL = "DEBUG"

# LOGGING = {
#     "version": 1,
#     "handlers": {
#         "console": {
#             "level": "DEBUG",
#             "class": "logging.StreamHandler",
#         }
#     },
#     "loggers": {
#         "django.db.backends": {
#             "level": "DEBUG",
#             "handlers": ["console"],
#         }
#     },
# }
