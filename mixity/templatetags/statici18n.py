from django import template
from django.templatetags.static import static

register = template.Library()


@register.simple_tag(takes_context=True)
def statici18n(context, file_path):
    if (
        hasattr(context["request"], "LANGUAGE_CODE")
        and context["request"].LANGUAGE_CODE == "fr"
    ):
        file_path = file_path.replace("{LANGUAGE}", "fr")
    else:
        file_path = file_path.replace("{LANGUAGE}", "en")
    static_path = static(file_path)
    return static_path
