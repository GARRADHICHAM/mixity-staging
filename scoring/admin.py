import csv
import datetime
import io
import logging
import gzip
import shutil
from datetime import date
from datetime import timedelta
from datetime import datetime
from tempfile import NamedTemporaryFile

from django.contrib.admin.widgets import (
    FilteredSelectMultiple,
)
from django.db.models.fields.related import ForeignKey
from django.db.models.functions import Coalesce

from django.db.models.query import QuerySet
from django.forms import BaseInlineFormSet
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.template.loader import render_to_string
from django.utils.html import format_html
from accounts.mails import (
    send_evaluation_answers_export,
    send_mail_evaluation_started,
)
from tinymce.widgets import TinyMCE
from address.models import Country
from django import forms
from django_rq import job
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter, StackedInline
from django.db.models import JSONField, Prefetch, Sum, F, Q, Count
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from accounts.vocabularies import MONTHS
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django_json_widget.widgets import JSONEditorWidget
from modeltranslation.admin import (
    TranslationAdmin,
    TranslationStackedInline,
    TranslationTabularInline,
)
from django.utils.translation import ugettext_lazy as _, get_language, activate


from accounts.models import (
    Membership,
    Entity,
    Structure,
    HumanCriteria,
    HumanCriteriaChoice,
    MixityUser,
)
from mixity import settings
from mixity.admin import MixityAdmin, MixityTabularInline, model_link
from mixity.services.namsor.api import Namsor
from mixity.settings import DEFAULT_CHOICE_VALUE
from mixity.utils import evaluation_random_generator, CSSJsAdminMixin
from scoring.mails import (
    send_evaluation_published_private_mail,
    send_evaluation_published_public_mail,
    send_evaluation_validated_mail,
    send_reevaluation_accepted,
)
from scoring.models import (
    Action,
    Aim,
    Answer,
    Category,
    Choice,
    Comment,
    ComputedEvaluation,
    CountryData,
    Evaluation,
    Question,
    QuestionSheet,
    QuestionSheetType,
    QuestionTag,
    ReevaluationRequest,
    ScoreCategory,
    Strength,
    SubAnswer,
    SubCategory,
    SubQuestion,
    Weakness,
    Collaborator,
    CollaboratorsStatistics,
    do_update_scoring,
    pre_register_filters,
    Indicator,
    IndicatorType,
    AnalysisByDimension,
    KeyRecommendation,
    AssessmentBestPractice,
    ExpertDei,
    GeneralAnalysis,
    MAIN_CATEGORIES_SLUGS,
    Profile,
    Skill,
    ScanCollaborator,
    IAScanAnalysis,
    IAScanAnalysisElement,
)
from subscriptions.models import Subscription, SubscriptionType, SubscriptionOption
from django.utils.translation import ugettext_lazy as _

from scoring.ia_scan import IAScan

logger = logging.getLogger(__name__)


@job("default")
def compute_export_evaluation_answers(email, evaluation_id):
    evaluation = Evaluation.objects.select_related(
        "entity__entity_level__structure"
    ).get(pk=evaluation_id)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_{evaluation.id}_answers_{stamp}"
    export = AnswerExport(evaluation)
    zipfile = export.zip(filename)
    send_evaluation_answers_export(email, evaluation, filename + ".gz", zipfile)


class EvaluationCountryFilter(SimpleListFilter):
    title = "country"
    parameter_name = (
        "entity__entity_level__structure__address__locality__state__country"
    )

    def lookups(self, request, model_admin):
        active_countries = Country.objects.filter(
            states__localities__isnull=False
        ).distinct()
        return active_countries.values_list("id", "name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                entity__entity_level__structure__address__locality__state__country__id__exact=self.value()
            )
        else:
            return queryset


class ScoreCategoryInline(MixityTabularInline):
    model = ScoreCategory
    can_delete = True
    extra = 0  #  pour supprimer les lignes inutiles
    fields = (
        "category",
        "category_answers_rate",
        "value",
        "actions",
        "evolution_delta",
        "is_evolution_delta_hidden",
    )
    readonly_fields = ("category", "category_answers_rate", "value", "actions")

    def get_queryset(self, request):
        queryset = super(ScoreCategoryInline, self).get_queryset(request)
        queryset = queryset.prefetch_related(
            "category",
            "category__subcategories",
        )
        return queryset

    def actions(self, sc):
        tmp_str = ""
        action = sc.actions.first()
        if action:
            tmp_str += "<strong>Détails</strong><br/>"
            for i in range(0, settings.DEFAULT_ACTION_ROW_NUMBER):
                tmp_str += (
                    str(i)
                    + ". "
                    + str(action.intitules_detail[i])
                    + " => "
                    + str(action.descriptif_detail[i])
                    + "<br/>"
                )
            tmp_str += "<strong>Objectifs</strong><br/>"
            for i in range(0, settings.DEFAULT_ACTION_ROW_NUMBER):
                tmp_str += (
                    str(i)
                    + ". "
                    + str(action.intitules_aim[i])
                    + " => "
                    + str(action.descriptif_aim[i])
                    + "<br/>"
                )
        return mark_safe(tmp_str)

    def has_add_permission(self, request, obj):
        """
        Supprime dans l'admin le bouton <Ajouter un objet> pour le modèle ScoreCategory
        :param request:
        :param obj:
        :return: False
        """
        return True


class AimInline(TranslationStackedInline, CSSJsAdminMixin):
    model = Aim
    # extra = 0  #  pour supprimer les lignes inutiles
    classes = ("collapse",)
    category = ""
    category_name = ""
    exclude = ["answer"]

    def __init__(self, *args, **kwargs):
        super(AimInline, self).__init__(*args, **kwargs)
        self.verbose_name = f"Objectif {self.category_name}"
        self.verbose_name_plural = f"Objectifs {self.category_name}"
        self.classes += (self.category,)

    def get_queryset(self, request):
        queryset = super(AimInline, self).get_queryset(request)
        return queryset.filter(category__slug=self.category)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(AimInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )

        return field


class GeneralAimInline(AimInline):
    category = "all"
    category_name = "Transversal"


class GenderAimInline(AimInline):
    category = "gender"
    category_name = "Genre"


class DisabilityAimInline(AimInline):
    category = "disability"
    category_name = "Handicap"


class CulturalAimInline(AimInline):
    category = "cultural_diversity"
    category_name = "Origines"


class GenerationalAimInline(AimInline):
    category = "generational_diversity"
    category_name = "Générations"


class LGBTAimInline(AimInline):
    category = "lgbt"
    category_name = "LGBTQIA+"


class GeneralConceptAimInline(AimInline):
    category = "general_concept"
    category_name = "Notions générales"


class CommunicationAimInline(AimInline):
    category = "communication"
    category_name = "Communication"


class PersonalEngagementAimInline(AimInline):
    category = "professional_engagement"
    category_name = "Engagement personnel"


class ProfessionalPracticesAimInline(AimInline):
    category = "professional_practice"
    category_name = "Pratique professionnelle"


class CognitiveBiasesAimInline(AimInline):
    category = "cognitive_biases"
    category_name = "Biais cognitifs"


class BonusPostureAimInline(AimInline):
    category = "bonus_posture"
    category_name = "Bonus - Attitude"


class StrengthInline(TranslationStackedInline, CSSJsAdminMixin):
    model = Strength
    extra = 0  #  pour supprimer les lignes inutiles
    classes = ("collapse",)
    category = ""
    category_name = ""

    def __init__(self, *args, **kwargs):
        super(StrengthInline, self).__init__(*args, **kwargs)
        self.verbose_name = f"Point fort {self.category_name}"
        self.verbose_name_plural = f"Points forts {self.category_name}"
        self.classes += (self.category,)

    def get_queryset(self, request):
        queryset = super(StrengthInline, self).get_queryset(request)
        return queryset.filter(category__slug=self.category)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(StrengthInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )

        return field


class GeneralStrengthInline(StrengthInline):
    category = "all"
    category_name = "Transversal"


class GenderStrengthInline(StrengthInline):
    category = "gender"
    category_name = "Genre"


class DisabilityStrengthInline(StrengthInline):
    category = "disability"
    category_name = "Handicap"


