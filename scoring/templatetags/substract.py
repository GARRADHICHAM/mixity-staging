from django.template.defaulttags import register


@register.filter(name="substract")
def substract(value, arg):
    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
        if isinstance(arg, str):
            arg = arg.replace(",", ".")
        return round(float(value) - float(arg), 1)
    except TypeError:
        return None
