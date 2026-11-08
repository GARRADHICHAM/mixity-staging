from modeltranslation.translator import TranslationOptions, register

from accounts.models import HumanCriteria, HumanCriteriaChoice
from .models import (
    Comment,
    Aim,
    Strength,
    Weakness,
    Question,
    Choice,
    SubQuestion,
    SubquestionChoice,
    Evaluation,
    Answer,
    SubCategory,
    Indicator,
    GeneralAnalysis,
    ExpertDei,
    AnalysisByDimension,
    KeyRecommendation,
    AssessmentBestPractice,
    Profile,
    IAScanAnalysisElement,
)


@register(SubCategory)
class SubCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Comment)
class CommentTranslationOptions(TranslationOptions):
    fields = ("description",)


@register(Aim)
class AimTranslationOptions(TranslationOptions):
    fields = ("description",)


@register(Strength)
class StrengthTranslationOptions(TranslationOptions):
    fields = ("description",)


@register(Weakness)
class WeaknessTranslationOptions(TranslationOptions):
    fields = ("description",)


@register(Question)
class QuestionTranslationOptions(TranslationOptions):
    fields = ("label", "help_text", "recommandation", "indicators")


@register(Choice)
class ChoiceTranslationOptions(TranslationOptions):
    fields = ("label",)


@register(SubQuestion)
class SubQuestionTranslationOptions(TranslationOptions):
    fields = ("label",)


@register(SubquestionChoice)
class SubquestionChoiceTranslationOptions(TranslationOptions):
    fields = ("label",)


@register(Evaluation)
class EvaluationTranslationOptions(TranslationOptions):
    fields = (
        "pdf_sheet",
        "collaborators_mail",
        "collaborators_mail_object",
    )


@register(Answer)
class AnswerTranslationOptions(TranslationOptions):
    fields = ("perimeter",)


@register(HumanCriteria)
class HumanCriteriaTranslationOption(TranslationOptions):
    fields = ("label",)


@register(HumanCriteriaChoice)
class HumanCriteriaChoiceTranslationOption(TranslationOptions):
    fields = ("label",)


@register(Indicator)
class IndicatorTranslationOption(TranslationOptions):
    fields = ("title", "selector_labels")


@register(GeneralAnalysis)
class GeneralAnalysisTranslationOption(TranslationOptions):
    fields = ("content", "comment")


@register(ExpertDei)
class ExpertDeiTranslationOption(TranslationOptions):
    fields = ("title",)


@register(AnalysisByDimension)
class AnalysisByDimensionTranslationOption(TranslationOptions):
    fields = ("content",)


@register(KeyRecommendation)
class KeyRecommendationTranslationOption(TranslationOptions):
    fields = ("content",)


@register(AssessmentBestPractice)
class AssessmentBestPracticeTranslationOption(TranslationOptions):
    fields = ("content",)


@register(Profile)
class ProfileTranslationOption(TranslationOptions):
    fields = ("name", "strenght", "improvement", "type")


@register(IAScanAnalysisElement)
class IAScanAnalysisElementTranslationOption(TranslationOptions):
    fields = ("content",)