class CulturalStrengthInline(StrengthInline):
    category = "cultural_diversity"
    category_name = "Origines"


class GenerationalStrengthInline(StrengthInline):
    category = "generational_diversity"
    category_name = "Générations"


class LGBTStrengthInline(StrengthInline):
    category = "lgbt"
    category_name = "LGBTQIA+"


class GeneralConceptStrengthInline(StrengthInline):
    category = "general_concept"
    category_name = "Notions générales"


class CommunicationStrengthInline(StrengthInline):
    category = "communication"
    category_name = "Communication"


class PersonalEngagementStrengthInline(StrengthInline):
    category = "professional_engagement"
    category_name = "Engagement personnel"


class ProfessionalPracticesStrengthInline(StrengthInline):
    category = "professional_practice"
    category_name = "Pratique professionnelle"


class CognitiveBiasesStrengthInline(StrengthInline):
    category = "cognitive_biases"
    category_name = "Biais cognitifs"


class BonusPostureStrengthInline(StrengthInline):
    category = "bonus_posture"
    category_name = "Bonus - Attitude"


class WeaknessInline(TranslationStackedInline, CSSJsAdminMixin):
    model = Weakness
    extra = 0  #  pour supprimer les lignes inutiles
    classes = ("collapse",)
    category = ""
    category_name = ""

    def __init__(self, *args, **kwargs):
        super(WeaknessInline, self).__init__(*args, **kwargs)
        self.verbose_name = f"Point faible {self.category_name}"
        self.verbose_name_plural = f"Points faibles {self.category_name}"
        self.classes += (self.category,)

    def get_queryset(self, request):
        queryset = super(WeaknessInline, self).get_queryset(request)
        return queryset.filter(category__slug=self.category)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(WeaknessInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )

        return field


class GeneralWeaknessInline(WeaknessInline):
    category = "all"
    category_name = "Transversal"


class GenderWeaknessInline(WeaknessInline):
    category = "gender"
    category_name = "Genre"


class DisabilityWeaknessInline(WeaknessInline):
    category = "disability"
    category_name = "Handicap"


class CulturalWeaknessInline(WeaknessInline):
    category = "cultural_diversity"
    category_name = "Origines"


class GenerationalWeaknessInline(WeaknessInline):
    category = "generational_diversity"
    category_name = "Générations"


class LGBTWeaknessInline(WeaknessInline):
    category = "lgbt"
    category_name = "LGBTQIA+"


class GeneralConceptWeaknessInline(WeaknessInline):
    category = "general_concept"
    category_name = "Notions générales"


class CommunicationWeaknessInline(WeaknessInline):
    category = "communication"
    category_name = "Communication"


class PersonalEngagementWeaknessInline(WeaknessInline):
    category = "professional_engagement"
    category_name = "Engagement personnel"


class ProfessionalPracticesWeaknessInline(WeaknessInline):
    category = "professional_practice"
    category_name = "Pratique professionnelle"


class CognitiveBiasesWeaknessInline(WeaknessInline):
    category = "cognitive_biases"
    category_name = "Biais cognitifs"


class BonusPostureWeaknessInline(WeaknessInline):
    category = "bonus_posture"
    category_name = "Bonus - Attitude"


class EvaluationForm(forms.ModelForm):
    model = Evaluation
    fields = "__all__"
    tags = forms.ModelMultipleChoiceField(
        queryset=QuestionTag.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Tags", False),
    )
    mandatory_questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Mandatory questions", False),
    )
    forbidden_questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Forbidden questions", False),
    )

    def __init__(self, *args, **kwargs):
        super(EvaluationForm, self).__init__(*args, **kwargs)
        fields = [
            "collaborators_mail_fr",
            "collaborators_mail_en",
            "collaborators_mail_es",
            "collaborators_mail_it",
            "collaborators_mail_ja",
            "collaborators_mail_zh_hans",
            "collaborators_mail_zh_hant",
        ]
        for field in fields:
            self.fields[field].widget = TinyMCE(
                attrs={"cols": 2, "rows": 2, "height": 200}
            )
        questions_list = [
            (
                q.id,
                f"{q.google_sheets_id} {q.category.name} / {q.subcategory.name} : {q.label}",
            )
            for q in self.instance.sheet.questions.all()
            .select_related("category", "subcategory")
            .only(
                "id",
                "google_sheets_id",
                "label",
                "category__name",
                "subcategory__name",
            )
        ]  # We only select questions related to the current sheet
        self.fields["mandatory_questions"].choices = questions_list
        self.fields["forbidden_questions"].choices = questions_list


class AnswerAdminForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(AnswerAdminForm, self).__init__(*args, **kwargs)
        if hasattr(self.instance, "question"):
            if self.fields.get("comment"):
                comments_list = [(None, _("--- Rien ---"))] + [
                    (comment.id, comment.__str__())
                    for comment in self.instance.question.comments.all()
                ]
                self.fields["comment"].choices = comments_list
            if self.instance.question.type == "mutliple_qcm":
                if "choices" in self.fields:
                    self.fields["choices"].queryset = (
                        self.instance.question.choices.all()
                    )
            else:
                if "choice" in self.fields:
                    self.fields["choice"].queryset = Choice.objects.filter(
                        question=self.instance.question
                    )


class EvaluationAnswerInline(MixityTabularInline, CSSJsAdminMixin):
    model = Answer
    ordering = ("question",)
    # readonly_fields = ('question', 'value', 'choice')
    fields = [
        "question_",
        "is_not_applicable",
        "is_not_followed",
        "empty_answer_mark",
        "choice_value",
        "question_weight_index",
        "choice",
        "choices",
        "text_value",
        "custom_value",
        "subanswers",
        "locked",
        "display",
        "to_review",
        "comment",
        "collaborator_comment",
    ]
    readonly_fields = [
        "question_",
        "empty_answer_mark",
        "choice_value",
        "question_weight_index",
        "choice",
        "choices",
        "custom_value",
        "subanswers",
        "collaborator_comment",
    ]
    # autocomplete_fields = ('choice',)
    form = AnswerAdminForm
    extra = 0
    can_delete = False
    max_num = 0
    classes = ("collapse",)
    category = ""
    category_name = ""
    _answers_dict = None

    def __init__(self, *args, **kwargs):
        super(EvaluationAnswerInline, self).__init__(*args, **kwargs)
        self.verbose_name = f"Réponse au questionnaire {self.category_name}"
        self.verbose_name_plural = f"Réponses au questionnaire {self.category_name}"
        self.classes += (self.category,)

    def choice_value(self, answer):
        return answer.choice.value

    def question_weight_index(self, answer):
        return answer.question.weight_index

    def question_(self, answer):
        return mark_safe(
            "<a title='Editer' target='_blank' href='../../../answer/"
            + str(answer.id)
            + "/change/'>🖊️</a> <a title='Télécharger les réponses' target='_blank' href='../../../../../scoring/evaluation/"
            + str(answer.evaluation_id)
            + "/"
            + str(answer.question_id)
            + "/export_answers/'><img style='height:15px' src='../../../../../static/img/excel.png' /></a> "
            + answer.question.__str__()
            + (" " + (answer.custom_question_label or ""))
        )

    def empty_answer_mark(self, answer):
        mark = answer.question.none_answer_value
        if mark is None:
            return DEFAULT_CHOICE_VALUE
        return mark

    def subanswers(self, answer):
        return mark_safe(
            "<br>".join(
                [
                    f"<b>{subanswer.subquestion.label} </b>- {(subanswer.value is not None and str(subanswer.value)) or (subanswer.choice and subanswer.choice.label)}"
                    for subanswer in answer.subanswers.all()
                ]
            )
        )

    def custom_value(self, answer):
        value = answer.value
        ratio_value = answer.ratio_value
        types = answer.question.get_types()

        if (
            len(types) > 2 and types[1] == "json"
        ):  # Special case with the new question type
            json_data = answer.question.get_json_data()

            # if it's a ratio, we display the pre-computed ratio
            if json_data["mode"] == "ratio-questions" and ratio_value is not None:
                # We return the formated value (in percent for example) and the original value
                return str(value) + " (" + str(ratio_value) + " %)"

            else:
                return value

        # Case when error with the JSON type or with all the other types
        if value is not None:
            return value
        else:
            return "-"

    choice_value.empty_value_display = "???"
    question_weight_index.empty_value_display = "???"

    def get_queryset(self, request):
        queryset = super(EvaluationAnswerInline, self).get_queryset(request)
        queryset = (
            queryset.filter(question__category__slug=self.category)
            .order_by("question_id", "pk")
            .distinct("question")
            .select_related(
                "choice",
                "question__category",
                "question__subcategory",
                "comment__question",
            )
            .prefetch_related(
                Prefetch(
                    "subanswers",
                    queryset=SubAnswer.objects.select_related(
                        "answer", "subquestion", "choice"
                    ),
                ),
                "question__comments",
            )
        )
        return queryset


