from django import template

register = template.Library()


@register.filter
def next_element(list_obj, index):
    try:
        return list(list_obj)[int(index) + 1]
    except Exception:
        return ""


@register.filter
def previous_element(list_obj, index):
    try:
        return list(list_obj)[int(index) - 1]
    except Exception:
        return ""
