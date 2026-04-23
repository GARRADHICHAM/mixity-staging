from django import template

register = template.Library()


@register.filter
def list_index(indexable, i):
    if len(indexable) > i:
        return indexable[i]
    else:
        return None
