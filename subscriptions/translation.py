from django.utils.translation import ugettext_lazy as _
from modeltranslation.translator import TranslationOptions, register

from .models import SubscriptionType


# @register(Price)
# class PriceTranslationOptions(TranslationOptions):
#     fields = ("tax_free_price",)


@register(SubscriptionType)
class SubscriptionTypeTranslationOptions(TranslationOptions):
    fields = ("description",)
