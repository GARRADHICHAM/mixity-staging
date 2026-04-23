from django.template.defaulttags import register


@register.filter
def sub_label(label):
    label = label.replace("Mixity ", "")
    return label
