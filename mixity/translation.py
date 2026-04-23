from modeltranslation.translator import TranslationOptions, register


from .models import FAQ, Language, SolutionFormat


@register(FAQ)
class CommentTranslationOptions(TranslationOptions):
    fields = ("question", "answer")


@register(Language)
class LanguageTranslationOptions(TranslationOptions):
    fields = ("label",)


@register(SolutionFormat)
class SolutionFormatTranslationOptions(TranslationOptions):
    fields = ("label",)
