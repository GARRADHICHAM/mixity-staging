from django.template.defaulttags import register


@register.filter(name="absolute_value")
def absolute_value(value):
    try:
        if isinstance(value, float):
            if value < 0:
                return -value
            return value
    except TypeError:
        return None