class GenderAnswerInline(EvaluationAnswerInline):
    category = "gender"
    category_name = "Genre"


class CulturalAnswerInline(EvaluationAnswerInline):
    category = "cultural_diversity"
    category_name = "Origines"


class LGBTAnswerInline(EvaluationAnswerInline):
    category = "lgbt"
    category_name = "LGBTQIA+"


class GenerationalAnswerInline(EvaluationAnswerInline):
    category = "generational_diversity"
    category_name = "Générations"


class DisabilityAnswerInline(EvaluationAnswerInline):
    category = "disability"
    category_name = "Handicap"


class GeneralAnswerInline(EvaluationAnswerInline):
    category = "all"
    category_name = "Transversal"


class VosSuggestionsInline(EvaluationAnswerInline):
    category = "your-suggestions"
    category_name = "Vos Suggestions"


class GeneralConceptAnswerInline(EvaluationAnswerInline):
    category = "general_concept"
    category_name = "Notions générales"


class CommunicationAnswerInline(EvaluationAnswerInline):
    category = "communication"
    category_name = "Communication"


class PersonalEngagementAnswerInline(EvaluationAnswerInline):
    category = "professional_engagement"
    category_name = "Engagement personnel"


class ProfessionalPracticesAnswerInline(EvaluationAnswerInline):
    category = "professional_practice"
    category_name = "Pratique professionnelle"


class CognitiveBiasesAnswerInline(EvaluationAnswerInline):
    category = "cognitive_biases"
    category_name = "Biais cognitifs"


class BonusPostureAnswerInline(EvaluationAnswerInline):
    category = "bonus_posture"
    category_name = "Bonus - Attitude"


@job("default")
def do_admin_validation_worker(queryset, request=None):
    actual_language = get_language()
    activate("fr")
    for evaluation in queryset:
        evaluation.version = now()
        month_number = evaluation.version.month
        month_name = MONTHS[month_number - 1]
        evaluation.display_version = f"{evaluation.version.year}-{month_name}"
        evaluation.do_admin_validation(request=request, evaluation=evaluation)
    activate(actual_language)


def validate_evaluation(modeladmin, request, queryset):
    # email_already_sent = evaluation.is_validated_by_admin
    do_admin_validation_worker(queryset, request=request)
    # compute scores now directly on validation by admin
    compute_score_and_ratio(modeladmin, request=request, queryset=queryset)
    # Notify users by email
    # 2022 07 11: disabled because this email should depends on is_private state
    # if not email_already_sent and evaluation.sheet.type.slug != "mixity_start":
    #     for user in evaluation.structure.owners:
    #         send_evaluation_validated_mail(user, request, evaluation)


validate_evaluation.short_description = "Valider les évaluations selectionnées"


def publish_evaluation_public(modeladmin, request, queryset):
    for evaluation in queryset:
        evaluation.public_display = True
        if not evaluation.first_publication_date:
            evaluation.first_publication_date = timezone.now()
        evaluation.save()

        for user in evaluation.entity.entity_level.structure.owners:
            send_evaluation_published_public_mail(user, request, evaluation)


publish_evaluation_public.short_description = (
    "Publier les évaluations selectionnées publiquement"
)


def publish_evaluation_private(modeladmin, request, queryset):
    for evaluation in queryset:
        evaluation.private_display = True
        evaluation.save()

        for user in evaluation.entity.entity_level.structure.owners:
            send_evaluation_published_private_mail(user, request, evaluation)


publish_evaluation_private.short_description = (
    "Publier les évaluations selectionnées à l'entreprise"
)


def compute_score_and_ratio(modeladmin, request, queryset):
    for evaluation in queryset:
        if not evaluation.is_validated_by_user:
            messages.warning(
                request, "L'évaluation n'a pas encore été validée par le client."
            )
        elif not evaluation.is_validated_by_admin:
            messages.warning(request, "Vous n'avez pas encore validé l'évaluation.")
        elif (
            evaluation.sheet.type.slug == "evaluation_collaborateurs_360"
            and evaluation != evaluation.entity.last_human_evaluation
        ):
            messages.warning(
                request,
                "L'évaluation sélectionnée n'est pas l'évaluation HUMAN en cours ni la dernière validée.",
            )
        elif (
            evaluation.sheet.type.slug == "mixity_evaluation_scan"
            and evaluation != evaluation.entity.last_scan_evaluation
        ):
            messages.warning(
                request,
                "L'évaluation sélectionnée n'est pas l'évaluation SCAN en cours ni la dernière validée.",
            )
        elif (
            evaluation.sheet.type.slug
            not in ["evaluation_collaborateurs_360", "mixity_evaluation_scan"]
            and evaluation != evaluation.entity.last_global_evaluation
        ):
            messages.warning(
                request,
                "L'évaluation sélectionnée n'est pas l'évaluation DIAG/GLOBAL en cours ni la dernière validée.",
            )
        else:
            do_update_scoring.delay(
                evaluation.id,
                update_choices=True,
                update_comments=False,
                update_categories=True,
                user_email=request.user.email,
            )


compute_score_and_ratio.short_description = "Calculer les scores et ratios"


def compute_pre_registered_filters(modeladmin, request, queryset):
    """
    This function launch the computing of the filters from the admin interface and send an email in the end
    """

    for evaluation in queryset:
        pre_register_filters.delay(evaluation.pk, request.user.email)


compute_pre_registered_filters.short_description = "Calculer les filtres"


def compute_aim(modeladmin, request, queryset):
    for evaluation in queryset:
        evaluation.create_aims()


compute_aim.short_description = "Régénérer les objectifs"


def generate_answers(modeladmin, request, queryset):
    for e in queryset:
        e.generate_answers()


generate_answers.short_description = "Regénérer le questionnaire"


def get_top_sheet(evaluations):
    previous_sheet = evaluations[0].sheet
    same_sheets = True
    for e in evaluations:
        if e.sheet.type != previous_sheet.type or e.sheet.year != previous_sheet.year:
            same_sheets = False
            break
    if (
        same_sheets
    ):  ## si toutes les évaluations ont le même questionnaire, alors on reste sur le même référentiel
        return QuestionSheet.objects.filter(
            type=previous_sheet.type, year=previous_sheet.year
        ).last()
    return QuestionSheet.objects.filter(
        type__slug="mixity_evaluation_globale"
    ).last()  # sinon on passe forcément sur le plus gros référentiel


@job("default")
def send_reminder(evaluation):
    collaborators = evaluation.collaborators.annotate(
        num_answers=Count("answers")
    ).filter(num_answers=0)
    for c in collaborators:
        if c.user:
            send_mail_evaluation_started(
                c.user,
                evaluation,
            )


def send_reminder_evaluation_human(modeladmin, request, queryset):
    for evaluation in queryset:
        send_reminder.delay(evaluation)


send_reminder_evaluation_human.short_description = "Relance mail Human"


def reset_mean_scores(modeladmin, request, queryset):
    try:
        Evaluation.do_reset_mean_scores(queryset)

        modeladmin.message_user(
            request,
            "Réinitialisation des scores de l'évaluation effectuée avec succès.",
            level=messages.SUCCESS,
        )

    except Exception as e:
        modeladmin.message_user(
            request,
            f"Erreur lors de la réinitialisation des scores : {str(e)}",
            level=messages.ERROR,
        )


reset_mean_scores.short_description = "Reset mean scores"


