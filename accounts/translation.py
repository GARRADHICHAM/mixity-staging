from modeltranslation.translator import TranslationOptions, register

from .models import Structure, BusinessLine


@register(Structure)
class StructureTranslationOptions(TranslationOptions):
    fields = ("description", "human_description", "commitment")


@register(BusinessLine)
class BusinessLineTranslationOptions(TranslationOptions):
    fields = ("name",)

