from django import template

register = template.Library()


@register.filter
def concat(s1, s2):
    return (s1 or "") + (s2 or "")