class HumanCriteriaInline(MixityTabularInline):
    model = HumanCriteria
    fields = readonly_fields = ("criteria_link",)
    extra = 1

    criteria_link = model_link(None, HumanCriteria)


class HumanCriteriaChoiceFormSet(BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["criteria"] = self.instance
        return kwargs


class HumanCriteriaChoiceForm(forms.ModelForm):
    model = HumanCriteriaChoice

    def __init__(self, *args, criteria, **kwargs):
        super(HumanCriteriaChoiceForm, self).__init__(*args, **kwargs)
        questions_list = [
            (
                q.id,
                f"{q.google_sheets_id} {q.category.name} / {q.subcategory.name} : {q.label}",
            )
            for q in criteria.evaluation.sheet.questions.all()
            .select_related("category")
            .only(
                "id",
                "google_sheets_id",
                "label",
                "category__name",
                "subcategory__name",
            )
        ]  # We only select questions related to the current sheet
        self.fields["mandatory_questions"].choices = questions_list
        self.fields["forbidden_questions"].choices = questions_list


class HumanCriteriaChoiceInline(TranslationStackedInline):
    model = HumanCriteriaChoice
    form = HumanCriteriaChoiceForm
    formset = HumanCriteriaChoiceFormSet
    filter_horizontal = ("tags", "mandatory_questions", "forbidden_questions")

    class Meta:
        fields = "__all__"


class SelectWOA(forms.widgets.Select):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super(SelectWOA, self).create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        return option


class HumanCriteriaForm(forms.ModelForm):
    evaluation = forms.ModelChoiceField(
        queryset=Evaluation.objects.filter(
            subscription__subscription_type__slug="human"
        ).all(),
        widget=SelectWOA(),
    )
    model = HumanCriteria
    fields = "__all__"


class HumanCriteriaAdmin(TranslationAdmin, CSSJsAdminMixin):
    form = HumanCriteriaForm
    inlines = [HumanCriteriaChoiceInline]
    list_display = ["label", "evaluation"]
    search_fields = ["label", "evaluation__name"]
    fields = [
        "label",
        "order",
        "evaluation",
        "mandatory_tags",
        "forbidden_tags",
        "allow_multiple",
        "is_csv_imported",
    ]
    readonly_fields = []

    filter_horizontal = ("mandatory_tags", "forbidden_tags")

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + [
                "evaluation",
            ]
        return self.readonly_fields

    def get_inline_instances(self, request, obj=None):
        if obj:
            return [inline(self.model, self.admin_site) for inline in self.inlines]
        return []

    class Meta:
        fields = "__all__"


class AnswerExport:
    def __init__(self, evaluation):
        self.fields = []
        self.evaluation = evaluation
        self.criteria_ids = {}

    def generate_header(self):
        row = [
            "structure_name",
            "category",
            "question_google_sheets_id",
            "question_label",
            "value",
            "text_value",
            "collaborator_comment",
            "allow_raw_usage",
            "choice_value",
            "choice_label",
            "empty_answer_mark",
            "skills_weight",
            "weight",
            "choices_value",
            "choices_label",
            "subquestion_value",
            "subquestion_label",
            "subquestion_choice_value",
            "subquestion_choice_label",
        ]
        if self.evaluation.is_scan:
            self.fields = [
                f
                for f in ScanCollaborator._meta.get_fields()[1:]
                if f.name
                not in [
                    "uuid",
                    "human_criteria_choices",
                    "evaluation",
                    "job",
                    "tag",
                ]
            ]
        else:
            self.fields = [
                f
                for f in Collaborator._meta.get_fields()[1:]
                if f.name
                not in [
                    "uuid",
                    "human_criteria_choices",
                    "service",
                    "is_lgbt",
                    "evaluation",
                    "tag",
                ]
            ]
        for field in self.fields:
            row.append("collaborator_" + field.name)
        human_criteria = []
        for criteria in self.evaluation.human_criteria.all():
            self.criteria_ids[criteria.id] = len(human_criteria)
            row.append("collaborator_" + criteria.label)
            human_criteria.append(criteria.label)
        self.writer.writerow(row)
        return human_criteria

    def generate_answer(self, answer, collaborator_data):
        base_row = [
            answer.evaluation.entity.name,
            answer.question.category.name,
            answer.question.google_sheets_id,
            answer.question.label,
            str(answer.value).replace(".", ","),
            answer.text_value,
            answer.collaborator_comment,
            answer.allow_raw_usage,
            answer.choice and str(answer.choice.value).replace(".", ","),
            answer.choice and answer.choice.label,
            answer.question.none_answer_value,
            answer.question.skills_weight,
            answer.question.weight_index,
        ]
        if answer.choices.exists():
            for choice in answer.choices.all():
                self.write_row(
                    base_row,
                    [
                        f"{choice.value}".replace(".", ","),
                        f"{choice.label}",
                        "",
                        "",
                        "",
                        "",
                    ],
                    collaborator_data,
                )
        if answer.subanswers.exists():
            for sb in answer.subanswers.all():
                self.write_row(
                    base_row,
                    [
                        "",
                        "",
                        f"{sb.value}".replace(".", ","),
                        f"{sb.subquestion}",
                        f"{sb.choice and sb.choice.value}".replace(".", ","),
                        f"{sb.choice and sb.choice.label}",
                    ],
                    collaborator_data,
                )
        else:
            self.write_row(
                base_row,
                [
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ],
                collaborator_data,
            )

    def write_row(self, base_row, values, collaborator_data):
        self.writer.writerow(base_row + values + collaborator_data)

    def generate_answers(self):
        if (
            not self.evaluation.collaborators.exists()
            and not self.evaluation.scan_collaborators.exists()
        ):  # not a human so we get answers directly from evaluation
            iterable = [self.evaluation]
        else:
            if self.evaluation.is_scan:
                iterable = self.evaluation.scan_collaborators.only(
                    "id",
                    "age",
                    "civility",
                    "job",
                    "evaluation",
                    "scan_criteria_choices",
                ).iterator(
                    chunk_size=settings.COMPUTE_EXPORT_EVALUATION_ANSWERS_CHUNK_SIZE
                )
            else:
                iterable = self.evaluation.collaborators.only(
                    "id",
                    "age",
                    "civility",
                    "status",
                    "evaluation",
                    "human_criteria_choices",
                ).iterator(
                    chunk_size=settings.COMPUTE_EXPORT_EVALUATION_ANSWERS_CHUNK_SIZE
                )
        for obj in iterable:
            collab = "collaborator"
            collab_choices = None
            if isinstance(obj, ScanCollaborator):
                collab = "scan_collaborator"
                collab_choices = obj.scan_criteria_choices.all()
            elif isinstance(obj, Collaborator):
                collab_choices = obj.human_criteria_choices.all()

            for answer in (
                obj.answers.select_related(
                    "question__category",
                    "evaluation__entity",
                    "choice",
                    f"{collab}__evaluation__entity",
                )
                .prefetch_related(
                    Prefetch(
                        "subanswers",
                        queryset=SubAnswer.objects.select_related(
                            "subquestion", "choice"
                        ).only(
                            "value",
                            "answer",
                            "subquestion",
                            "choice",
                        ),
                    ),
                    "choices",
                )
                .only(
                    "evaluation__entity__name",
                    "question__category",
                    "question__id",
                    "question__label",
                    "question__google_sheets_id",
                    "question__none_answer_value",
                    "question__weight_index",
                    "question__skills_weight",
                    "text_value",
                    "collaborator_comment",
                    "allow_raw_usage",
                    "value",
                    "choice",
                    f"{collab}__evaluation__entity",
                )
            ):
                if collab_choices:
                    datas_list = [getattr(obj, field.name) for field in self.fields]
                    criteria_labels = [""] * len(self.criteria_ids)
                    for choice in collab_choices:
                        if criteria_labels[self.criteria_ids[choice.criteria_id]] == "":
                            criteria_labels[self.criteria_ids[choice.criteria_id]] = (
                                choice.label
                            )
                        else:
                            criteria_labels[self.criteria_ids[choice.criteria_id]] += (
                                ", " + choice.label
                            )
                    datas_list.extend(criteria_labels)
                else:
                    datas_list = []
                self.generate_answer(answer, datas_list)

    def csv(self, filename):
        with NamedTemporaryFile(
            mode="w", delete=False, prefix=filename + "_", suffix=".csv"
        ) as fd:
            self.writer = csv.writer(fd, delimiter=";", quoting=csv.QUOTE_NONNUMERIC)
            self.generate_header()
            self.generate_answers()
            return fd.name

    def zip(self, filename):
        csv_filepath = self.csv(filename)
        zip_filepath = csv_filepath + ".gz"
        with open(csv_filepath, "rb") as f_in:
            with gzip.open(zip_filepath, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return zip_filepath


class EvaluationAdmin(MixityAdmin, CSSJsAdminMixin):
    form = EvaluationForm
    exclude = [
        "collaborators_mail",
    ]
    search_fields = ["entity__name"]
    readonly_fields = (
        "global_score",
        "mean_score",
        "mean_score_in_business_line",
        "can_validate",
        "answers_rate",
        "collaborator_url",
        "created_date",
        "count_answers",
        "answers_rate_cache",
        "trial",
    )

    list_display = [
        "__str__",
        "display_version",
        # "structure_report_link",
        "entity_link",
        "is_started",
        "is_validated_by_user",
        "is_validated_by_admin",
        "private_display",
        "public_display",
        "global_score",
        "inline_page_link",
        "answers_rate",
        "sheet",
        "trial",
    ]
    list_filter = [
        "is_validated_by_admin",
        "is_validated_by_user",
        "sheet__type",
        "sheet__year",
        EvaluationCountryFilter,
    ]
    actions = [
        validate_evaluation,
        publish_evaluation_private,
        publish_evaluation_public,
        compute_score_and_ratio,
        compute_aim,
        # aggregate_score,
        generate_answers,
        reset_mean_scores,
        send_reminder_evaluation_human,
        "export_csv_score_categories",
        "export_csv_answers",
        evaluation_random_generator,
        compute_pre_registered_filters,
    ]
    max_num = 0
    extra = 0

    class Meta:
        fields = "__all__"

    def inline_page_link(self, obj):
        url = reverse("admin:scoring_evaluationexpertiseproxy_change", args=[obj.id])
        link = '<a href="{}">Page expertise pour {}</a>'.format(url, obj.entity)
        return mark_safe(link)

    inline_page_link.short_description = "Voir l'expertise"

    def trial(self, obj):
        # On retourne si l'évaluation a été créée dans le cadre d'un essai ou pas.
        return obj.is_trial

    def count_answers(self, obj):
        return obj.answers.count()

    def get_queryset(self, request):
        if request.resolver_match.func.__name__ == "change_view":
            queryset = super().get_queryset(request)
        else:
            queryset = Evaluation.objects.all()
        return queryset.select_related(
            "sheet__type",
            "entity",
            "subscription__subscription_type",
        ).prefetch_related("subscription__tags")

    def has_generated_thumbnails(self, obj):
        return bool(obj.footprint and obj.share and obj.social_thumbnail)

    has_generated_thumbnails.short_description = "Miniatures générées"
    has_generated_thumbnails.boolean = True

    def entity_link(self, obj):
        url = reverse("admin:accounts_entity_change", args=[obj.entity.id])
        link = '<strong><a href="{}">{}</a></strong>'.format(url, obj.entity)
        return mark_safe(link)

    entity_link.short_description = "Entité"

    def export_csv_score_categories(self, request, queryset):
        output = io.StringIO()
        writer = csv.writer(
            output,
            delimiter=";",
            quoting=csv.QUOTE_NONNUMERIC,
        )
        row = ["entity_name", "question_sheet_type", "year", "global_score"]
        sc_indexes = {}
        for category in Category.objects.filter(slug__in=MAIN_CATEGORIES_SLUGS):
            row.append(category.name)
            sc_indexes[category.slug] = len(sc_indexes)
        writer.writerow(row)
        for e in queryset:
            tmp_row = [
                e.entity.name,
                e.sheet.type,
                e.sheet.year,
                e.global_score,
            ]
            while len(tmp_row) < len(row):
                tmp_row.append("N/A")
            for sc in e.scores_categories.filter(
                category__slug__in=MAIN_CATEGORIES_SLUGS
            ):
                tmp_row[sc_indexes[sc.category.slug] + 4] = sc.value
            writer.writerow(tmp_row)
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="evaluations_scores_dump_'
            + datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            + '.csv"'
        )
        return response

    export_csv_score_categories.short_description = (
        "Extraire les scores par catégorie des évaluations sélectionnées"
    )

    def export_csv_answers(self, request, queryset):
        for evaluation_id in queryset.values_list("id", flat=True):
            compute_export_evaluation_answers.delay(request.user.email, evaluation_id)
        messages.success(
            request,
            (
                "Préparation de %i export(s)... Les résultats vous seront envoyés à l'adresse: %s"
            )
            % (queryset.count(), request.user.email),
        )

    export_csv_answers.short_description = (
        "Exporter les réponses des évaluations sélectionnées (envoi par email)"
    )


class EvaluationExpertiseProxy(Evaluation):
    class Meta:
        proxy = True
        verbose_name = "Expertise on Evaluation"
        verbose_name_plural = "Expertise on Evaluations"


class EvaluationExpertiseProxyAdmin(admin.ModelAdmin):
    inlines = [
        HumanCriteriaInline,
        ScoreCategoryInline,
        GeneralAnswerInline,
        GeneralStrengthInline,
        GeneralWeaknessInline,
        GeneralAimInline,
        GenderAnswerInline,
        GenderStrengthInline,
        GenderWeaknessInline,
        GenderAimInline,
        DisabilityAnswerInline,
        DisabilityStrengthInline,
        DisabilityWeaknessInline,
        DisabilityAimInline,
        CulturalAnswerInline,
        CulturalStrengthInline,
        CulturalWeaknessInline,
        CulturalAimInline,
        GenerationalAnswerInline,
        GenerationalStrengthInline,
        GenerationalWeaknessInline,
        GenerationalAimInline,
        LGBTAnswerInline,
        LGBTStrengthInline,
        LGBTWeaknessInline,
        LGBTAimInline,
        GeneralConceptAnswerInline,
        GeneralConceptStrengthInline,
        GeneralConceptWeaknessInline,
        GeneralConceptAimInline,
        CommunicationAnswerInline,
        CommunicationStrengthInline,
        CommunicationWeaknessInline,
        CommunicationAimInline,
        PersonalEngagementAnswerInline,
        PersonalEngagementStrengthInline,
        PersonalEngagementWeaknessInline,
        PersonalEngagementAimInline,
        ProfessionalPracticesAnswerInline,
        ProfessionalPracticesStrengthInline,
        ProfessionalPracticesWeaknessInline,
        ProfessionalPracticesAimInline,
        CognitiveBiasesAnswerInline,
        CognitiveBiasesStrengthInline,
        CognitiveBiasesWeaknessInline,
        CognitiveBiasesAimInline,
        BonusPostureAnswerInline,
        BonusPostureStrengthInline,
        BonusPostureWeaknessInline,
        BonusPostureAimInline,
        VosSuggestionsInline,
    ]
    list_display = ["__str__"]
    fields = ["__str__"]
    readonly_fields = ["__str__"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        pass

    def get_queryset(self, request):
        return EvaluationExpertiseProxy.objects.all().select_related("entity")


@job("default")
def create_duplicatas_task(obj_id):
    obj = ReevaluationRequest.objects.get(id=obj_id)
    # Récupérer les entités filles directement
    entity = obj.evaluation.entity
    max_level = entity.entity_level.structure.entity_level.count()
    filters = Q(pk=entity.pk)
    for i in range(1, max_level):
        filters |= Q(**{"__".join(i * ["parent_entity"]): entity})

    entities = (
        Entity.objects.filter(filters)
        .select_related("parent_entity__entity_level", "entity_level")
        .prefetch_related("children_entities")
    )

    # Récupérer toutes les évaluations à dupliquer
    evaluations = []
    for entity in entities:
        evaluation = entity.last_global_evaluation
        if evaluation and evaluation.display_version != "en-cours":
            evaluations.append(evaluation)

    # Dupliquer les évaluations et leurs objets associés dans une transaction atomique
    for evaluation in evaluations:
        with transaction.atomic():
            duplicata = Evaluation.objects.create(
                subscription=evaluation.subscription,
                display_version="en-cours",
                entity=evaluation.entity,
                sheet=evaluation.sheet,
                name=evaluation.entity.name,
                description=evaluation.description,
                created_date=now(),
                modified_by_user_date=now(),
                is_started=True,
                need_auth=evaluation.need_auth,
                is_validated_by_user=False,
                is_validated_by_admin=False,
                include_in_human_benchmark=evaluation.include_in_human_benchmark,
                display_human_introduction=evaluation.display_human_introduction,
                public_display=evaluation.public_display,
                private_display=evaluation.private_display,
                active_aggregation_with_children=evaluation.active_aggregation_with_children,
                display_aims_category=evaluation.display_aims_category,
                display_mean_score=evaluation.display_mean_score,
                share=evaluation.share,
                social_thumbnail=evaluation.social_thumbnail,
                questions_sheet=evaluation.questions_sheet,
                pdf_sheet=evaluation.pdf_sheet,
                collaborators_mail=evaluation.collaborators_mail,
                collaborators_mail_object=evaluation.collaborators_mail_object,
                mean_score=evaluation.mean_score,
                mean_score_in_business_line=evaluation.mean_score_in_business_line,
                custom_comment=evaluation.custom_comment,
                ethnicity_limit_per_file=evaluation.ethnicity_limit_per_file,
                pre_registered_filters=evaluation.pre_registered_filters,
                civility_filters_display=evaluation.civility_filters_display,
                status_filters_display=evaluation.status_filters_display,
            )
            duplicata.tags.set(evaluation.tags.all())
            duplicata.mandatory_questions.set(evaluation.mandatory_questions.all())
            duplicata.forbidden_questions.set(evaluation.forbidden_questions.all())
            duplicate_related_objects(evaluation, duplicata)


@job("default")
def send_emails_to_users(obj_id):
    obj = ReevaluationRequest.objects.get(id=obj_id)
    # Récupérer les entités filles directement
    obj_entity = obj.evaluation.entity
    max_level = obj_entity.entity_level.structure.entity_level.count()
    filters = Q(pk=obj_entity.pk)
    for i in range(1, max_level):
        filters |= Q(**{"__".join(i * ["parent_entity"]): obj_entity})

    entities = (
        Entity.objects.filter(filters)
        .select_related("parent_entity__entity_level", "entity_level")
        .prefetch_related("children_entities")
    )
    for entity in entities:
        for owner in entity.owners:
            send_reevaluation_accepted(obj.evaluation, owner.email)


def duplicate_related_objects(original, duplicata):
    # Dupliquer les objets associés à l'évaluation originale
    weaknesses = Weakness.objects.filter(evaluation=original)
    for weakness in weaknesses:
        Weakness.objects.create(
            evaluation=duplicata,
            subcategory=weakness.subcategory,
            category=weakness.category,
            description=weakness.description,
            order=weakness.order,
        )

    strengths = Strength.objects.filter(evaluation=original)

    for strength in strengths:
        Strength.objects.create(
            evaluation=duplicata,
            subcategory=strength.subcategory,
            category=strength.category,
            description=strength.description,
            order=strength.order,
        )

    answers = Answer.objects.filter(evaluation=original)
    for answer in answers:
        duplicated_sibling_answer = None
        if answer.sibling_answer:
            duplicated_sibling_answer = Answer.objects.create(
                choice=answer.choice,
                value=answer.value,
                ratio_value=answer.ratio_value,
                text_value=answer.text_value,
                currency_symbol=answer.currency_symbol,
                evaluation=duplicata,
                question=answer.question,
                comment=answer.comment,
                perimeter=answer.perimeter,
                display=answer.display,
                locked=answer.locked,
                collaborator=answer.collaborator,
                collaborator_comment=answer.collaborator_comment,
                date_answered=now(),
                date_modified=now(),
                mean_score=answer.mean_score,
                mean_score_in_business_line=answer.mean_score_in_business_line,
                blocked_aggregation=answer.blocked_aggregation,
                is_not_applicable=answer.is_not_applicable,
                is_not_followed=answer.is_not_followed,
                allow_raw_usage=answer.allow_raw_usage,
                custom_question_label=answer.custom_question_label,
                to_review=answer.to_review,
            )
        duplicated_answer = Answer.objects.create(
            sibling_answer=duplicated_sibling_answer,
            choice=answer.choice,
            value=answer.value,
            ratio_value=answer.ratio_value,
            text_value=answer.text_value,
            currency_symbol=answer.currency_symbol,
            evaluation=duplicata,
            question=answer.question,
            comment=answer.comment,
            perimeter=answer.perimeter,
            display=answer.display,
            locked=answer.locked,
            collaborator=answer.collaborator,
            collaborator_comment=answer.collaborator_comment,
            date_answered=now(),
            date_modified=now(),
            mean_score=answer.mean_score,
            mean_score_in_business_line=answer.mean_score_in_business_line,
            blocked_aggregation=answer.blocked_aggregation,
            is_not_applicable=answer.is_not_applicable,
            is_not_followed=answer.is_not_followed,
            allow_raw_usage=answer.allow_raw_usage,
            custom_question_label=answer.custom_question_label,
            to_review=answer.to_review,
        )

        sub_answers = SubAnswer.objects.filter(answer=answer)
        for sub_answer in sub_answers:
            SubAnswer.objects.create(
                value=sub_answer.value,
                subquestion=sub_answer.subquestion,
                answer=duplicated_answer,
                choice=sub_answer.choice,
                mean_score=sub_answer.mean_score,
                mean_score_in_business_line=sub_answer.mean_score_in_business_line,
                ratio_value=sub_answer.ratio_value,
            )

    scores_categories = ScoreCategory.objects.filter(evaluation=original)
    for score_category in scores_categories:
        sc = ScoreCategory.objects.create(
            value=score_category.value,
            category=score_category.category,
            evaluation=duplicata,
            detail=score_category.detail,
            key_figures_filled=score_category.key_figures_filled,
        )
        actions = Action.objects.filter(scorecategory=score_category)
        for action in actions:
            Action.objects.create(
                scorecategory=sc,
                intitules_detail=action.intitules_detail,
                descriptif_detail=action.descriptif_detail,
                intitules_aim=action.intitules_aim,
                descriptif_aim=action.descriptif_aim,
            )


class ReevaluationRequestAdmin(admin.ModelAdmin):
    model = ReevaluationRequest
    list_display = [
        "evaluation",
        "request_date",
        "is_accepted",
        "reopening_date",
    ]
    actions = ["duplicate_evaluation_action"]

    class Meta:
        fields = "__all__"

    def duplicate_evaluation_action(self, request, queryset):
        obj = queryset.first()
        if queryset.count() == 1 and obj.is_accepted == False:
            try:
                create_duplicatas_task.delay(obj.id)
                obj.reopening_date = now()
                obj.is_accepted = True
                obj.save()
                self.message_user(request, "Réouverture réussie.")
                send_emails_to_users.delay(obj.id)

            except Exception as e:
                self.message_user(
                    request, f"Erreur lors de la réouverture : {e}", level="ERROR"
                )

        elif queryset.count() > 1:
            self.message_user(
                request,
                "Veuillez sélectionner une seule évaluation pour la réouverture.",
                level="ERROR",
            )

        elif obj.is_accepted == True:
            self.message_user(
                request, "Cette requête a déjà été étudiée.", level="ERROR"
            )

    duplicate_evaluation_action.short_description = "Valider la demande de réouverture"


class ChoiceInline(MixityTabularInline):
    model = Choice
    min_num = 0
    max_num = 5
    can_delete = True


class CommentQuestionInline(TranslationTabularInline):
    model = Comment
    min_num = 0
    max_num = 5
    can_delete = True
    fields = ["description", "is_good"]


class AnswerInline(MixityTabularInline, CSSJsAdminMixin):
    model = Answer
    readonly_fields = fields = [
        "evaluation",
        "text_value",
        "value",
        "ratio_value",
        "choice",
        "choices",
        "display",
        "business_line",
        "secondary_business_lines",
    ]
    can_delete = False
    extra = 0
    form = AnswerAdminForm
    max_num = 5

    def get_queryset(self, request):
        queryset = (
            super(AnswerInline, self)
            .get_queryset(request)
            .select_related("evaluation__entity")
            .prefetch_related(
                "evaluation__entity__entity_level__structure__secondary_business_lines"
            )
        )
        queryset = queryset.order_by("evaluation__id").distinct("evaluation")
        return queryset

    def business_line(self, obj):
        return obj.evaluation.entity.entity_level.structure.business_line

    def secondary_business_lines(self, obj):
        return " | ".join(
            str(bl)
            for bl in obj.evaluation.entity.entity_level.structure.secondary_business_lines.all()
        )


class SubQuestionInline(MixityTabularInline, CSSJsAdminMixin):
    model = SubQuestion
    fields = [
        "label",
        "ui_type",
    ]
    extra = 0
    max_num = 5


class QuestionAdmin(MixityAdmin, CSSJsAdminMixin):
    model = Question
    inlines = [ChoiceInline, CommentQuestionInline, AnswerInline, SubQuestionInline]
    search_fields = ["label", "google_sheets_id"]
    list_display = [
        "google_sheets_id",
        "hierarchy",
        "label",
        "subquestions",
        "choices",
        "weight_index",
    ]
    list_filter = ["target", "category", "subcategory", "sheets"]
    fk_select_fields = ["sheets", "mandatory_tags", "forbidden_tags"]
    filter_horizontal = ("sheets", "mandatory_tags", "forbidden_tags")

    class Meta:
        fields = "__all__"

    def hierarchy(self, question):
        return f"{question.target} / {question.category.name} / {question.subcategory.name}"

    hierarchy.short_description = "Hiérarchie"

    def choices(self, obj):
        return mark_safe(
            "<br>".join(
                [f"{choice.value} - {choice.label}" for choice in obj.choices.all()]
            )
        )

    choices.short_description = "Choix"

    def comments(self, obj):
        return mark_safe(
            "<br>".join([f"{str(comment)}" for comment in obj.comments.all()])
        )

    comments.short_description = "Commentaires"

    def subquestions(self, question):
        return mark_safe(
            "<br>".join([f"{str(sub.label)}" for sub in question.subquestions.all()])
        )

    subquestions.short_description = "Sous-questions"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("category").prefetch_related(
            "comments",
            "choices",
            Prefetch("subquestions", queryset=SubQuestion.objects.order_by("order")),
        )


class QuestionInline(MixityTabularInline):
    model = Question
    fields = ("label", "order_num", "weight_index")


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "order",
        "weight_index",
        "color",
    )
    list_filter = ("subcategories",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    class Meta:
        fields = "__all__"


class SubCategoryAdmin(TranslationAdmin):
    list_display = (
        "name",
        "order",
        "color",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    class Meta:
        fields = "__all__"


class ComputedEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "region",
        "business_line",
    )

    class Meta:
        fields = "__all__"


class QuestionTagAdmin(admin.ModelAdmin):
    class Meta:
        fields = "__all__"


class SubAnswerForm(forms.ModelForm):
    model = SubAnswer
    parent_obj = None

    def __init__(self, *args, **kwargs):
        self.base_fields["subquestion"] = forms.ModelChoiceField(
            queryset=SubQuestion.objects.filter(question=self.parent_obj.question)
        )
        super(SubAnswerForm, self).__init__(*args, **kwargs)


class SubAnswerInline(MixityTabularInline):
    model = SubAnswer
    form = SubAnswerForm
    exclude = ["mean_score", "mean_score_in_business_line"]

    def get_formset(self, request, obj=None, **kwargs):
        SubAnswerForm.parent_obj = obj
        return super(SubAnswerInline, self).get_formset(request, obj, **kwargs)


class AnswerAdmin(admin.ModelAdmin, CSSJsAdminMixin):
    form = AnswerAdminForm
    inlines = [SubAnswerInline]
    search_fields = ["question__google_sheets_id", "question__id"]
    list_filter = ("evaluation__entity__name",)
    readonly_fields = [
        "question_link",
        "sibling_answer",
        "evaluation",
        "collaborator",
        "date_answered",
        "date_modified",
        "mean_score",
        "mean_score_in_business_line",
        "ratio_value",
    ]
    fields = [
        "evaluation",
        "question_link",
        "sibling_answer",
        "value",
        "ratio_value",
        "text_value",
        "mean_score",
        "mean_score_in_business_line",
        "currency_symbol",
        "comment",
        "blocked_aggregation",
        "locked",
        "is_not_applicable",
        "is_not_followed",
        "display",
        "custom_question_label",
        "to_review",
        "collaborator",
        "collaborator_comment",
        "perimeter",
        "date_answered",
        "date_modified",
    ]

    list_display = ["__str__", "question_link", "collaborator_comment"]

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and obj.question:
            if obj.question.type == "multiple_qcm":
                fields.append("choices")
            else:
                fields.append("choice")
        return fields

    def question_link(self, obj):
        url = reverse("admin:scoring_question_change", args=[obj.question.id])
        link = '<strong><a href="{}">{}</a></strong>'.format(url, obj.question)
        return mark_safe(link)

    question_link.short_description = "Question"

    def save_model(self, request, obj, form, change):
        pass  # don't actually save the parent instance

    def save_formset(self, request, form, formset, change):
        formset.save()  # this will save the children
        form.instance.save()  # form.instance is the parent

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "question__subcategory", "evaluation__entity"
        ).prefetch_related("subanswers")


class QuestionSheetAdmin(admin.ModelAdmin):
    model = QuestionSheet
    list_display = ["slug", "evaluation_count", "type", "version", "year"]
    list_filter = ["type", "year"]

    class Meta:
        fields = "__all__"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(evaluation_count=Count("evaluations"))

    def evaluation_count(self, obj):
        return obj.evaluation_count

    evaluation_count.short_description = "Nombre d'évaluations"


class QuestionSheetInline(MixityTabularInline):
    model = QuestionSheet
    # list_display = ('type', 'slug', 'version', 'date_created',)

    class Meta:
        fields = "__all__"


class QuestionSheetTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "workforce_limit",
        "is_collaborator",
    )
    inlines = (QuestionSheetInline,)

    class Meta:
        fields = "__all__"


