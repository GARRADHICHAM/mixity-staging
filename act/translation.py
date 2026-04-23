from modeltranslation.translator import TranslationOptions, register

from act.models import (
    Solution,
    BestPractice,
    BestPracticePublic,
    BestPracticeType,
    BestPracticeKeyword,
    BestPracticeSize,
    BestPracticeOrganizationType,
)


@register(Solution)
class SolutionTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "summary",
        "description",
        "price_desc",
        "public",
        "objective",
        "format_session",
    )


@register(BestPractice)
class BestPracticeOptions(TranslationOptions):
    fields = ("label", "summary", "description", "setting_up", "difficulties", "advice")


@register(BestPracticePublic)
class BestPracticePublicTranslationOptions(TranslationOptions):
    fields = ("label",)


@register(BestPracticeType)
class BestPracticeTypeTranslationOptions(TranslationOptions):
    fields = ("label",)


@register(BestPracticeKeyword)
class BestPracticeKeywordTranslationOptions(TranslationOptions):
    fields = ("label",)


@register(BestPracticeSize)
class BestPracticeSizeTranslationOptions(TranslationOptions):
    fields = ("label",)


@register(BestPracticeOrganizationType)
class BestPracticeOrganizationTypeTranslationOptions(TranslationOptions):
    fields = ("label",)
