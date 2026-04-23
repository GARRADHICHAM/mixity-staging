from django import template

register = template.Library()


@register.simple_tag(name="histogram_rate")
def do_histogram_rate(value=None, max_value=None, max_rate=None):
    """
    Format evolution between two years
    Usage::
        {% load histogram_rate %}
        {% histogram_rate  %}
    """

    if value is None:
        return (0, 0)

    elif value == 0:
        return (max_rate, max_rate)

    if value > 0:
        value = 100 - float(value)
        max_value = float(max_value)
        ratio = (value / max_value) * max_rate
        result = round(ratio)
        return (max_rate, result)

    elif value < 0:
        value = 100 + float(value)
        max_value = float(max_value)
        ratio = (value / max_value) * max_rate
        result = round(ratio)
        return (result, max_rate)