class ActionAdmin(admin.ModelAdmin):
    class Meta:
        fields = "__all__"


class CountryDataAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }
    list_filter = ["country"]

    class Meta:
        fields = "__all__"


class EvaluationProxy(Evaluation):
    class Meta:
        proxy = True
        verbose_name = "Evaluation with Collaborators Statistics"
        verbose_name_plural = "Evaluations with Collaborators Statistics"


class EvaluationCollaboratorsMail(Evaluation):
    class Meta:
        proxy = True
        verbose_name = _("Mail des collaborateurs")
        verbose_name_plural = _("Mails des collaborateurs")


class EvaluationCollaboratorsMailAdmin(admin.ModelAdmin):
    form = EvaluationForm
    search_fields = ["entity__name"]
    list_display = [
        "entity",
        "is_validated_by_user",
        "is_validated_by_admin",
        "private_display",
        "public_display",
        "sheet",
    ]

    fieldsets = (
        (
            "Mails",
            {
                "fields": (
                    "collaborators_mail_object_fr",
                    "collaborators_mail_object_en",
                    "collaborators_mail_object_es",
                    "collaborators_mail_object_it",
                    "collaborators_mail_object_ja",
                    "collaborators_mail_object_zh_hans",
                    "collaborators_mail_object_zh_hant",
                    "collaborators_mail_fr",
                    "collaborators_mail_en",
                    "collaborators_mail_es",
                    "collaborators_mail_it",
                    "collaborators_mail_ja",
                    "collaborators_mail_zh_hans",
                    "collaborators_mail_zh_hant",
                )
            },
        ),
        # Add more fieldsets as needed
    )

    class Meta:
        fields = "__all__"


