import os

from django.conf import settings
from modeltranslation.utils import fallbacks

def conf(request):
    settings_dict = {
        "ENVIRONMENT_NAME": settings.ENVIRONMENT_NAME,
        "ENVIRONMENT_COLOR": settings.ENVIRONMENT_COLOR,
    }

    if os.environ["DJANGO_SETTINGS_MODULE"] == "mixity.settings.prod":
        settings_dict["SENTRY_DSN"] = settings.SENTRY_DSN
        settings_dict["SENTRY_ENV"] = settings.SENTRY_ENV
        settings_dict["GTAG"] = settings.GTAG
        settings_dict["HOTJAR_SCRIPT"] = settings.HOTJAR_SCRIPT
        settings_dict["CRISP_ID"] = settings.CRISP_ID
        settings_dict["SCREEB_KEY"] = settings.SCREEB_KEY
        settings_dict["USER_GUIDING_KEY"] = settings.USER_GUIDING_KEY
        settings_dict["GOOGLE_ANALYTICS_KEY"] = settings.GOOGLE_ANALYTICS_KEY

    return settings_dict
