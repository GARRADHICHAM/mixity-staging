from django import template

register = template.Library()


@register.filter
def getattribute(object, attr):
    return getattr(object, attr.replace("-", "_"))
