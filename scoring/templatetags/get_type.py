from django.template.defaulttags import register


@register.filter(name="get_type")
def get_type(value):
    return value.field.__class__.__name__
