from django.template.defaulttags import register


@register.filter(name="modulo")
def modulo(num, val):
    return num % val
