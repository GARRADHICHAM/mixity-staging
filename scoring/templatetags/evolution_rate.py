from django.template.defaulttags import register


@register.filter(name="evolution_rate")
def evolution_rate(value1, value2):
    try:
        value1 = float(value1)
    except (ValueError, TypeError):
        value1 = 0
    try:
        value2 = float(value2)
    except (ValueError, TypeError):
        value2 = 0
    if value2 == 0:
        return 0
    return round(((value1 - value2) / value2) * 100, 2)
