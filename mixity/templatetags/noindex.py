import os

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def noindex():
    if os.getenv("SENTRY_ENV") == "staging":
        return mark_safe("<meta name=”robots” content=”noindex”>")
    else:
        return ""