class CollaboratorsStatisticsInline(StackedInline, CSSJsAdminMixin):
    model = CollaboratorsStatistics
    fields = [
        "type",
        "status",
        "can_delete",
        "stats",
    ]
    readonly_fields = [
        "type",
        "status",
        "stats",
    ]

    def get_queryset(self, request):
        return CollaboratorsStatistics.objects.select_related("statistics")

    def has_add_permission(self, *args, **kwargs):
        return False

    def stats(self, obj):
        return mark_safe(
            render_to_string(
                "admin/statistics_admin.html",
                context={
                    "statistics": obj.statistics,
                    "vocabulary": Namsor.get_ethnicity_choices(),
                },
            )
        )


class EvaluationWithCollaboratorsStatisticsAdmin(admin.ModelAdmin):
    change_list_template = "admin/admin_collaborators_statistics_changelist.html"
    list_display = ["__str__", "sheet", "credits_used"]
    fields = ["__str__", "sheet", "credits_used"]
    readonly_fields = ["__str__", "sheet", "credits_used"]
    inlines = [CollaboratorsStatisticsInline]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credits = (None, datetime.fromtimestamp(0))

    def get_credits(self):
        if self.credits[1] + timedelta(seconds=30) < datetime.now():
            self.credits = (
                {
                    value["id"]: value["total"]
                    for value in Evaluation.objects.filter(
                        collaborators_statistics__isnull=False
                    )
                    .values("id")
                    .annotate(
                        total=Sum(
                            F("collaborators_statistics__statistics__credits_used")
                        )
                    )
                    .all()
                },
                datetime.now(),
            )
        return self.credits[0]

    class Meta:
        pass

    def get_queryset(self, request):
        return (
            EvaluationProxy.objects.filter(collaborators_statistics__isnull=False)
            .select_related("sheet")
            .distinct()
        )

    def credits_used(self, obj):
        return self.get_credits().get(obj.id)

    def has_delete_permission(self, *args, **kwargs):
        return False


class IndicatorAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "google_sheets_id",
        "type",
    ]
    autocomplete_fields = ["question"]
    search_fields = ["question__google_sheets_id", "title"]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        queryset = super().get_queryset(request)
        return queryset.select_related("question", "type")

    def google_sheets_id(self, obj):
        return obj.question.google_sheets_id

    class Meta:
        pass


class IndicatorTypeAdmin(admin.ModelAdmin):
    list_display = [
        "slug",
    ]

    class Meta:
        pass


class ExpertDeiAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "title"]
    search_fields = ["first_name", "last_name", "title"]


class AnalysisByDimensionInline(TranslationStackedInline):
    model = AnalysisByDimension
    extra = 1
    fields = ["category", "content_fr", "content_en", "content_es"]


class KeyRecommendationInline(TranslationStackedInline):
    model = KeyRecommendation
    extra = 1
    fields = ["content_fr", "content_en", "content_es"]


class AssessmentBestPracticeInline(TranslationStackedInline):
    model = AssessmentBestPractice
    extra = 1
    fields = ["content_fr", "content_en", "content_es"]


class GeneralAnalysisForm(forms.ModelForm):
    class Meta:
        model = GeneralAnalysis
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fields = [
            "content_fr",
            "content_en",
            "content_es",
            "comment_fr",
            "comment_en",
            "comment_es",
        ]
        for field in fields:
            self.fields[field].widget = TinyMCE(
                attrs={"cols": 2, "rows": 2, "height": 200}
            )


