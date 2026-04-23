from django.template.defaulttags import register


@register.filter
def get_tax_free_price(subscription_type, workforce):
    return subscription_type.get_tax_free_price(workforce)
