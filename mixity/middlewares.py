import base64
import re

from django.conf import settings
from django.http import HttpResponse
from django.middleware.locale import LocaleMiddleware as _LocaleMiddleware
from django.utils import translation

from accounts.vocabularies import (
    CURRENCY_CHOICES,
    DOLLARD_CODE,
    EURO_CODE,
    EUROPEAN_COUNTRY_CODE,
    LANGUAGE_CHOICES,
)


class BasicAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # If DEBUG is true, we're in dev. Raise MiddlewareNotUsed to remove
        # this middleware from the list.
        # TODO: This should probably be based off of the QA env once we hit
        # production

    def _unauthed(self):
        response = HttpResponse(
            """<html><title>Auth required</title><body>
                                <h1>Authorization Required</h1></body></html>""",
            content_type="text/html",
        )
        response["WWW-Authenticate"] = 'Basic realm="Development"'
        response.status_code = 401
        return response

    def __call__(self, request):
        if "HTTP_AUTHORIZATION" not in request.META:
            return self._unauthed()
        else:
            authentication = request.META["HTTP_AUTHORIZATION"]
            (auth_method, auth) = authentication.split(" ", 1)
            if "basic" != auth_method.lower():
                return self._unauthed()
            auth = base64.b64decode(auth.strip()).decode("utf-8")
            username, password = auth.split(":", 1)
            if (
                username == settings.BASICAUTH_USERNAME
                and password == settings.BASICAUTH_PASSWORD
            ):
                return self.get_response(request)

        return self._unauthed()


class ConfigMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        version = settings.VERSION
        setattr(request, "version", version)
        response = self.get_response(request)
        return response


LANGUAGE_CODES = set([code for code, label in LANGUAGE_CHOICES])


def validate_language(language_code):
    if not language_code:
        return None
    language_code = language_code.lower()
    if language_code in LANGUAGE_CODES:
        return language_code
    return None


class LocaleMiddleware(_LocaleMiddleware):
    def process_request(self, request):
        # Extracting cookie language
        lang = validate_language(request.COOKIES.get("language_code", None))

        # If user is authenticated
        if request.user.is_authenticated and request.user.language:
            if not lang:
                lang = validate_language(request.user.language)
            elif lang != request.user.language:
                request.user.language = lang
                request.user.save()

        # If browser has specified a known language
        if not lang:
            lang = validate_language(
                translation.get_language_from_request(request, check_path=False)
            )

        # Finally, if nothing else, the default user language
        if not lang:
            # In fact we never get here because translation.get_language_from_request()
            # Returns the server LANGUAGE_CODE if nothing is specified in the request
            lang = settings.DEFAULT_USER_LANGUAGE_CODE

        # Setting locale
        translation.activate(lang)
        # Saving locale in request
        request.LANGUAGE_CODE = lang

    def process_response(self, request, response):
        # response.headers.setdefault('Content-Language', request.LANGUAGE_CODE)
        response.set_cookie("language_code", request.LANGUAGE_CODE)
        return response


class CurrencyMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Extracting cookie currency
        currency = request.COOKIES.get("currency_code")

        # If user is authenticated
        if request.user.is_authenticated:
            if currency:
                if currency != request.user.currency:
                    request.user.currency = currency
                    request.user.save()
            else:
                currency = request.user.currency

        if not currency:
            accept_language = request.headers.get("Accept-Language")
            res = accept_language and re.match(
                r"^[a-zA-Z]{2}[-_][a-zA-Z]{2}", accept_language
            )

            if res:
                res = res.group(0)
                country_code = res.replace("-", "_").split("_")[1]

                if country_code in EUROPEAN_COUNTRY_CODE:
                    currency = EURO_CODE
                else:
                    currency = DOLLARD_CODE
            else:
                currency = DOLLARD_CODE

        request.CURRENCY_CODE = currency
        request.CURRENCY_SYMBOL = dict(CURRENCY_CHOICES)[currency]

        response = self.get_response(request)

        response.set_cookie("currency_code", request.CURRENCY_CODE)
        return response
