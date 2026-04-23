from modeltranslation.translator import TranslationOptions, register

from lead.models import (
    GenericKpi,
)


@register(GenericKpi)
class GenericKpiTranslationOptions(TranslationOptions):
    fields = ("label", "help_text")