class GeneralAnalysisAdmin(MixityAdmin, CSSJsAdminMixin):
    form = GeneralAnalysisForm
    list_display = ["evaluation", "content", "comment"]
    fields = [
        "evaluation",
        "expert",
        "content_fr",
        "content_en",
        "content_es",
        "comment_fr",
        "comment_en",
        "comment_es",
    ]
    inlines = [
        AnalysisByDimensionInline,
        KeyRecommendationInline,
        AssessmentBestPracticeInline,
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "evaluation":
            kwargs["queryset"] = Evaluation.objects.select_related("entity")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProfileAdmin(MixityAdmin, CSSJsAdminMixin):
    class Meta:
        model = Profile
        fields = "__all__"


class SkillAdmin(MixityAdmin, CSSJsAdminMixin):
    class Meta:
        model = Skill
        fields = "__all__"


class ScanCollaboratorAdmin(admin.ModelAdmin):
    search_fields = [
        "user__email",
        "evaluation__entity__name",
        "evaluation__entity__entity_level__structure__juridic_name",
    ]
    list_display = [
        "get_user_email",
        "get_structure_juridic_name",
        "get_entity_name",
        "get_response",
    ]

    def get_user_email(self, obj):
        return obj.user.email

    get_user_email.short_description = "email"

    def get_structure_juridic_name(self, obj):
        return obj.evaluation.entity.entity_level.structure.juridic_name

    get_structure_juridic_name.short_description = "Nom juridique de la structure"

    def get_entity_name(self, obj):
        return obj.evaluation.entity.name

    get_entity_name.short_description = "Nom de l'entité"

    def get_response(self, obj):
        if obj.profile:
            return True
        return False

    get_response.short_description = "A répondu"


class IAScanAnalysisElementInline(TranslationStackedInline, CSSJsAdminMixin):
    model = IAScanAnalysisElement
    extra = 0

    fields = [
        "category",
        "type",
        "content_fr",
        "content_en",
        "content_es",
        "content_it",
        "content_zh_hans",
        "content_zh_hant",
        "content_ja",
    ]


class IAScanAnalysisAdmin(admin.ModelAdmin):
    search_fields = [
        "evaluation__name",
        "evaluation__entity__name",
        "evaluation__entity__entity_level__structure__juridic_name",
    ]
    list_display = [
        "evaluation", 
        "get_display_version",
        "scan_collaborator",
        "is_validated_by_admin",
    ]
    readonly_fields = [
        "evaluation",
        "scan_collaborator",
        "is_validated_by_admin",
    ]
    actions = [
        "validate_analysis",
        "regenerate_analysis",
    ]
    inlines = [
        IAScanAnalysisElementInline,
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("ia_scan_analysis_elements").select_related("evaluation")

    def get_display_version(self, obj):
        return obj.evaluation.display_version if obj.evaluation else "-"
    
    get_display_version.short_description = "Version"

    def validate_analysis(self, request, queryset):
        for analysis in queryset:
            analysis.is_validated_by_admin = True
            analysis.save()

    validate_analysis.short_description = "Valider l'analyse"

    def regenerate_analysis(self, request, queryset):
        for analysis in queryset:
            instance = IAScan.get_instance()
            user = analysis.scan_collaborator
            eval_id = user.evaluation.id
            response = instance.do_scan_analysis(eval_id, user)
            if response["status"] == "error":
                e = response["message"]
                messages.warning(
                    request, f"Erreur lors de l'analyse : {e}"
                )
            else:
                messages.success(
                    request, "Analyse terminée !"
                )
    
    regenerate_analysis.short_description = "Relancer l'analyse"



admin.site.register(IAScanAnalysis, IAScanAnalysisAdmin)
admin.site.register(ScanCollaborator, ScanCollaboratorAdmin)
admin.site.register(ExpertDei, ExpertDeiAdmin)
admin.site.register(GeneralAnalysis, GeneralAnalysisAdmin)
admin.site.register(Evaluation, EvaluationAdmin)
admin.site.register(EvaluationExpertiseProxy, EvaluationExpertiseProxyAdmin)
admin.site.register(ReevaluationRequest, ReevaluationRequestAdmin)
admin.site.register(EvaluationProxy, EvaluationWithCollaboratorsStatisticsAdmin)
admin.site.register(EvaluationCollaboratorsMail, EvaluationCollaboratorsMailAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(ComputedEvaluation, ComputedEvaluationAdmin)
admin.site.register(QuestionSheetType, QuestionSheetTypeAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(QuestionTag, QuestionTagAdmin)
admin.site.register(CountryData, CountryDataAdmin)
admin.site.register(QuestionSheet, QuestionSheetAdmin)
admin.site.register(HumanCriteria, HumanCriteriaAdmin)
admin.site.register(Indicator, IndicatorAdmin)
admin.site.register(IndicatorType, IndicatorTypeAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Skill, SkillAdmin)
