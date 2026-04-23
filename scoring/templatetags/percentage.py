from django.template.defaulttags import register


@register.filter(name="percentage")
def percentage(num, den):
    if num is not None and den:
        return num * 100 / den
