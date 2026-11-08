import io
import json
import logging
import os
from collections.abc import Iterable
from collections import defaultdict
from statistics import mean
from typing import OrderedDict

from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models.expressions import RawSQL, Subquery
from playwright.sync_api import sync_playwright
from PyPDF2 import PdfFileReader, PdfFileWriter
import asyncio
from playwright.async_api import async_playwright

from django.http import JsonResponse

# from accounts.mails import send
import uuid as uuid
from datetime import datetime
from django_rq import job
from seal.models import SealableModel
from constance import config as constanceconfig
from django.conf import settings
from django.contrib import messages
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField, When, Case, OuterRef, FloatField, Exists
from django.core.exceptions import ImproperlyConfigured
from django.core.signing import Signer
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Avg, Count, DecimalField, F, Q, Sum, Value, Prefetch
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.functions import Coalesce, Cast
from django.urls import reverse
from django.utils import timezone

from django.utils.functional import cached_property
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate, get_language
from django.utils.text import slugify
from django.utils import translation
from tempfile import NamedTemporaryFile
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from openpyxl import Workbook
from openpyxl.styles import numbers
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment, Font
from accounts.models import MixityUser, Structure, Entity
from accounts.vocabularies import (
    AGE_CHOICES,
    CIVILITY_CHOICES,
    CURRENCY_CHOICES,
    CAMPUS_CHOICE,
    SERVICE_CHOICES,
    TARGET_CHOICE,
    TYPE_CHOICES,
    INDICATOR_LABELS,
    MONTHS,
    SCAN_ROLE_CHOICE,
)

from mixity.models import ModifiedArrayField
from mixity.utils import deep_getattr
from mixity.validators import year_validator
from accounts.models import HumanCriteriaChoice
from subscriptions.models import SubscriptionPack, SubscriptionOption, Product

# fixing dev environnement where CLOUDINARY_URL is not set
from scoring.mails import alert_admin_computing

try:
    from mixity.storage import FlatRawCloudinaryStorage

    class RawStorage(FlatRawCloudinaryStorage):
        pass

except ImproperlyConfigured:

    from mixity.storage_dev import LocalOrCloudinaryRawStorage

    class RawStorage(LocalOrCloudinaryRawStorage):
        pass


logger = logging.getLogger("mixity.scoring")

SCORING_VALUES = (-2, 0, 1, 2, 3, 4, 5)
CHOICE_SCORING_VALUES = [(i, str(i)) for i in SCORING_VALUES]

MAIN_CATEGORIES_SLUGS = [
    "all",
    "gender",
    "disability",
    "cultural_diversity",
    "generational_diversity",
    "lgbt",
]

SCAN_CATEGORIES_SLUGS = [
    "general_concept",
    "communication",
    "professional_engagement",
    "professional_practice",
    "cognitive_biases",
    "bonus_posture",
]


# Related Models Functions
def default_data():
    return {
        "paygapshift": 0,
        "paygapoperatives": 0,
        "paygapmanagers": 0,
        "disabilityrate": 0,
        "scholarshipstudent": 0,
    }


def get_human_campus_short_slugs():
    return list({get_human_campus_short_slug(slug) for slug, label in CAMPUS_CHOICE})


def get_human_campus_short_slug(slug):
    return slug.split("__")[0].split("_")[1]


def get_filtered_human_campus_slugs(human_filter):
    filters = [
        choice[0]
        for choice in CAMPUS_CHOICE
        if get_human_campus_short_slug(choice[0]) in human_filter
    ]
    return filters


def header_filtered_sheet(
    ws,
    ft_title,
    ft_title2,
    ft_question,
    collab_queryset,
    selected_filters,
    ws_index,
    filter_index,
):
    # Filling collaborators
    ws[f"A{ws_index}"] = str(_("Total des répondants"))
    ws[f"A{ws_index}"].font = ft_title
    ws[f"B{ws_index}"] = str(collab_queryset.count())
    ws[f"B{ws_index}"].font = ft_question
    ws_index += 1
    # Filling filters
    if filter_index:
        ws[f"A{ws_index}"] = str(_("Filtres choisis pour le filtre n°")) + str(
            filter_index
        )
    else:
        ws[f"A{ws_index}"] = str(_("Filtres choisis"))
    ws[f"A{ws_index}"].font = ft_title

    filter_title = ""
    ws_col_index = 2
    for key, value in selected_filters.get("collab_filters", {}).items():
        if value:
            # Filter label
            for v in value:
                # Filter choices
                ws.cell(row=ws_index, column=ws_col_index).value = str(_(v["label"]))
                ws_col_index += 1
                filter_title += str(_(v["label"])) + ", "
    for key, value in selected_filters.get("collab_human_criteria", {}).items():
        # Human filter label
        if value:
            # human Filter choices
            slug_list = HumanCriteriaChoice.objects.filter(id__in=value).all()
            for slug in slug_list:
                ws.cell(row=ws_index, column=ws_col_index).value = str(_(slug.label))
                filter_title += str(_(slug.label)) + ", "
                ws_col_index += 1
    ws.append([])  # adding a blank line
    ws_index += 2
    return ws, ws_index, filter_title[:-2]


def display_exported_percentage(ws, choices_percentage, k, ws_index, ws_col_index):
    if export_get_percentage(choices_percentage, k):
        ws.cell(row=ws_index, column=ws_col_index).value = float(
            round(export_get_percentage(choices_percentage, k), 2) / 100
        )
    else:
        ws.cell(row=ws_index, column=ws_col_index).value = float(0.00)
    ws.cell(row=ws_index, column=ws_col_index).number_format = numbers.FORMAT_PERCENTAGE
    return ws


def display_current_subchoices(
    ws, sub_choices_percentage, value, ws_index, ws_col_index, new_ws_col_index
):
    current_sub_choices = export_get_percentage_subquestions(
        sub_choices_percentage, value["id"], False
    )
    if current_sub_choices:
        ws_col_index = new_ws_col_index
        for i in range(0, len(current_sub_choices)):
            if current_sub_choices[i]["value"]:
                ws.cell(row=ws_index, column=ws_col_index).value = float(
                    round(current_sub_choices[i]["value"], 2) / 100
                )
            else:
                ws.cell(row=ws_index, column=ws_col_index).value = float(0.00)
            ws.cell(row=ws_index, column=ws_col_index).number_format = (
                numbers.FORMAT_PERCENTAGE
            )
            ws_col_index += 1
    return ws, ws_index, ws_col_index


def display_current_sub_percentage(
    ws, sub_choices_qcm_percentage, value, ws_index, ws_col_index
):
    if export_get_percentage_subquestions(
        sub_choices_qcm_percentage, value["id"], True
    ):
        ws.cell(row=ws_index, column=ws_col_index).value = float(
            round(
                export_get_percentage_subquestions(
                    sub_choices_qcm_percentage,
                    value["id"],
                    True,
                ),
                2,
            )
            / 100
        )
    else:
        ws.cell(row=ws_index, column=ws_col_index).value = float(0.00)
    ws.cell(row=ws_index, column=ws_col_index).number_format = numbers.FORMAT_PERCENTAGE
    return ws


def compute_value_from_param(import_self, question, collab_queryset, parameters):
    return Answer(question_id=question.id).get_computed_value(
        evaluation=import_self,
        param=parameters,
        queryset=collab_queryset,
    )


def init_worksheet_header(ws, import_self):
    # Fit height and width style
    ws.page_setup.fitToHeight = 1
    ws.page_setup.fitToWidth = 1

    # Worksheet Title
    ws.title = "Questionnaire Mixity avec filtres"

    # Worksheet Columns
    ws.column_dimensions["A"].width = 100  # Questions and Titles Column
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 30
    ws.column_dimensions["D"].width = 30
    ws.column_dimensions["E"].width = 30
    ws.column_dimensions["F"].width = 30
    ws.column_dimensions["G"].width = 30
    ws.column_dimensions["H"].width = 30
    ws.column_dimensions["I"].width = 30

    # Getting evaluation questions
    mandatory_ids = [q.id for q in import_self.mandatory_questions.all()]
    forbidden_ids = [q.id for q in import_self.forbidden_questions.all()]
    questions = import_self.get_questions_human(
        mandatory_question_ids=mandatory_ids,
        forbidden_question_ids=forbidden_ids,
    )

    # Order questions according to the GSheet doc
    questions.sort(
        key=lambda question: (
            question.category.order,
            question.subcategory.order,
            question.order_num,
        )
    )

    # Getting list of categories
    categories = [
        c for c in import_self.get_categories_values() if c != "Vos suggestions"
    ]

    # Worksheet styles
    # Font color and size styles
    ft_title = Font(color="181b3d", size=25)
    ft_title1 = Font(color="f67273", size=20)
    ft_title2 = Font(color="8888e2", size=16)
    ft_question = Font(bold=True)

    # Tracking cell position in the worksheet
    ws_index = 1

    # Worksheet Content
    # Worksheet header
    pa = os.path.join(settings.STATICFILES_DIRS[0], "img/logo-mixity-258x73.png")
    img = Image(pa)

    # Cell A1
    ws.add_image(img, "A1")

    # Row 2 to 7
    for i in range(7):
        ws_index += 1
        if i == 5:
            ws.merge_cells(f"A1:F{ws_index}")
            ws.append([])
        else:
            ws.append([])

    return (
        ws,
        questions,
        categories,
        ft_title,
        ft_title1,
        ft_title2,
        ft_question,
        ws_index,
    )


def update_evaluation_scoring(
    evaluation, update_choices, update_comments, update_categories
):
    """
    Compute ScoreCategories (weighted average of answer's values)
    """

    start_time = timezone.now()
    # evaluation = (
    #     Evaluation.objects.select_related(
    #         "sheet",
    #         "entity__entity_level__structure__address__locality__state__country",
    #     )
    #     .prefetch_related("scores_categories")
    #     .get(pk=evaluation_id)
    # )
    # Explicit message to keep trace (warning to locate in logs)
    logger.warning(
        "EVALUATION SCORING (id: %i, type: %s)",
        evaluation.id,
        str(evaluation.sheet),
    )
    # compute choices if some answers were answered before others and needed another answer
    answers = (
        evaluation.answers.select_related("question", "choice", "evaluation")
        # Not possible anymore due to iterator() --> https://docs.djangoproject.com/fr/4.0/ref/models/querysets/
        # .prefetch_related(
        #     Prefetch("question__choices"),
        #     Prefetch(
        #         "subanswers",
        #         queryset=SubAnswer.objects.select_related("subquestion__question"),
        #     ),
        # )
        # .all()
    )
    for i, answer in enumerate(
        answers.iterator(chunk_size=settings.UPDATE_EVALUATION_SCORING_CHUNK_SIZE)
    ):
        if i % 10000 == 0:
            # For log progress display
            logger.warning(
                "EVALUATION SCORING (id: %i, type: %s, duration: %f seconds) do_compute_scores %i",
                evaluation.id,
                str(evaluation.sheet),
                (timezone.now() - start_time).total_seconds(),
                i,
            )
        answer.do_compute_scores(update_choices, update_comments, evaluation)
    logger.warning(
        "EVALUATION SCORING (id: %i, type: %s, duration: %f seconds) scores_categories",
        evaluation.id,
        str(evaluation.sheet),
        (timezone.now() - start_time).total_seconds(),
    )

    if update_categories:
        for score in evaluation.scores_categories.all():
            score.value = score.compute_score()
            score.save()
    logger.warning(
        "EVALUATION SCORING (id: %i, type: %s, duration: %f seconds) apply_ratio",
        evaluation.id,
        str(evaluation.sheet),
        (timezone.now() - start_time).total_seconds(),
    )

    evaluation.global_score = evaluation.apply_ratio()
    evaluation.save()

    # Explicit message to keep trace (warning to locate in logs)
    duration = timezone.now() - start_time
    logger.warning(
        "EVALUATION SCORING (id: %i, type: %s, duration: %f seconds) score = %.2f",
        evaluation.id,
        str(evaluation.sheet),
        duration.total_seconds(),
        evaluation.global_score,
    )


@job("default", timeout=3600)
def pre_register_filters(evaluation_id, user_email=""):
    """
    This function precompute et pre-register the needed filtered information of Human classic & campus
    """
    evaluation = Evaluation.objects.get(pk=evaluation_id)

    if evaluation:
        # List of human filters
        if (evaluation.is_human and not evaluation.is_campus) or evaluation.is_scan:
            human_filters = ["man", "woman", "non-binary", "prefer-not-to-say"]
        elif evaluation.is_human and evaluation.is_campus:
            human_filters = get_human_campus_short_slugs()

        json_filters = {}

        def prevent_save(*args, **kwargs):
            pass

        # Pre-compute scores categories
        for human_filter in human_filters:
            json_filters[human_filter] = {"global_score": 0, "scores": []}
            global_score = 0
            for sc in evaluation.scores_categories.all():
                if (
                    sc.category.slug != "your-suggestions"
                    and sc.category.slug != "bonus_posture"
                ):
                    # Compute of categories scores
                    sc.value = sc.compute_score(human_filter=human_filter)
                    sc.save = prevent_save

                    # Compute of global score
                    global_score += sc.display_value()
                    json_filters[human_filter]["scores"].append(
                        {
                            sc.category.name: {
                                "display_score": sc.display_value(),
                                "slug": sc.category.slug,
                                "color": sc.category.color,
                                # Mean score
                                "mean_score": sc._mean_score(
                                    human_filter=human_filter, in_realtime=True
                                ),
                                # Mean score in business line
                                "mean_score_business_line": sc._mean_score_in_business_line(
                                    human_filter=human_filter,
                                    in_realtime=True,
                                ),
                            }
                        }
                    )
            if evaluation.is_scan:
                filters_count = evaluation.scores_categories.filter(
                    category__slug__in=SCAN_CATEGORIES_SLUGS
                ).count()
            else:
                filters_count = evaluation.scores_categories.filter(
                    category__slug__in=MAIN_CATEGORIES_SLUGS
                ).count()

            if filters_count != 0:
                global_score /= filters_count
                json_filters[human_filter]["global_score"] = global_score

        evaluation.pre_registered_filters = json_filters
        evaluation.save(update_fields=["pre_registered_filters"])

        # Send an email to prevent the admin once the computing and saving are done
        if user_email:
            alert_admin_computing(user_email, evaluation, only_filters=True)


@job("default", timeout=3600)
def do_update_scoring(
    evaluation_id, update_choices, update_comments, update_categories, user_email=""
):
    """
    This function recompute all the scores of any evaluation and filters if it is Human
    """
    # Getting evaluation
    evaluation = (
        Evaluation.objects.select_related(
            "sheet",
            "entity__entity_level__structure__address__locality__state__country",
        )
        .prefetch_related("scores_categories")
        .get(pk=evaluation_id)
    )

    # Updating all the evaluation scores
    update_evaluation_scoring(
        evaluation, update_choices, update_comments, update_categories
    )

    # Computing pre-registering filters
    if evaluation.is_human or evaluation.is_scan:
        pre_register_filters(evaluation.pk)

    # Sending an email after updating scores and computing filters is done
    if user_email:
        alert_admin_computing(user_email, evaluation)


def export_get_percentage(results, choice_id):
    if results:
        for result in results[0]:
            if result["choice_id"] == choice_id:
                return result["value"]


def export_get_percentage_subquestions(results, subquestion_id, is_qcm):
    if results:
        for result in results[0]:
            if result["subquestion_id"] == subquestion_id:
                if is_qcm:
                    return result["value"]
                else:
                    return result["choices"]


def init_none():
    l = list()
    for i in range(0, settings.DEFAULT_ACTION_ROW_NUMBER):
        l.append(None)
    return l


def prepare_human_filters_queries(human_filters, for_collaborators, is_human):
    collab = "collaborator"
    if not is_human:
        collab = "scan_collaborator"
    human_filters_queries = []
    # Default Human Filters
    if "civility" in human_filters:
        if len(human_filters["civility"]) > 0:
            human_filters_queries.append(
                Q(civility__in=human_filters["civility"])
                if for_collaborators
                else Q(**{f"{collab}__civility__in": human_filters["civility"]})
            )
    if "age" in human_filters:
        if len(human_filters["age"]) > 0:
            human_filters_queries.append(
                Q(age__in=human_filters["age"])
                if for_collaborators
                else Q(**{f"{collab}__age__in": human_filters["age"]})
            )
    if "status" in human_filters:
        if len(human_filters["status"]) > 0:
            human_filters_queries.append(
                Q(status__in=human_filters["status"])
                if for_collaborators
                else Q(**{f"{collab}__status__in": human_filters["status"]})
            )
    if "job" in human_filters:
        if len(human_filters["job"]) > 0:
            human_filters_queries.append(
                Q(status__in=human_filters["job"])
                if for_collaborators
                else Q(**{f"{collab}__job__in": human_filters["job"]})
            )
    # Human Criteria Filters
    # if "human_criteria" in human_filters:
    #     if len(human_filters["human_criteria"]) > 0:
    #         criteriasChoices = list(HumanCriteriaChoice.objects.filter(id__in=human_filters["human_criteria"]).select_related("criteria"))
    #         criterias = dict()
    #
    #         for choice in criteriasChoices:
    #             criteria_id = choice.criteria.id  # Utiliser l'ID plutôt que l'objet
    #             if criteria_id not in criterias:
    #                 criterias[criteria_id] = []
    #             criterias[criteria_id].append(choice.id)
    #
    #         for criteria, choices in criterias.items():
    #             human_filters_queries.append(
    #                 Q(human_criteria_choices__in=HumanCriteriaChoice.objects.filter(id__in=choices))
    #                 if for_collaborators
    #                 else Q(
    #                     collaborator__human_criteria_choices__in=choices
    #                 )
    #             )
    # print(human_filters_queries)
    return human_filters_queries


def indicators_prevent_save(reset_mean_score=True, *args, **kwargs):
    pass


# Models Classes
class QuestionTag(models.Model):
    name = models.CharField(max_length=128)

    # human = models.BooleanFields(default = False)

    def __str__(self):
        return self.name


class CountryData(models.Model):
    country = models.ForeignKey(
        "address.Country",
        verbose_name=_("Pays"),
        on_delete=models.PROTECT,
        related_name="country_datas",
    )

    year = models.PositiveIntegerField(
        verbose_name=_("Année"),
        validators=[year_validator],
        default=2021,
    )

    data = JSONField(
        verbose_name="Données",
        default=default_data,
    )

    source_link = models.URLField(
        verbose_name=_("Lien de la source"),
        max_length=2048,  # Large lenght for large URL
        null=True,
        blank=True,
    )

    description = models.TextField(
        verbose_name=_("Description"),
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["year"]

    def __str__(self):
        return str(self.country) + " - " + str(self.year)


def count_collaborators_with_answers(collaborators):
    """
    Nombre de collaborateurs (distincts) qui ont au moins une réponse.

    EXISTS à la place d'une jointure avec GROUP BY / HAVING sur toutes les réponses : même résultat,
    nettement plus rapide sur les évaluations qui comptent beaucoup de collaborateurs et de réponses
    (cette valeur est calculée pour chaque évaluation affichée sur le tableau de bord).
    """
    return (
        collaborators.filter(Exists(Answer.objects.filter(collaborator=OuterRef("pk"))))
        .distinct()
        .count()
    )


class QuestionSheetType(models.Model):
    slug = models.SlugField()
    name = models.CharField(max_length=128)
    is_collaborator = models.BooleanField(default=False)
    workforce_limit = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Effectifs maximum",
    )
    category = models.ForeignKey(
        "Category",
        verbose_name="Catégorie du questionnaire",
        on_delete=models.PROTECT,
        related_name="question_sheet_types",
        null=True,
        blank=True,
    )

    suffix_company_sheet = models.CharField(
        verbose_name="Suffixe pour la fiche entreprise",
        blank=True,
        null=False,
        default="",
        max_length=32,
    )

    tag = models.CharField(
        verbose_name="Tag pour les commparaisons",
        default="global",
        max_length=32,
    )

    class Meta:
        verbose_name = _("Type de questionnaire")

    def __str__(self):
        return f"{self.name}"


class QuestionSheet(models.Model):
    type = models.ForeignKey(
        "QuestionSheetType",
        verbose_name=_("Type de questionnaire"),
        on_delete=models.PROTECT,
        related_name="question_sheets",
    )
    slug = models.SlugField()
    version = models.FloatField()
    export = models.FileField(
        null=True,
        blank=True,
        upload_to="sheets/",
        verbose_name="Export",
        storage=RawStorage,
    )
    google_sheet = JSONField(default=list, blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, null=True)
    year = models.PositiveIntegerField(
        validators=[year_validator],
        verbose_name=_("Année du référentiel"),
        default=2019,
    )

    class Meta:
        verbose_name = _("Questionnaire")
        ordering = ["slug", "version"]
        unique_together = ["slug", "version"]

    def __str__(self):
        return f"{self.slug} - v{self.version} - {self.date_created}"

    def get_data_year(self):
        return str(self.year)

    @staticmethod
    def get_new_evaluation_question_sheet(subscription_option):
        # TODO what if it has several subscriptions ?
        if not subscription_option.is_active:
            return
        if subscription_option.tags.filter(name="mixity_start").exists():
            return QuestionSheet.objects.filter(type__slug="mixity_start").last()
        return QuestionSheet.objects.filter(
            type=subscription_option.product.question_sheet_type
        ).last()


class Question(models.Model):
    sheets = models.ManyToManyField(
        "QuestionSheet",
        verbose_name=_("Questionnaire"),
        related_name="questions",
        blank=True,
    )
    sibling = models.ForeignKey(
        "self",
        verbose_name="Question reliée",
        related_name="siblings",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    label = models.TextField(verbose_name="Intitulé")
    scan_indicator_label = models.TextField(
        verbose_name="Intitulé pour indicateur Scan",
        null=True,
        blank=True,
    )
    recommandation = models.TextField(
        verbose_name="Recommandation", null=True, blank=True
    )
    indicators = models.TextField(
        verbose_name="Indicateurs à suivre", null=True, blank=True
    )
    target = models.CharField(
        max_length=20,
        verbose_name="Cible",
        default="collaborator",
        choices=TARGET_CHOICE,
    )
    help_text = models.TextField(
        verbose_name="Texte d'aide",
        blank=True,
        null=True,
    )
    subcategory = models.ForeignKey(
        "SubCategory",
        verbose_name="Sous Catégorie",
        on_delete=models.CASCADE,
        related_name="questions",
    )
    category = models.ForeignKey(
        "Category",
        verbose_name="Catégorie",
        null=True,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    order_num = models.IntegerField(
        verbose_name="numéro d'ordre",
        null=True,
        blank=True,
        db_index=True,
    )
    order_stat_subcategory = models.IntegerField(  # used to know if question go to fictive subcategorie "chiffre"
        verbose_name="numéro dans la sous categorie stat",
        null=True,
        blank=True,
        db_index=True,
    )
    weight_index = models.DecimalField(
        default=1,
        verbose_name="Indice de pondération",
        decimal_places=2,
        max_digits=3,
    )

    none_answer_value = models.IntegerField(
        verbose_name="Points en cas de réponse vide", null=True, blank=True
    )

    ask_detail = models.BooleanField(
        default=False, verbose_name="Demander des précisions sur la réponse"
    )
    aggregate_mode = models.CharField(
        max_length=128,
        blank=False,
        default="avg",
        choices=(("sum", "Somme"), ("avg", "Moyenne")),
    )
    mandatory_tags = models.ManyToManyField(
        QuestionTag,
        blank=True,
        related_name="questions_mandatory",
        verbose_name="Tags obligatoires",
    )
    forbidden_tags = models.ManyToManyField(
        QuestionTag,
        blank=True,
        related_name="questions_forbidden",
        verbose_name="Tags interdits",
    )
    theme = models.CharField(
        max_length=128, blank=True, null=True, verbose_name="Thème(s) de la question"
    )
    display = models.BooleanField(
        default=True
    )  # display the question in the questionnaire
    public_display_default = models.BooleanField(
        default=True
    )  # default display in fiche entreprise
    display_not_applicable = models.BooleanField(
        default=False
    )  # if True, a checkbox with "Not applicable" will be displayed and if checked, weight will be set to 0
    is_indicator = models.BooleanField(
        default=False
    )  # if True, a checkbox with "This indicator is not followed" will be displayed and if checked, empty_answer_mark will be chosen
    display_custom_question_label = models.BooleanField(
        default=False
    )  # if True, a custom text field next to question label will appear to allow the user to provide a custom label

    VALUE_TYPE = ("valeur", "Valeur")
    QCM_TYPE = ("qcm", "Qcm")
    TEXT_TYPE = ("text", "Texte")
    PERCENT_TYPE = ("pourcentage", "Pourcentage")
    type = models.TextField(
        default="qcm",
        # choices=(VALUE_TYPE, QCM_TYPE, TEXT_TYPE, PERCENT_TYPE), FIXME can't  because of valeur_10_20_100
    )
    """
        NOTE: if we want to take the ui type to test if this is a key figure question
        it is good to know these questions use Slider and Sq_select as a ui type
    """
    SELECT_UI_TYPE = ("select", ("Select"))
    SLIDER_UI_TYPE = ("slider", ("Slider"))
    TEXT_UI_TYPE = ("text", ("Texte"))
    SQ_DUAL_UI_TYPE = ("sq_dual", ("Sous-question double"))
    SQ_SELECT = ("sq_select", ("Sous-question select"))
    SQ_QCM = ("sq_qcm", ("Sous-question QCM"))
    ui_type = models.CharField(
        max_length=128,
        blank=True,
        default="select",
        choices=(
            SELECT_UI_TYPE,
            SLIDER_UI_TYPE,
            TEXT_UI_TYPE,
            SQ_DUAL_UI_TYPE,
            SQ_SELECT,
            SQ_QCM,
        ),
    )
    google_sheets_id = models.IntegerField(null=True)

    priority_order = models.IntegerField(
        verbose_name="Ordre de priorité", null=True, blank=True
    )

    adp_metadata = models.JSONField(null=True, blank=True, default=dict)

    skills = models.ManyToManyField(
        "scoring.Skill",
        blank=True,
        related_name="questions",
        verbose_name="Liste des compétences évalués sur cette question",
    )
    skills_weight = models.JSONField(
        verbose_name="Indices de pondération des compétences",
        default=dict,
        blank=True,
        null=True,
    )

    feedback = models.TextField(
        max_length=2048, blank=True, null=True, verbose_name=_("Solution")
    )

    class Meta:
        verbose_name = _("Question")
        ordering = ["category__order", "subcategory__order", "order_num"]

    def __str__(self):
        # label = self.label[:50] + '...' if len(self.label) > 50 else self.label
        return "{} - {} {}".format(
            self.google_sheets_id,
            self.subcategory,
            self.label,
        )

    def get_types(self):
        return self.type.split("_")

    def get_indicator(self):
        return self.indicators

    @property
    def label_html(self):
        ponctuations = [":", "?", "!", ";", "%"]
        label = self.label
        for ponctuation in ponctuations:
            label = label.__str__().replace(" " + ponctuation, " " + ponctuation)
        return label

    def get_choice_from_value_and_country(self, value, country):
        # ex self.type = 'valeur_relative_country_paygap_-5_-3_0_5_100'
        # ex self.type = 'pourcentage_relative_country_paygap_-5_-3_0_5_100'
        types = self.get_types()
        last_data = CountryData.objects.filter(country=country).last()
        if not last_data:
            return None
        elem = types[3]
        if elem not in last_data.data:
            return None
        country_value = last_data.data[elem]
        for i in range(4, len(types)):
            if value - country_value <= float(types[i]):
                return self.choices.all().order_by("order")[i - 4]
        return self.choices.all().order_by("order").last()

    def get_choice_from_value_and_question(self, value, evaluation):
        # ex self.type = 'valeur_relative_20212059_-5_-3_0_5_100'
        # ex self.type = 'pourcentage_relative_20212059_-5_-3_0_5_100'
        # ex self.type = 'valeur_ratio_20212059_-5_-3_0_5_100'
        types = self.get_types()
        try:
            related_answer = evaluation.answers.filter(
                question__google_sheets_id=int(types[2])
            ).first()
            if related_answer and related_answer.value is None:
                logger.warning(
                    "Falling back to first choice (evaluation %s, question %i)",
                    str(evaluation),
                    self.id,
                )
                return self.choices.all().order_by("order").first()
            for i in range(3, len(types)):
                if types[1] != "ratio" and value - related_answer.value <= float(
                    types[i]
                ):
                    return self.choices.all().order_by("order")[i - 3]
                elif types[
                    1
                ] == "ratio" and value * 100 / related_answer.value <= float(types[i]):
                    return self.choices.all().order_by("order")[i - 3]
            return self.choices.all().order_by("order").last()
        except Exception as e:
            logger.exception(e)
            return self.choices.all().order_by("order").last()

    def get_value_from_json_params(self, json_data, value, evaluation_id, answer):
        if json_data["mode"] == "ratio-questions":
            return self.get_value_from_json_params_and_ratio_questions(
                json_data, value, evaluation_id
            )
        elif json_data["mode"] == "subquestions-qcm-count":
            return self.get_subquestions_qcm_count_value(answer)
        return None

    @staticmethod
    def get_value_from_json_params_and_ratio_questions(json_data, value, evaluation_id):
        sum = 0
        for question in json_data["questions"]:
            try:
                question = question.split("_")
                answer = Answer.objects.get(
                    question__google_sheets_id=int(question[0]),
                    evaluation_id=evaluation_id,
                )

                if len(question) > 1 and answer:
                    subanswers = answer.subanswers.all()
                    if len(subanswers) > int(question[1]):
                        sum += subanswers[int(question[1])].value or 0.0
                elif answer:
                    sum += answer.value or 0.0
            except Answer.DoesNotExist:
                pass

        try:
            if value is None:  # No answers given => value is None
                return None
            final_value = value / sum
        except ZeroDivisionError:
            return None

        return final_value

    def get_choice_from_json_params_and_range(self, json_data, final_value):
        for index, limit in enumerate(json_data["range"]):
            if final_value <= limit:
                return self.choices.all().order_by("order")[index]
        return self.choices.all().order_by("order").last()

    def get_json_data(self):
        type = self.get_types()
        if len(type) > 2 and type[1] == "json":
            return json.loads("_".join(type[2:]))
        elif len(type) > 3 and type[2] == "json":
            return json.loads("_".join(type[3:]))

    def get_choice_from_value_and_json_params(self, value, evaluation, answer):
        """
        Exemple de type :
            pourcentage_json_{
                "mode": "ratio-questions",
                "questions": ["20213001", "202130201_1"],
                "range": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
                "attributionmode": "range"
            }
        """

        types = self.get_types()
        if len(types) > 2:
            try:
                json_data = self.get_json_data()
                final_value = self.get_value_from_json_params(
                    json_data, value, evaluation.id, answer
                )
                if "attributionmode" in json_data:
                    if isinstance(json_data["attributionmode"], dict):
                        if json_data["attributionmode"]["type"] == "tag-rule":
                            self.assign_rule_to_json_data(json_data, answer, evaluation)
                    if json_data["attributionmode"] == "range":
                        return self.get_choice_from_json_params_and_range(
                            json_data, final_value
                        )
            except Exception as e:
                logger.exception(e)
        return self.choices.all().order_by("order").last()

    def get_subquestions_qcm_count_value(self, answer):
        return answer.subanswers.aggregate(Sum("value"))["value__sum"]

    """
        We determine the rule to compute the corresponding choice by looking at evaluation tags
        If no rule is viable for the current evaluation, the answer will be ignored
    """

    def assign_rule_to_json_data(self, json_data, answer, evaluation):
        tags = set([tag.name for tag in evaluation.tags.only("name").all()])
        chosen_rule = []
        for rule in json_data["attributionmode"]["rules"]:
            if set(rule["mandatory_tags"]).issubset(tags) and not any(
                i in tags for i in rule["forbidden_tags"]
            ):
                chosen_rule = rule["rule"]
                break
        if len(chosen_rule) == 0 and not answer.is_not_applicable:
            answer.is_not_applicable = (
                True  # if no corresponding rule, we ignore the answer in the score
            )
            answer.save()
        json_data["attributionmode"] = json_data["attributionmode"]["attributionmode"]
        json_data[json_data["attributionmode"]] = chosen_rule

    def get_choice_from_value_and_answers(self, answer, evaluation):
        """
        Evaluation is passed in argument and self.evaluation is not used because select_related needs to be done only once, not for each answers.
        """

        assert (
            answer.evaluation_id == evaluation.id
        ), "This answer does not belong to the given evaluation"
        value = answer.value
        if value is None:
            return None
        types = self.get_types()
        if len(types) > 1 and (types[1] == "relative" or types[1] == "ratio"):
            if types[2] != "country":
                return self.get_choice_from_value_and_question(value, evaluation)
            else:
                try:
                    return self.get_choice_from_value_and_country(
                        value,
                        evaluation.entity.entity_level.structure.address.locality.state.country,
                    )
                except Exception as e:
                    logger.exception(e)
                    return self.choices.all().order_by("order").last()
        elif len(types) > 1 and types[1] == "json":
            return self.get_choice_from_value_and_json_params(value, evaluation, answer)
        else:
            return self.get_choice_from_value(value)

    def get_choice_from_value(self, value):
        if value is None:
            return None

        if not self.choices.all().order_by("order"):
            return None

        types = self.type.split("_")
        # ex self.type = 'pourcentage_50_60_70_80'
        # ex self.type = 'valeur_2_4_6'
        for index, limit in enumerate(types[1:]):
            if value <= float(limit):
                return self.choices.all().order_by("order")[index]

        return self.choices.all().order_by("order").last()

    def get_choice_from_subanswers(self, subanwsers, evaluation, answer):
        if (
            isinstance(subanwsers, Iterable)
            and subanwsers.count() > 0
            and isinstance(subanwsers[0], SubAnswer)
        ):
            if self.google_sheets_id == 2020021:
                if subanwsers.count() == 3:
                    non_binaires = subanwsers.filter(
                        subquestion__label__icontains="binaire"
                    ).first()
                    if not non_binaires or non_binaires.value is None:
                        return self.choices.all().order_by("order").first()
                    else:
                        return self.choices.all().order_by("order")[1]
            elif self.google_sheets_id in [
                2020038,
                2020039,
                2020040,
                20213049,
                20213050,
                20213051,
                20214060,
                20214061,
                20214062,
                20215046,
                20215047,
                20215048,
                202130511,
                202140621,
                202150481,
                20236174,
                20236155,
                20236156,
                20236157,
                20236158,
                20236159,
                20236135,
                20236136,
                20236137,
                20236138,
                20236139,
            ]:
                nb_women = (
                    subanwsers.filter(
                        Q(subquestion__label_fr__icontains="femmes")
                        | Q(subquestion__label_en__icontains="women")
                    )
                    .first()
                    .value
                )
                nb_no_binary = (
                    subanwsers.filter(
                        Q(subquestion__label_fr__icontains="binaire")
                        | Q(subquestion__label_en__icontains="binary")
                    )
                    .first()
                    .value
                )

                sum = (nb_women or 0.0) + (nb_no_binary or 0.0)

                if 40 <= sum <= 60:
                    return self.choices.all().order_by("order").first()

                elif 20 > sum or sum > 80:
                    return self.choices.all().order_by("order").last()

                else:
                    return self.choices.all().order_by("order")[1]

            elif self.google_sheets_id in [2020104, 2020130]:
                return None
            elif self.google_sheets_id == 2020053:
                for sa in subanwsers:
                    if sa.value == 1.0:
                        return self.choices.all().order_by("order").first()
            elif self.google_sheets_id in [
                2021009,
                20210090,
                2021018,
                20210091,
                20210092,
                20230109,
            ]:
                weight = {0: 5, 1: 4, 3: 3, 4: 2, 5: 1}
                if self.google_sheets_id == 2021018:
                    weight = {5: 1, 4: 2, 3: 3, 2: 4, 1: 5}
                sum = 0
                weight_sum = 0
                for subanwser in subanwsers:
                    if subanwser.choice.value in weight:
                        sum += weight[subanwser.choice.value] * subanwser.choice.value
                        weight_sum += weight[subanwser.choice.value]
                if weight_sum > 0:
                    return self.choices.filter(value=round(sum / weight_sum)).first()
                else:
                    return self.choices.first()
            elif self.google_sheets_id in [2021049, 20210491, 2021051, 20210512]:
                weight = {5: 1, 1: 5, 3: 3}
                sum = 0
                weight_sum = 0
                for subanwser in subanwsers:
                    if subanwser.choice.value in weight:
                        sum += weight[subanwser.choice.value] * subanwser.choice.value
                        weight_sum += weight[subanwser.choice.value]
                if weight_sum > 0:
                    value = round(sum / weight_sum)
                    # If the value is rounded to 2 or 4, modify it to keep working with 1, 3 or 5
                    if value in [2, 4] and (sum / weight_sum) >= value:
                        value += 1
                    elif value in [2, 4] and (sum / weight_sum) < value:
                        value -= 1
                    return self.choices.filter(value=value).first()
                else:
                    return self.choices.first()

            elif "subquestions_qcm_" in self.type:
                split = self.type.split("_")
                if len(split) > 2 and split[2] == "json":
                    return self.get_choice_from_value_and_json_params(
                        0.0, evaluation, answer
                    )
                sum = subanwsers.aggregate(Sum("value"))["value__sum"]
                for i in range(2, len(split)):
                    if sum <= float(split[i]):
                        return self.choices.all()[i - 2]
                return self.choices.first()

            return self.choices.all().order_by("order").last()


class SubQuestion(models.Model):
    question = models.ForeignKey(
        "Question",
        on_delete=models.CASCADE,
        blank=True,
        null=False,
        related_name="subquestions",
    )
    label = models.CharField(max_length=512)
    ui_type = models.CharField(
        max_length=128,
        blank=True,
        default="pourcentage",
    )
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Sous question"
        verbose_name_plural = "Sous questions"
        ordering = ("order", "label")

    def __str__(self):
        return self.label

    @property
    def label_html(self):
        ponctuations = [":", "?", "!", ";", "%"]
        label = self.label
        for ponctuation in ponctuations:
            label = label.__str__().replace(" " + ponctuation, " " + ponctuation)
        return label


class SubAnswer(models.Model):
    value = models.FloatField(blank=True, null=True)
    subquestion = models.ForeignKey(
        "SubQuestion",
        on_delete=models.CASCADE,
        blank=True,
        null=False,
        related_name="subanswers",
    )
    answer = models.ForeignKey(
        "Answer",
        on_delete=models.CASCADE,
        blank=True,
        null=False,
        related_name="subanswers",
    )
    choice = models.ForeignKey(
        "SubquestionChoice",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subanswers",
    )
    mean_score = models.FloatField(
        null=True,
        default=None,
        verbose_name=_("Score moyen dans mon secteur"),
    )
    mean_score_in_business_line = models.FloatField(
        null=True,
        default=None,
        verbose_name=_("Score moyen dans toutes les entreprises"),
    )
    ratio_value = models.FloatField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Valeur de ratio"),
    )

    class Meta:
        verbose_name = "Sous-Réponse"
        verbose_name_plural = "Sous-Réponses"
        ordering = ("subquestion__order",)

    @property
    def get_value_from_json_params(self):
        if self.ratio_value is not None:
            return self.ratio_value
        try:
            json_data = self.answer.question.get_json_data()
            self.ratio_value = self.answer.question.get_value_from_json_params(
                json_data, self.value, self.answer.evaluation_id, self.answer
            )
            if self.ratio_value:
                self.ratio_value *= 100
            self.save()
            return self.ratio_value
        except Exception as e:
            logger.exception(e)
            return None

    @property
    def get_mean_score(self):
        if self.mean_score is None:
            self.mean_score = self._mean_score()
            if self.mean_score:
                self.save()
        return self.mean_score

    def _mean_score(self):
        # FIXME should it be default value to 1 for non answered ?
        # FIXME should it be validated to be in the mean ? evaluation__is_validated_by_user=True
        if self.subquestion.question.google_sheets_id == 2020104:
            subanswers = SubAnswer.objects.filter(
                subquestion=self.subquestion,
            )
            if "Baby Boomers" in self.subquestion.label:
                answers = Answer.objects.filter(question__google_sheets_id=10104)
            elif "GenX" in self.subquestion.label:
                answers = Answer.objects.filter(question__google_sheets_id=10103)
            elif "GenY" in self.subquestion.label:
                answers = Answer.objects.filter(question__google_sheets_id=10102)
            else:
                answers = Answer.objects.filter(question__google_sheets_id=10101)

            subanswers_sum = subanswers.aggregate(Sum("value"))["value__sum"]
            answers_sum = answers.aggregate(Sum("value"))["value__sum"]
            subanswers_count = subanswers.count()
            answers_count = answers.count()

            if answers_count == 0 and subanswers_count == 0:
                return 0

            elif answers_count == 0:
                mean_score = float(subanswers_sum) / float(subanswers_count)
                return mean_score

            elif subanswers_count == 0:
                mean_score = float(answers_sum) / float(answers_count)
                return mean_score

            else:
                mean_score = float(answers_sum + subanswers_sum) / float(
                    answers_count + subanswers_count
                )

                return mean_score

        else:
            subanswers_list = SubAnswer.objects.filter(
                subquestion=self.subquestion,
            )
            try:
                json_data = self.answer.question.get_json_data()
                if json_data["mode"] is not None:
                    sum = 0
                    count = 0
                    for sb in subanswers_list:
                        val = sb.get_value_from_json_params
                        if val:
                            sum += val
                        count += 1
                    return sum / count
            except Exception as e:
                logger.exception(e)
            mean_score = subanswers_list.aggregate(Avg("value"))["value__avg"]

            return mean_score

    @property
    def get_mean_score_in_business_line(self):
        if not self.mean_score_in_business_line:
            self.mean_score_in_business_line = self._mean_score_in_business_line()
            if self.mean_score_in_business_line:
                self.save()
        return self.mean_score_in_business_line

    def _mean_score_in_business_line(self):
        # FIXME should it be default value to 1 for non answered ?
        # FIXME should it be validated to be in the mean ? evaluation__is_validated_by_user=True
        if self.subquestion.question.google_sheets_id == 2020104:
            subanswers = SubAnswer.objects.filter(subquestion=self.subquestion).filter(
                Q(
                    answer__evaluation__entity__entity_level__structure__business_line=self.answer.evaluation.entity.entity_level.structure.business_line
                )
                | Q(
                    answer__evaluation__entity__entity_level__structure__secondary_business_lines=self.entity.entity_level.structure.business_line
                )
            )
            if "Baby Boomers" in self.subquestion.label:
                answers = Answer.objects.filter(
                    question__google_sheets_id=10104
                ).filter(
                    Q(
                        evaluation__entity__entity_level__structure__business_line=self.answer.evaluation.entity.entity_level.structure.business_line
                    )
                    | Q(
                        evaluation__entity__entity_level__structure__secondary_business_lines=self.entity.entity_level.structure.business_line
                    )
                )
            elif "GenX" in self.subquestion.label:
                answers = Answer.objects.filter(
                    question__google_sheets_id=10103
                ).filter(
                    Q(
                        evaluation__entity__entity_level__structure__business_line=self.answer.evaluation.entity.entity_level.structure.business_line
                    )
                    | Q(
                        evaluation__entity__entity_level__structure__secondary_business_lines=self.entity.entity_level.structure.business_line
                    )
                )
            elif "GenY" in self.subquestion.label:
                answers = Answer.objects.filter(
                    question__google_sheets_id=10102
                ).filter(
                    Q(
                        evaluation__entity__entity_level__structure__business_line=self.answer.evaluation.entity.entity_level.structure.business_line
                    )
                    | Q(
                        evaluation__entity__entity_level__structure__secondary_business_lines=self.entity.entity_level.structure.business_line
                    )
                )
            else:
                answers = Answer.objects.filter(
                    question__google_sheets_id=10101
                ).filter(
                    Q(
                        evaluation__entity__entity_level__structure__business_line=self.answer.evaluation.entity.entity_level.structure.business_line
                    )
                    | Q(
                        evaluation__entity__entity_level__structure__secondary_business_lines=self.entity.entity_level.structure.business_line
                    )
                )

            subanswers_sum = subanswers.aggregate(Sum("value"))["value__sum"]
            answers_sum = answers.aggregate(Sum("value"))["value__sum"]
            subanswers_count = subanswers.count()
            answers_count = answers.count()

            if answers_count == 0 and subanswers_count == 0:
                return 0

            elif answers_count == 0:
                mean_score_in_business_line = float(subanswers_sum) / float(
                    subanswers_count
                )
                return mean_score_in_business_line

            elif subanswers_count == 0:
                mean_score_in_business_line = float(answers_sum) / float(answers_count)
                return mean_score_in_business_line

            else:
                mean_score_in_business_line = float(
                    answers_sum + subanswers_sum
                ) / float(answers_count + subanswers_count)
                return mean_score_in_business_line

        else:
            subanswers_list = SubAnswer.objects.filter(
                subquestion=self.subquestion
            ).filter(
                Q(
                    answer__evaluation__entity__entity_level__structure__business_line=self.answer.evaluation.entity.entity_level.structure.business_line
                )
                | Q(
                    answer__evaluation__entity__entity_level__structure__secondary_business_lines=self.answer.evaluation.entity.entity_level.structure.business_line
                )
            )
            try:
                json_data = self.answer.question.get_json_data()
                if json_data["mode"] is not None:
                    sum = 0
                    count = 0
                    for sb in subanswers_list:
                        val = sb.get_value_from_json_params
                        if val:
                            sum += val
                        count += 1
                    return sum / count
            except Exception as e:
                logger.exception(e)
            """
            get the average scores in the main area of the business of this subanswer

            """
            mean_score_in_business_line = subanswers_list.aggregate(Avg("value"))[
                "value__avg"
            ]

            return mean_score_in_business_line

    # def save(self, save_ratio_value=False, save_mean_score=False, *args, **kwargs):
    #     if not save_ratio_value and not save_mean_score:
    #         self.ratio_value = None
    #     super(SubAnswer, self).save()
    #     if not save_mean_score and not save_ratio_value:
    #         SubAnswer.objects.filter(subquestion_id=self.subquestion_id).filter(
    #             Q(
    #                 answer__evaluation__structure__business_line=self.answer.evaluation.structure.business_line
    #             )
    #             | Q(
    #                 answer__evaluation__structure__secondary_business_lines=self.answer.evaluation.structure.business_line
    #             )
    #         ).update(mean_score_in_business_line=None)
    #         SubAnswer.objects.filter(subquestion_id=self.subquestion_id).update(
    #             mean_score=None
    #         )


class Category(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name=_("Nom"),
    )
    slug = models.CharField(
        max_length=50,
        verbose_name="Slug",
    )
    order = models.IntegerField(default=1, editable=False)
    weight_index = models.DecimalField(
        verbose_name="Indice de pondération",
        decimal_places=2,
        max_digits=5,
    )
    color = models.CharField(
        max_length=50,
        verbose_name="Couleur",
        default="#EBEAEA",  # light grey
        blank=True,
    )

    class Meta:
        verbose_name = _("Catégorie de diversité")
        verbose_name_plural = _("Catégories de diversité")
        ordering = ("order",)

    def __str__(self):
        return ugettext(self.name)

    def get_next(self, sheet):
        return Category.objects.filter(
            subcategories__questions__sheets__in=[sheet], order__gt=self.order
        ).first()

    def get_next_from_evaluation(self, evaluation, target=None):
        categories = Category.objects.filter(
            subcategories__questions__in=evaluation.get_questions_from_answers,
            order__gt=self.order,
            slug__in=MAIN_CATEGORIES_SLUGS,
        )
        if target:
            categories = categories.filter(subcategories__questions__target=target)
        return categories.first()

    def first_subcategory(self, sheet):
        return SubCategory.objects.filter(
            questions__sheets__in=[sheet], category=self
        ).first()

    def first_subcategory_from_evaluation(self, evaluation, target=None):
        questions = evaluation.get_questions_from_answers.filter(
            (Q(order_stat_subcategory__isnull=True) | Q(order_stat_subcategory=0)),
            category=self,
        )
        if target:
            questions = questions.filter(target=target)
        return SubCategory.objects.filter(
            questions__in=questions,
            categories=self,
        ).first()

    def has_key_figures(self, evaluation):
        return (
            Answer.objects.filter(
                evaluation=evaluation,
                question__order_stat_subcategory__gte=1,
                question__category=self,
            ).first()
            is not None
        )


class SubCategory(models.Model):
    STR_CACHE = dict()

    categories = models.ManyToManyField(
        "Category",
        blank=True,
        verbose_name=_("Catégories"),
        related_name="subcategories",
    )
    name = models.CharField(
        max_length=50,
        verbose_name=_("Nom"),
    )
    short_name = models.CharField(
        max_length=20,
        verbose_name="Nom court",
    )
    order = models.IntegerField(default=0)
    slug = models.CharField(
        max_length=50,
        verbose_name="Slug",
    )
    color = models.CharField(
        max_length=50,
        verbose_name=("Couleur"),
        default="#EBEAEA",  # light grey
        blank=True,
    )

    class Meta:
        verbose_name = _("Sous-catégorie de diversité")
        verbose_name_plural = "Sous-catégories de diversité"
        ordering = ("order",)

    def __str__(self):
        # This should normaly use an lru_cache, but it's breaking when trying to print an object without pk.
        # So this new implementation is fixing that by preventing caching objects with a None pk.
        if self.pk in self.STR_CACHE:
            return self.STR_CACHE[self.pk]
        label = ugettext(self.name)
        if self.pk is not None:
            self.STR_CACHE[self.pk] = label
        return label

    def get_next(self, sheet):
        next_in_same_cat = SubCategory.objects.filter(
            category=self.category, questions__sheets__in=[sheet], order__gt=self.order
        ).first()
        next_in_next_cat = SubCategory.objects.filter(
            category__order__gt=self.category.order,
            questions__sheets__in=[sheet],
            order__gt=self.order,
        ).first()
        return next_in_same_cat or next_in_next_cat

    def get_next_from_evaluation(self, evaluation, category, target=None):
        questions = evaluation.get_questions_from_answers.filter(
            Q(order_stat_subcategory__isnull=True) | Q(order_stat_subcategory=0),
        )
        if target:
            questions = questions.filter(target=target)
        next_in_same_cat = (
            SubCategory.objects.filter(
                categories=category,
                questions__in=questions,
                order__gt=self.order,
            )
            .annotate(
                num_questions_same_category=Count(
                    "questions", filter=Q(questions__category=category)
                )
            )
            .filter(num_questions_same_category__gt=0)
            .first()
        )
        next_in_next_cat = SubCategory.objects.filter(
            categories__order__gt=category.order,
            questions__in=questions,
            order__gt=self.order,
        ).first()
        return (True, next_in_same_cat) or (False, next_in_next_cat)


class Choice(models.Model):
    value = models.IntegerField(
        choices=CHOICE_SCORING_VALUES,
        verbose_name="Valeur",
    )
    label = models.TextField(
        verbose_name="Intitulé",
    )
    question = models.ForeignKey(
        Question,
        models.CASCADE,
        related_name="choices",
        verbose_name="Question",
    )
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Choix"
        verbose_name_plural = "Choix"
        ordering = (
            "question",
            "order",
        )

    def __str__(self):
        return self.label


class SubquestionChoice(models.Model):
    value = models.IntegerField(
        choices=CHOICE_SCORING_VALUES,
        verbose_name=("Valeur"),
    )
    label = models.TextField(
        verbose_name=("Intitulé"),
    )
    subquestion = models.ForeignKey(
        SubQuestion,
        models.CASCADE,
        related_name="choices",
        verbose_name=("Sous-question"),
    )
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Choix"
        verbose_name_plural = "Choix"
        ordering = (
            "subquestion",
            "order",
        )

    def __str__(self):
        return self.label


class Answer(SealableModel):
    """
    Table intermédiaire pour établir l'unicité de choix de réponse pour une Question reliée à
    une évaluation pour ne pas que l'on ne puisse pas répondre plusieurs fois à la question
    avec l'installation d'un <unique_together>
    """

    choice = models.ForeignKey(
        Choice, on_delete=models.PROTECT, blank=True, null=True, related_name="answers"
    )
    # Exist only for multiple_qcm in scan
    choices = models.ManyToManyField(
        Choice, blank=True, related_name="answers_multiple_qcm"
    )
    value = models.FloatField(blank=True, null=True)
    ratio_value = models.FloatField(blank=True, null=True)
    text_value = models.TextField(blank=True, null=True)
    currency_symbol = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Symbole monétaire",
        choices=CURRENCY_CHOICES,
    )
    evaluation = models.ForeignKey(
        "Evaluation", on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        "Question",
        on_delete=models.PROTECT,
        blank=True,
        null=False,
        related_name="answers",
    )
    sibling_answer = models.ForeignKey(
        "self",
        verbose_name="Réponse reliée",
        related_name="siblings",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    comment = models.ForeignKey(
        "Comment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="answers",
    )
    perimeter = models.TextField(blank=True, null=True, verbose_name="perimeter")
    display = models.BooleanField(default=False, verbose_name="Afficher")
    locked = models.BooleanField(default=False, verbose_name="Verrouiller")
    collaborator = models.ForeignKey(
        "Collaborator",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="answers",
    )
    scan_collaborator = models.ForeignKey(
        "ScanCollaborator",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="answers",
    )
    collaborator_comment = models.TextField(
        blank=True,
        null=True,
    )
    date_answered = models.DateTimeField(default=None, null=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True)

    mean_score = models.FloatField(
        null=True,
        default=None,
        verbose_name=_("Score moyen dans mon secteur"),
    )
    mean_score_in_business_line = models.FloatField(
        null=True,
        default=None,
        verbose_name=_("Score moyen dans toutes les entreprises"),
    )
    blocked_aggregation = models.BooleanField(
        default=False
    )  # if True, the answer will not take child's aggregated values
    is_not_applicable = models.BooleanField(
        default=False
    )  # if True, question weight set to 0

    is_not_followed = models.BooleanField(
        default=False
    )  # if True, answer is ignored and empty_answer_mark is chosen instead
    allow_raw_usage = models.BooleanField(
        default=False
    )  # if True, answer can be transmitted raw with consent of collaborator
    custom_question_label = models.TextField(
        blank=True,
        null=True,
    )
    to_review = models.BooleanField(
        default=False,
        verbose_name=_("À revoir"),
    )
    skills_values = ArrayField(
        models.FloatField(blank=True, null=True), blank=True, null=True, default=list
    )

    class Meta:
        unique_together = (("question", "evaluation", "collaborator"),)
        verbose_name = _("Réponse")
        verbose_name_plural = _("Réponses")

    def __str__(self):
        return "{} - Question {} - Evaluation {}".format(
            self.question.subcategory, self.question_id, self.evaluation_id
        )

    def save(self, *args, **kwargs):
        """
        On surchage la méthode save() pour automatiquement relier l'Answer à la question
        :param args:
        :param kwargs:
        :return: rien
        """
        if self.choice:
            self.question_id = self.choice.question_id
        elif not self.question_id:
            raise Exception("Answer without Question")

        self.ratio_value = self.compute_ratio()
        super().save(*args, **kwargs)

    def do_compute_scores(self, update_choices, update_comments, evaluation):
        """
        Evaluation is passed in argument and self.evaluation is not used because select_related needs to be done only once, not for each answers.
        """
        assert (
            self.evaluation_id == evaluation.id
        ), "This answer does not belong to the given evaluation"
        if update_choices and not self.locked:
            if self.subanswers.exists():
                self.choice = self.question.get_choice_from_subanswers(
                    self.subanswers.all(), evaluation, self
                )
            elif self.choices.count() > 0:
                self.value = self.choices.aggregate(
                    sum_choices=Sum(
                        Case(
                            When(
                                value__lt=0, then=Value(0)
                            ),  # Si la valeur est négative, remplace par 0
                            default=F("value"),  # Sinon, garde la valeur
                            output_field=models.FloatField(),  # Précise le type de sortie
                        )
                    )
                )["sum_choices"]
                self.save()
            elif (
                len(self.question.get_types()) >= 1
                and self.question.get_types()[0] != "qcm"
            ):
                self.choice = self.question.get_choice_from_value_and_answers(
                    self, evaluation
                )
        if update_comments:
            self.comment = None
            if self.choice:
                if self.choice.value == 5:
                    self.comment = Comment.objects.filter(
                        question_id=self.question_id, is_good=True
                    ).first()  # good comment
                elif 0 <= self.choice.value <= 1:
                    self.comment = Comment.objects.filter(
                        question_id=self.question_id, is_good=False
                    ).first()  # bad comment

        if update_choices or update_comments:
            self.save()

    def get_computed_value(self, evaluation, param, queryset=None):
        from scoring.indicators_utils import HumanResultsPerIndicator

        try:
            # IMPORTANT REFONTE : HumanResultsPerIndicator
            human_instance = HumanResultsPerIndicator(
                json.loads(param), self.question_id, evaluation, queryset
            )
            return human_instance.get_results()
        except Exception as e:
            logger.exception(e)
            return None

    def compute_ratio(self):
        try:
            json_data = self.question.get_json_data()

            if (
                json_data
                and self.value is not None
                and json_data["mode"] == "ratio-questions"
            ):
                # We get the computed value depending on the JSON parameters provided
                ratio_value = self.question.get_value_from_json_params(
                    json_data, self.value, self.evaluation_id, self
                )

                if ratio_value is not None:
                    return round(ratio_value * 100, 2)

        except json.decoder.JSONDecodeError:
            pass

    @property
    def get_related_value(self):
        ty = self.question.type.split("_")
        if len(ty) >= 3:
            if ty[2] == "country":
                try:
                    return (
                        CountryData.objects.filter(
                            country=self.evaluation.entity.entity_level.structure.address.locality.state.country
                        )
                        .last()
                        .data[ty[3]]
                    )
                except Exception as e:
                    logger.exception(e)
            else:
                try:
                    return Answer.objects.get(
                        evaluation=self.evaluation,
                        answer__question__google_sheets_id=int(ty[2]),
                    ).value
                except Exception as e:
                    logger.exception(e)
        return _("ND*")

    @property
    def get_description_display(self):
        if not self.comment:
            return self.question.label

        if "{}" in self.comment.description:
            if len(self.comment.description.split("{}")) == 3:
                value = self.value
                if value and value >= 10.0:
                    value = round(value)
                value2 = self.get_related_value
                if value2 and value2 >= 10.0:
                    value2 = round(value2)
                display = self.comment.description.format(value, value2)
            else:
                tmp_value = _("ND*")
                if not self.value and self.subanswers.exists():
                    tmp_value = self.subanswers.first().value
                value = self.value
                if value and value >= 10.0:
                    value = round(value)
                if type(tmp_value) == float and tmp_value >= 10.0:
                    tmp_value = round(tmp_value)
                if value is not None:
                    display = self.comment.description.format(value)
                else:
                    display = self.comment.description.format(tmp_value)
            return display
        display = self.comment.description
        return display

    @property
    def get_ordered_subanswers(
        self,
    ):  # Permet de récupérer les réponses ordonnées dans les templates
        if (
            self.subanswers is not None
            and self.question.sheets.first().type.slug != "mixity_international"
        ):
            return self.subanswers.order_by("subquestion__label")
        else:
            return self.subanswers.all()

    @property
    def fake_subanswer(self):
        strs = {
            "10104": "Baby Boomers",
            "10103": "GenX",
            "10102": "GenY",
            "10101": "Millénials",
        }
        g_s = str(self.question.google_sheets_id)
        if g_s not in strs:
            return None
        sq = SubQuestion.objects.filter(
            question__google_sheets_id=2020104, label__icontains=strs[g_s]
        ).first()
        if sq is None:
            return None
        sa = SubAnswer(value=self.value, answer=self, subquestion=sq)
        return sa

    @property
    def get_mean_score(self):
        if not self.mean_score:
            self.mean_score = self._mean_score()
            if self.mean_score:
                self.save()
        return self.mean_score

    def _mean_score(self):
        # FIXME should it be default value to 1 for non answered ?
        if self.question.google_sheets_id in [10101, 10102, 10103, 10104]:
            fk_sa = self.fake_subanswer
            if fk_sa is None:
                return 0

            mean_score = fk_sa.get_mean_score

            return mean_score

        elif self.question.google_sheets_id in [20213002, 20213006]:
            sum = 0
            number = 0

            answers = Answer.objects.select_related(
                "evaluation__entity__entity_level__structure"
            ).filter(question__google_sheets_id=self.question.google_sheets_id)

            for answer in answers:
                workforce = answer.evaluation.get_workforce_from_evaluation
                if answer and answer.value and workforce:
                    sum += answer.value * 100 / workforce
                    number += 1
            if number == 0:
                return None

            mean_score = sum / number

            return mean_score

        else:
            answers = Answer.objects.filter(
                evaluation__is_validated_by_admin=True,
                question=self.question,
            )

            try:
                json_data = self.question.get_json_data()

                if json_data and json_data["mode"] == "ratio-questions":
                    mean_score = answers.aggregate(Avg("ratio_value"))[
                        "ratio_value__avg"
                    ]

                else:
                    mean_score = answers.aggregate(Avg("value"))["value__avg"]

            except json.decoder.JSONDecodeError:
                mean_score = answers.aggregate(Avg("value"))["value__avg"]

            return mean_score

    @property
    def get_mean_score_in_business_line(self):
        if not self.mean_score_in_business_line:
            self.mean_score_in_business_line = self._mean_score_in_business_line()
            if self.mean_score_in_business_line:
                self.save()
        return self.mean_score_in_business_line

    def _mean_score_in_business_line(self):
        # FIXME should it be default value to 1 for non answered ?
        if self.question.google_sheets_id in [10101, 10102, 10103, 10104]:
            fk_sa = self.fake_subanswer
            if fk_sa is None:
                return 0

            mean_score_in_business_line = fk_sa.get_mean_score_in_business_line
            return mean_score_in_business_line

        elif self.question.google_sheets_id in [20213002, 20213006]:
            sum = 0
            number = 0

            """
            get all the same answer of evaluations with the same business line
            """
            answers = Answer.objects.select_related("evaluation").filter(
                question__google_sheets_id=self.question.google_sheets_id
            )

            answers = answers.filter(
                Q(
                    evaluation__entity__entity_level__structure__business_line=self.evaluation.entity.entity_level.structure.business_line
                )
                | Q(
                    evaluation__entity__entity_level__structure__secondary_business_lines=self.evaluation.entity.entity_level.structure.business_line
                )
            )

            for answer in answers:
                workforce = answer.evaluation.get_workforce_from_evaluation
                if answer and answer.value and workforce:
                    sum += answer.value * 100 / workforce
                    number += 1

            if number == 0:
                return None

            mean_score_in_business_line = sum / number

            return mean_score_in_business_line

        else:
            answers = Answer.objects.filter(
                question=self.question,
                evaluation__is_validated_by_admin=True,
            )

            if not answers:
                return None

            answers = answers.filter(
                Q(
                    evaluation__entity__entity_level__structure__business_line=self.evaluation.entity.entity_level.structure.business_line
                )
                | Q(
                    evaluation__entity__entity_level__structure__secondary_business_lines=self.evaluation.entity.entity_level.structure.business_line
                )
            )

            try:
                json_data = self.question.get_json_data()

                if json_data and json_data["mode"] == "ratio-questions":
                    mean_score_in_business_line = answers.aggregate(Avg("ratio_value"))[
                        "ratio_value__avg"
                    ]

                else:
                    mean_score_in_business_line = answers.aggregate(Avg("value"))[
                        "value__avg"
                    ]

            except json.decoder.JSONDecodeError:
                mean_score_in_business_line = answers.aggregate(Avg("value"))[
                    "value__avg"
                ]

            return mean_score_in_business_line

    @cached_property
    def sibling(self):
        if self.sibling_answer:
            return self.sibling_answer

        if self.question.sibling is None:
            return None

        sibling_answer = (
            Answer.objects.filter(
                question_id=self.question.sibling_id,
                evaluation__entity__entity_level__structure=self.evaluation.entity.entity_level.structure,
                evaluation__modified_by_user_date__lt=self.evaluation.modified_by_user_date,
                evaluation__public_display=True,
            )
            .exclude(evaluation=self.evaluation)
            .select_related("evaluation__sheet")
            .order_by("evaluation__modified_by_user_date")
            .last()
        )

        if sibling_answer:
            self.sibling_answer = sibling_answer
            self.save()

        return sibling_answer

    @cached_property
    def sibling_value(self):
        return None
        # return self.sibling.value if self.sibling else None

    @cached_property
    def sibling_year(self):
        sibling = self.sibling
        if sibling is None:
            return self.evaluation.sheet.year - 1
        return sibling.evaluation.sheet.year


class Comment(models.Model):
    description = models.TextField()
    question = models.ForeignKey(
        "Question",
        on_delete=models.PROTECT,
        related_name="comments",
        null=True,
        blank=True,
    )
    is_good = models.BooleanField(default=False)

    def __str__(self):
        description = self.description
        status = "++" if self.is_good else "--"
        return "{} {}".format(status, description)


class Aim(models.Model):
    description = models.TextField(null=True, blank=True)
    subcategory = models.ForeignKey(
        "SubCategory",
        verbose_name="Sous Catégorie",
        on_delete=models.PROTECT,
        related_name="aims",
        null=True,
        blank=True,
    )
    custom_title = models.TextField(
        verbose_name="Titre customisé",
        blank=True,
        null=False,
    )
    category = models.ForeignKey(
        "Category",
        verbose_name="Catégorie",
        null=True,
        on_delete=models.PROTECT,
        related_name="aims",
    )
    evaluation = models.ForeignKey(
        "Evaluation",
        models.CASCADE,
        related_name="aims",
        verbose_name="Evaluation",
    )
    answer = models.ForeignKey(
        "Answer",
        models.CASCADE,
        related_name="aims",
        verbose_name="Answer",
        null=True,
        blank=True,
    )
    order = models.IntegerField(verbose_name=_("Ordre"), default=0)
    priority_value = models.IntegerField(
        verbose_name=_("Valeur de priorité"), default=0, editable=False
    )
    is_auto_generate = models.BooleanField(
        default=False, verbose_name="Généré automatiquement"
    )
    objective = models.OneToOneField(
        to="lead.Objective",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="objective",
        verbose_name=_("Objectif"),
    )

    class Meta:
        verbose_name = _("Objectif")
        verbose_name_plural = _("Objectifs")
        ordering = ("order", "subcategory__order")


class Strength(models.Model):
    description = models.TextField(null=True, blank=True)
    subcategory = models.ForeignKey(
        "SubCategory",
        verbose_name="Sous-Catégorie",
        on_delete=models.PROTECT,
        related_name="strengths",
        null=True,
        blank=True,
    )
    custom_title = models.TextField(
        verbose_name="Titre customisé",
        blank=True,
        null=False,
    )
    category = models.ForeignKey(
        "Category",
        verbose_name="Catégorie",
        null=True,
        on_delete=models.PROTECT,
        related_name="strengths",
    )
    evaluation = models.ForeignKey(
        "Evaluation",
        models.CASCADE,
        related_name="strengths",
        verbose_name="Evaluation",
    )
    order = models.IntegerField(verbose_name=_("Ordre"), default=0)

    class Meta:
        verbose_name = _("Point fort")
        verbose_name_plural = _("Points forts")
        ordering = ("order", "subcategory__order")


class Weakness(models.Model):
    description = models.TextField()
    subcategory = models.ForeignKey(
        "SubCategory",
        verbose_name="Sous-Catégorie",
        on_delete=models.PROTECT,
        related_name="weaknesses",
        null=True,
        blank=True,
    )
    custom_title = models.TextField(
        verbose_name="Titre customisé",
        blank=True,
        null=False,
    )
    category = models.ForeignKey(
        "Category",
        verbose_name="Catégorie",
        null=True,
        on_delete=models.PROTECT,
        related_name="weaknesses",
    )
    evaluation = models.ForeignKey(
        "Evaluation",
        models.CASCADE,
        related_name="weaknesses",
        verbose_name="Evaluation",
    )
    order = models.IntegerField(verbose_name=_("Ordre"), default=0)

    class Meta:
        verbose_name = _("Point faible")
        verbose_name_plural = _("Points faibles")
        ordering = ("order", "subcategory__order")


class ReevaluationRequest(models.Model):
    evaluation = models.ForeignKey(
        "scoring.Evaluation",
        related_name="reevaluation",
        on_delete=models.CASCADE,
    )
    request_date = models.DateField(
        auto_now_add=True,
    )
    is_accepted = models.BooleanField(
        default=False,
        verbose_name="Réouverture acceptée",
    )
    reopening_date = models.DateField(
        blank=True,
        null=True,
    )


class EvaluationManager(models.Manager):
    def random_and_validated_by_admin(self):
        return self.filter(is_validated_by_admin=True).order_by("?")


class Evaluation(models.Model):
    subscription = models.ForeignKey(
        "subscriptions.Subscription",
        related_name="evaluations",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    version = models.DateTimeField(
        verbose_name="Date de validation par l'utilisateur",
        null=True,
        blank=True,
    )
    display_version = models.CharField(
        blank=True, max_length=14, verbose_name="Version"
    )
    entity = models.ForeignKey(
        Entity,
        models.CASCADE,
        related_name="evaluations",
        verbose_name=_("Entité"),
    )
    sheet = models.ForeignKey(
        "QuestionSheet",
        verbose_name="Questionnaire",
        on_delete=models.PROTECT,
        related_name="evaluations",
    )
    name = models.CharField(
        max_length=256,
        verbose_name=_("Nom"),
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
    )
    global_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score Global",
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création",
    )
    modified_by_user_date = models.DateTimeField(
        verbose_name="Date de modification",
        auto_now_add=True,
    )
    first_publication_date = models.DateTimeField(
        verbose_name="Date de première publication",
        null=True,
        blank=True,
    )
    is_started = models.BooleanField(
        default=False,
        verbose_name="Commencée",
    )
    need_auth = models.BooleanField(
        default=False,
        verbose_name="Authentification requise",
    )
    is_validated_by_user = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Validée par l'Abonné",
    )
    is_validated_by_admin = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Validée par l'Admin",
    )
    include_in_human_benchmark = models.BooleanField(
        default=True,
        verbose_name="Inclure dans le benchmark human (global et secteur)",
        db_index=True,
    )
    display_human_introduction = models.BooleanField(
        default=True,
        verbose_name="Afficher l'introduction au questionnaire human",
        db_index=True,
    )
    public_display = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Publique",
    )
    private_display = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Privée",
    )
    active_aggregation_with_children = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Activer l'agrégation des réponses avec les entités filles"),
    )
    display_aims_category = models.BooleanField(
        default=False, verbose_name="afficher les catégories des objectifs"
    )
    display_mean_score = models.BooleanField(
        default=True, verbose_name="afficher les scores moyens"
    )
    choices = models.ManyToManyField(
        Choice,
        blank=True,
        related_name="evaluations",
        verbose_name=_("Réponses"),
        through=Answer,
    )
    reminder_count = models.IntegerField(
        verbose_name="Nombre de relances effectuées",
        default=0,
    )
    last_reminder_date = models.DateTimeField(
        verbose_name=_("Date du dernier rappel"),
        null=True,
        blank=True,
    )
    footprint = models.ImageField(
        null=True,
        blank=True,
        upload_to="footprints/",
        verbose_name=_("Empreinte"),
    )
    share = models.ImageField(
        null=True,
        blank=True,
        upload_to="share/",
        verbose_name=_("Partage"),
    )
    social_thumbnail = models.ImageField(
        null=True,
        blank=True,
        upload_to="social_thumbnail/",
        verbose_name=_("Miniature de réseaux sociaux"),
    )
    questions_sheet = models.FileField(
        null=True,
        blank=True,
        upload_to="questions_sheets/",
        verbose_name=_("Questionnaire"),
        storage=RawStorage,
    )
    pdf_sheet = models.FileField(
        null=True,
        blank=True,
        upload_to="pdf_sheets/",
        verbose_name=_("Fiche entreprise"),
        storage=RawStorage,
    )

    collaborators_mail = models.TextField(
        verbose_name=_("Mails des collaborateurs"),
    )

    collaborators_mail_object = models.TextField(
        verbose_name=_("Objet des collaborateurs"),
    )

    signer = Signer(salt="scoring.Evaluation")

    tags = models.ManyToManyField(
        QuestionTag, blank=True, related_name="evaluations", verbose_name="Tags"
    )

    mean_score = models.FloatField(
        null=True,
        default=None,
        verbose_name=_("Score moyen dans mon secteur"),
    )
    mean_score_in_business_line = models.FloatField(
        null=True,
        default=None,
        verbose_name=_("Score moyen dans toutes les entreprises"),
    )

    custom_comment = models.TextField(
        null=True,
        blank=True,
        verbose_name="Commentaire personnalisé",
    )

    answers_rate_cache = models.FloatField(
        null=True,
        default=None,
        verbose_name=_("Taux de réponse de l'évaluation"),
    )

    mandatory_questions = models.ManyToManyField(
        "scoring.Question",
        blank=True,
        related_name="mandatory_evaluations",
        help_text="Custom questions to display if this criteria choice is selected",
    )

    forbidden_questions = models.ManyToManyField(
        "scoring.Question",
        blank=True,
        related_name="forbidden_evaluations",
        help_text="Custom questions to hide if this criteria choice is selected",
    )
    ethnicity_limit_per_file = models.IntegerField(
        verbose_name="Limite de noms/prénoms par fichier pour l'analyse Namsor",
        null=True,
        blank=True,
    )

    # A JSON file that contains the precomputed scores by filters for Human evaluations
    pre_registered_filters = JSONField(
        verbose_name="Filtres pré-enregistrés", default=dict, blank=True, null=True
    )

    # Customized display for pre-registered filters by : civility (for Human classic) and status (for Human Campus)
    civility_filters_display = ModifiedArrayField(
        models.CharField(
            choices=CIVILITY_CHOICES, max_length=100, blank=True, null=True
        ),
        blank=True,
        null=True,
        verbose_name="Liste des filtres par civilité (Human Classique)",
    )

    status_filters_display = ModifiedArrayField(
        models.CharField(
            choices=[
                ("teacher", "Collaborateur.trice  -  enseignant.e "),
                ("collaborator", "Collaborateur.trice  -  administratif "),
                ("student", "Etudiant.e"),
            ],
            max_length=100,
            blank=True,
            null=True,
        ),
        blank=True,
        null=True,
        verbose_name="Liste des filtres par status (Human Campus)",
    )

    objects = EvaluationManager()

    def save(self, *args, **kwargs):
        if not self.pk:  # Vérifie si c'est une nouvelle instance
            self.collaborators_mail_fr = (
                self.collaborators_mail_fr
                or "<p>Bonjour {COLLABORATOR_NAME},<br /><br />Comment allez-vous ?<br /><br />{ENTITY_NAME} souhaite recueillir votre opinion sur leur politique en mati&egrave;re de Diversit&eacute;, d'&Eacute;quit&eacute; et d'Inclusion (DE&amp;I). Votre point de vue est crucial pour nous aider &agrave; identifier leurs points forts et les domaines o&ugrave; une progression est possible au sein de votre entreprise.<br /><br />Ce sondage est administr&eacute; par Mixity, une plateforme sp&eacute;cialis&eacute;e dans la collecte, l'analyse et la restitution des donn&eacute;es li&eacute;es &agrave; la DE&amp;I. Pour acc&eacute;der au sondage, veuillez vous connecter &agrave; la plateforme en cliquant sur le bouton ci-dessous et en cr&eacute;ant votre mot de passe :<br /><br />{ACCESS_BUTTON}<br /><br />Nous tenons &agrave; vous assurer que vos r&eacute;ponses seront trait&eacute;es de mani&egrave;re confidentielle et anonyme. Vos commentaires sont pr&eacute;cieux pour nous permettre de mettre en lumi&egrave;re leurs r&eacute;ussites et d'identifier les domaines o&ugrave; des am&eacute;liorations sont n&eacute;cessaires afin de cr&eacute;er un environnement de travail encore plus inclusif et &eacute;quitable.<br /><br />Le sondage ne devrait pas vous prendre plus de [temps estim&eacute;] minutes.<br /><br />Nous vous remercions sinc&egrave;rement pour votre participation et votre engagement envers {ENTITY_NAME}.<br /><br />Cordialement,<br /><br />L'&eacute;quipe Mixity</p>"
            )
            self.collaborators_mail_object_fr = (
                self.collaborators_mail_object_fr
                or "Participez à notre enquête sur la diversité, l'équité et l'inclusion"
            )
            self.collaborators_mail_en = (
                self.collaborators_mail_en
                or "<p>Hello {COLLABORATOR_NAME},</p>\r\n<p>&nbsp;</p>\r\n<p>How are you doing?</p>\r\n<p>&nbsp;</p>\r\n<p>{ENTITY_NAME} would like to hear your views on their Diversity, Equity and Inclusion (DE&amp;I) policy. Your views are crucial in helping us to identify their strengths and areas for improvement within your company.</p>\r\n<p>&nbsp;</p>\r\n<p>This survey is administered by Mixity, a platform specialized in the collection, analysis and reporting of DE&amp;I data. To access the survey, please log in to the platform by clicking on the button below and creating your password:</p>\r\n<p>&nbsp;</p>\r\n<p>{ACCESS_BUTTON}</p>\r\n<p>&nbsp;</p>\r\n<p>We would like to assure you that your answers will be treated confidentially and anonymously. Your feedback is invaluable in enabling us to highlight their successes and identify areas where improvements are needed to create an even more inclusive and equitable working environment.</p>\r\n<p>&nbsp;</p>\r\n<p>The survey should take no more than [estimated time] minutes to complete.</p>\r\n<p>&nbsp;</p>\r\n<p>We sincerely thank you for your participation and commitment to {ENTITY_NAME}.</p>\r\n<p>&nbsp;</p>\r\n<p>Yours faithfully</p>\r\n<p>&nbsp;</p>\r\n<p>The Mixity team</p>"
            )
            self.collaborators_mail_object_en = (
                self.collaborators_mail_object_en
                or "Take part in our diversity, equity and inclusion survey"
            )
            self.collaborators_mail_es = (
                self.collaborators_mail_es
                or "<p>Hola {COLLABORATOR_NAME},</p>\r\n<p>&nbsp;</p>\r\n<p>&iquest;C&oacute;mo le va?</p>\r\n<p>&nbsp;</p>\r\n<p>A {ENTITY_NAME} le gustar&iacute;a conocer tu opini&oacute;n sobre su pol&iacute;tica de Diversidad, Equidad e Inclusi&oacute;n (D&amp;I). Sus opiniones son cruciales para ayudarnos a identificar sus puntos fuertes y las &aacute;reas de mejora dentro de su empresa.</p>\r\n<p>&nbsp;</p>\r\n<p>Esta encuesta es administrada por Mixity, una plataforma especializada en la recopilaci&oacute;n, el an&aacute;lisis y la notificaci&oacute;n de datos relacionados con la Diversidad, la Igualdad y la Inclusi&oacute;n. Para acceder a la encuesta, inicie sesi&oacute;n en la plataforma haciendo clic en el siguiente bot&oacute;n y creando su contrase&ntilde;a:</p>\r\n<p>&nbsp;</p>\r\n<p>{ACCESS_BUTTON}</p>\r\n<p>&nbsp;</p>\r\n<p>Le aseguramos que sus respuestas se tratar&aacute;n de forma confidencial y an&oacute;nima. Sus comentarios son muy valiosos para permitirnos destacar sus &eacute;xitos e identificar las &aacute;reas en las que se necesitan mejoras para crear un entorno de trabajo a&uacute;n m&aacute;s inclusivo y equitativo.</p>\r\n<p>&nbsp;</p>\r\n<p>Completar la encuesta no le llevar&aacute; m&aacute;s de [tiempo estimado] minutos.</p>\r\n<p>&nbsp;</p>\r\n<p>Le agradecemos sinceramente su participaci&oacute;n y su compromiso con {ENTITY_NAME}.</p>\r\n<p>&nbsp;</p>\r\n<p>Atentamente</p>\r\n<p>&nbsp;</p>\r\n<p>El equipo de Mixity</p>"
            )
            self.collaborators_mail_object_es = (
                self.collaborators_mail_object_es
                or "Participe en nuestra encuesta sobre diversidad, equidad e inclusión"
            )
            self.collaborators_mail_it = (
                self.collaborators_mail_it
                or "<p>Salve {COLLABORATOR_NAME},</p>\r\n<p>&nbsp;</p>\r\n<p>Come va?</p>\r\n<p>&nbsp;</p>\r\n<p>{ENTITY_NAME} vorrebbe conoscere il tuo parere sulla sua politica di Diversit&agrave;, Equit&agrave; e Inclusione (DE&amp;I). Le vostre opinioni sono fondamentali per aiutarci a identificare i punti di forza e le aree di miglioramento della vostra azienda.</p>\r\n<p>&nbsp;</p>\r\n<p>Questo sondaggio &egrave; gestito da Mixity, una piattaforma specializzata nella raccolta, nell'analisi e nel reporting dei dati relativi alla DE&amp;I. Per accedere al sondaggio, si prega di accedere alla piattaforma cliccando sul pulsante sottostante e creando la propria password:</p>\r\n<p>&nbsp;</p>\r\n<p>{ACCESS_BUTTON}</p>\r\n<p>&nbsp;</p>\r\n<p>Desideriamo assicurarvi che le vostre risposte saranno trattate in modo confidenziale e anonimo. Il vostro feedback &egrave; prezioso per permetterci di evidenziare i nostri successi e identificare le aree in cui sono necessari miglioramenti per creare un ambiente di lavoro ancora pi&ugrave; inclusivo ed equo.</p>\r\n<p>&nbsp;</p>\r\n<p>Il sondaggio non dovrebbe richiedere pi&ugrave; di [tempo stimato] minuti per essere completato.</p>\r\n<p>&nbsp;</p>\r\n<p>Vi ringraziamo sinceramente per la vostra partecipazione e per il vostro impegno nei confronti di {ENTITY_NAME}.</p>\r\n<p>&nbsp;</p>\r\n<p>Cordiali saluti</p>\r\n<p>&nbsp;</p>\r\n<p>Il team di Mixity</p>"
            )
            self.collaborators_mail_object_it = (
                self.collaborators_mail_object_it
                or "Partecipate al nostro sondaggio su diversità, equità e inclusione"
            )
            self.collaborators_mail_ja = (
                self.collaborators_mail_ja
                or "<p>こんにちは、{COLLABORATOR_NAME}です、</p>\r\n<p>&nbsp;</p>\r\n<p>お元気ですか。</p>\r\n<p>&nbsp;</p>\r\n<p>{ENTITY_NAME}では、貴社の多様性、公平性、インクルージョン（DE&amp;I）方針に関するご意見をお聞かせいただきたく存じます。あなたのご意見は、貴社の強みと改善点を特定する上で非常に重要です。</p>\r\n<p>&nbsp;</p>\r\n<p>本調査は、ED&amp;Iに関連するデータの収集、分析、報告を専門とするプラットフォームであるMixityによって運営されています。調査にアクセスするには、以下のボタンをクリックしてプラットフォームにログインし、パスワードを作成してください：</p>\r\n<p>&nbsp;</p>\r\n<p>{ACCESS_BUTTON}</p>\r\n<p>&nbsp;</p>\r\n<p>ご回答は秘密厳守、匿名扱いとさせていただきます。皆様からのフィードバックは、より包括的で公平な労働環境を実現するために、成功事例を紹介し、改善が必要な分野を特定する上で大変貴重なものです。</p>\r\n<p>&nbsp;</p>\r\n<p>アンケートの所要時間は[推定時間]分以内です。</p>\r\n<p>&nbsp;</p>\r\n<p>ENTITY_NAME}へのご参加とご尽力に心より感謝申し上げます。</p>\r\n<p>&nbsp;</p>\r\n<p>敬具</p>\r\n<p>&nbsp;</p>\r\n<p>ミクシティチーム</p>"
            )
            self.collaborators_mail_object_ja = (
                self.collaborators_mail_object_ja
                or "多様性、公平性、インクルージョンに関する調査に参加する"
            )
            self.collaborators_mail_zh_hans = (
                self.collaborators_mail_zh_hans
                or "<p>您好 {COLLABORATOR_NAME}、</p>\r\n<p>&nbsp;</p>\r\n<p>您好</p>\r\n<p>&nbsp;</p>\r\n<p>{ENTITY_NAME}希望听取您对其多元化、平等和包容（DE&amp;I）政策的意见。您的意见对于帮助我们确定贵公司的优势和需要改进的地方至关重要。</p>\r\n<p>&nbsp;</p>\r\n<p>本调查由 Mixity 负责管理，这是一个专门收集、分析和报告与 ED&amp;I 相关数据的平台。要访问调查问卷，请单击下面的按钮登录平台并创建密码：</p>\r\n<p>&nbsp;</p>\r\n<p>{ACCESS_BUTTON}</p>\r\n<p>&nbsp;</p>\r\n<p>我们向您保证，您的回答将以保密和匿名的方式处理。您的反馈意见非常宝贵，可帮助我们彰显其成功之处，并确定需要改进的领域，从而创造一个更加包容和公平的工作环境。</p>\r\n<p>&nbsp;</p>\r\n<p>完成调查不超过 [预计时间] 分钟。</p>\r\n<p>&nbsp;</p>\r\n<p>我们衷心感谢您的参与和对 {ENTITY_NAME} 的承诺。</p>\r\n<p>&nbsp;</p>\r\n<p>您忠实的</p>\r\n<p>&nbsp;</p>\r\n<p>Mixity 团队</p>"
            )
            self.collaborators_mail_object_zh_hans = (
                self.collaborators_mail_object_zh_hans
                or "参加我们的多元化、公平和包容性调查"
            )
            self.collaborators_mail_zh_hant = (
                self.collaborators_mail_zh_hant
                or "<p>你好{COLLABORATOR_NAME}，</p>\r\n<p>&nbsp;</p>\r\n<p>你沒事吧？</p>\r\n<p>&nbsp;</p>\r\n<p>{ENTITY_NAME} 想聽聽您對他們的多元化、公平和包容 （DE&amp;I） 政策的看法。您的觀點對於幫助我們確定他們的優勢和貴公司內部有改進空間的領域至關重要。</p>\r\n<p>&nbsp;</p>\r\n<p>該調查由Mixity管理，Mixity是一個專門收集、分析和報告與DE&amp;I相關的數據的平臺。要訪問調查，請點擊下面的按鈕並創建密碼登錄平臺：</p>\r\n<p>&nbsp;</p>\r\n<p>{ACCESS_BUTTON}</p>\r\n<p>&nbsp;</p>\r\n<p>我們向您保證，您的回復將以保密和匿名的方式處理。您的反饋非常寶貴，使我們能夠突出他們的成功，並確定需要改進的領域，以創造一個更加包容和公平的工作環境。</p>\r\n<p>&nbsp;</p>\r\n<p>調查花費的時間不應超過 [估計時間] 分鐘。</p>\r\n<p>&nbsp;</p>\r\n<p>我們衷心感謝您的參與和對{ENTITY_NAME}的承諾。</p>\r\n<p>&nbsp;</p>\r\n<p>親切問候</p>\r\n<p>&nbsp;</p>\r\n<p>Mixity 團隊</p>"
            )
            self.collaborators_mail_object_zh_hant = (
                self.collaborators_mail_object_zh_hant
                or "參加我們的多元化、公平和包容性調查"
            )
            """
        On surchage la méthode save() pour automatiquement relier l'Answer à la question
        :param args:
        :param kwargs:
        :return: rien
        """
        if self.version:
            actual_language = get_language()
            activate("fr")
            month_number = self.version.month
            month_name = MONTHS[month_number - 1]
            self.display_version = f"{self.version.year}-{month_name}"
            activate(actual_language)
        else:
            self.display_version = "en-cours"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Evaluation"
        get_latest_by = "modified_by_user_date"

    def __str__(self):
        return self.entity.name

    @property
    def get_option(self):
        if self.is_scan:
            subscription_option = (
                SubscriptionOption.objects.filter(
                    subscriptionPack__structure=self.entity.entity_level.structure,
                    product__slug="scan",
                )
                .order_by("-start_date")
                .first()
            )
        elif self.is_human:
            subscription_option = (
                SubscriptionOption.objects.filter(
                    subscriptionPack__structure=self.entity.entity_level.structure,
                    product__slug="human",
                )
                .order_by("-start_date")
                .first()
            )
        else:
            subscription_option = (
                SubscriptionOption.objects.filter(
                    subscriptionPack__structure=self.entity.entity_level.structure,
                    product__slug="diag",
                )
                .order_by("-start_date")
                .first()
            )
        return subscription_option

    @cached_property
    def display_version_slugified(self):
        return slugify(self.display_version)

    @cached_property
    def display_version_from_slug(self, slug):
        year, month_slug = slug.split("-")
        result = year + "-"
        actual_language = get_language()
        activate("fr")
        for month in MONTHS:
            if slugify(month) == month_slug:
                result += month
        activate(actual_language)
        return result

    def generate_answers(self):
        if self.sheet.type.is_collaborator:
            return
        questions = self.get_questions
        questions_dict = {q.id: q for q in questions}
        questions_from_answers = self.get_questions_from_answers.only("id")
        for q in questions_from_answers:
            if q.id in questions_dict:
                del questions_dict[q.id]
        questions_to_create = questions_dict.values()
        categories = {}
        answers = []
        for question in questions_to_create:
            a = Answer(
                question=question,
                evaluation=self,
            )
            a.display = question.public_display_default
            answers.append(a)
            categories[question.category.slug] = question.category
        answers_to_delete = Answer.objects.filter(evaluation=self).exclude(
            question__in=questions
        )
        Answer.objects.bulk_create(answers)
        for category in categories.values():
            ScoreCategory.objects.get_or_create(category=category, evaluation=self)
        answers_to_delete.delete()

    @property
    def is_mixity_start(self):
        return self.tags.filter(name="mixity_start").exists()

    @property
    def get_questions_from_answers(self):
        return Question.objects.filter(answers__evaluation=self)

    @property
    def get_applicable_answers(self):
        return self.answers.exclude(is_not_applicable=True)

    @cached_property
    def csrd_tag_on(self):
        return self.tags.filter(name="csrd").exists()

    @cached_property
    def get_global_score_delta(self):
        categories_list = MAIN_CATEGORIES_SLUGS
        if self.is_scan:
            categories_list = SCAN_CATEGORIES_SLUGS
        global_score_delta = 0
        scores_categories = self.scores_categories.filter(
            category__slug__in=categories_list
        )
        for sc in scores_categories:
            global_score_delta += sc.display_value()
        if len(scores_categories) != 0:
            return global_score_delta / len(scores_categories)
        else:
            return global_score_delta

    @cached_property
    def is_human(self):
        return self.sheet.type.slug == "evaluation_collaborateurs_360"

    @cached_property
    def is_scan(self):
        return self.sheet.type.slug == "mixity_evaluation_scan"

    @cached_property
    def is_diag(self):
        return self.sheet.type.slug not in [
            "evaluation_collaborateurs_360",
            "mixity_evaluation_scan",
        ]

    @cached_property
    def is_scan(self):
        return self.sheet.type.slug == "mixity_evaluation_scan"

    @cached_property
    def is_campus(self):
        return self.tags.filter(name="campus").exists()

    @cached_property
    def get_workforce_from_evaluation(self):
        if self.is_human:
            return self.entity.workforce
        workforce_answer = self.answers.filter(
            Q(question__google_sheets_id=20213001)
            | Q(question__sibling__google_sheets_id=221)
            | Q(question__google_sheets_id=10001)
            | Q(question__sibling__google_sheets_id=10001)
        ).first()
        return (workforce_answer and workforce_answer.value) or self.entity.workforce

    @property
    def sibling(self):
        return (
            Evaluation.objects.filter(
                entity=self.entity,
                modified_by_user_date__lt=self.modified_by_user_date,
            )
            .exclude(pk=self.pk)
            .select_related("sheet")
            .order_by("modified_by_user_date")
            .last()
        )

    @property
    def collaborator_url(self):
        return reverse(
            "collaborator_evaluation:collaborator_evaluation_landing",
            kwargs={"signed_pk": self.signer.sign(self.pk)},
        )

    @property
    def collaborator_fill_url(self):
        return reverse(
            "collaborator_evaluation:collaborator_evaluation_fill",
            kwargs={"signed_pk": self.signer.sign(self.pk)},
        )

    @cached_property
    def answer_count(self):
        return count_collaborators_with_answers(self.collaborators)

    @property
    def collaborator_end_url(self):
        return reverse(
            "collaborator_evaluation:collaborator_evaluation_end",
            kwargs={"signed_pk": self.signer.sign(self.pk)},
        )

    @property
    def short_name(self):
        return "{} - {}".format(
            self.entity.name
            or self.entity.entity_level.structure.juridic_name
            or self.name
            or "",
            self.sheet.year,
        )

    def get_footprint_url(self):
        if not self.footprint:
            return ""
        return self.footprint.url

    @cached_property
    def get_general_analysis(self):
        try:
            return self.general_analysis
        except Exception:
            return None

    @property
    def get_questions(self):
        return self.get_questions_global(
            (
                self.sheet.questions.all()
                .prefetch_related("mandatory_tags")
                .select_related("category", "subcategory")
            ).order_by("order_num")
        )

    def get_questions_human(
        self,
        mandatory_question_ids=None,
        forbidden_question_ids=None,
        criteria_tags=None,
    ):
        return self.get_questions_global(
            (
                self.sheet.questions.all()
                .prefetch_related("subquestions__choices", "choices")
                .prefetch_related("mandatory_tags", "forbidden_tags")
                .select_related("category", "subcategory")
            ).order_by("order_num"),
            mandatory_question_ids,
            forbidden_question_ids,
            criteria_tags,
        )

    def get_questions_global(
        self,
        questions,
        mandatory_question_ids=None,
        forbidden_question_ids=None,
        extra_tags=None,
    ):
        if extra_tags is None:
            extra_tags = []
        if forbidden_question_ids is None:
            forbidden_question_ids = []
        forbidden_question_ids = set(
            forbidden_question_ids
            + list(self.forbidden_questions.values_list("google_sheets_id", flat=True))
        )
        if mandatory_question_ids is None:
            mandatory_question_ids = []
        mandatory_question_ids = set(
            mandatory_question_ids
            + list(self.mandatory_questions.values_list("google_sheets_id", flat=True))
        )
        campus_tags = set(
            QuestionTag.objects.filter(name__startswith="campus_").values_list(
                "name", flat=True
            )
        )
        tags = set([tag.name for tag in self.tags.all()] + extra_tags)
        for tag in tags:
            questions = questions.exclude(
                ~Q(google_sheets_id__in=mandatory_question_ids)
                & Q(forbidden_tags__name=tag)
            )
        questions = questions.exclude(google_sheets_id__in=forbidden_question_ids)
        included_questions = []
        for question in questions:
            question_tags = set([tag.name for tag in question.mandatory_tags.all()])
            if self.entity.entity_level.structure.category == "school":
                question_tags = question_tags.difference(campus_tags)
            if (
                question_tags.issubset(tags)
                or question.google_sheets_id in mandatory_question_ids
            ):
                included_questions.append(question)
        return included_questions

    @cached_property
    def targets(self):
        targets = list(
            self.sheet.questions.all()
            .values_list("target", flat=True)
            .order_by("target")
            .distinct()
        )
        return targets

    def get_share_url(self):
        if not self.share:
            return ""
        return self.share.url

    def get_questions_sheet_url(self):
        if not self.questions_sheet:
            return ""
        return self.questions_sheet.url

    @property
    def answers_rate(self):
        if self.answers_rate_cache is None:
            answers = self.answers.distinct("question")
            try:
                self.answers_rate_cache = round(
                    answers.exclude(date_answered=None).count() / answers.count(),
                    3,
                )
                self.save()
            except ZeroDivisionError:
                return None
        return self.answers_rate_cache

    @property
    def can_validate(
        self,
    ):  # No cache needed for this method because self.scores_categories is already used elsewhere
        min_answer_rate = constanceconfig.MIXITY_MIN_ANSWER_RATE
        return bool(
            not self.is_validated_by_user
            and len(
                [
                    s.id
                    for s in self.scores_categories.exclude(category__slug="csrd")
                    if s.category_answers_rate > min_answer_rate
                ]
            )
            >= self.scores_categories.exclude(category__slug="csrd").count()
        )

    @property
    def childrens_validated(self):
        if not self.entity.children_entities.filter(
            Q(evaluations__subscription=self.subscription)
            & Q(evaluations__is_validated_by_user=False)
        ).values("evaluations"):
            return True
        return False

    @property
    def next_question(self):
        # la prochaine question qui n'a pas de reponse sur cette evaluation
        question = (
            Question.objects.filter(
                answers__date_answered=None, answers__evaluation=self
            )
            .order_by("order_num")
            .select_related("category", "subcategory")
            .first()
        )
        if question:
            return question
        else:
            return (
                Question.objects.filter(answers__evaluation=self)
                .order_by("order_num")
                .select_related("category", "subcategory")
                .first()
            )

    @property
    def first_subcategory_slug(self):
        next_question = self.next_question
        if (
            next_question.order_stat_subcategory
            and next_question.order_stat_subcategory >= 1
        ):
            return settings.KEY_FIGURES_SLUG
        return next_question.subcategory.slug

    def get_sidebar_queryset(self):
        """
        We want to perform a sql GROUPBY to list all subcategories, duplicated by targets, and with intermediate counts.
        """
        return (
            self.answers
            # Very important for sql GROUPBY to function
            .order_by(
                "question__target",
                "question__category__order",
                "question__subcategory__order",
            ).exclude(question__display=False)
            # Naming aliases
            .annotate(
                target_slug=F("question__target"),
                category_id=F("question__category_id"),
                category_slug=F("question__category__slug"),
                category_name=F("question__category__name"),
                subcategory_id=F("question__subcategory_id"),
                subcategory_slug=F("question__subcategory__slug"),
                subcategory_name=F("question__subcategory__name"),
            )
            # Values to GROUPBY
            .values(
                "target_slug",
                "category_id",
                "category_slug",
                "category_name",
                "subcategory_id",
                "subcategory_slug",
                "subcategory_name",
            )
            # Computations
            .annotate(
                nb_remaining_answers=Count(
                    "id",
                    filter=Q(
                        date_answered__isnull=True,
                        question__order_stat_subcategory__isnull=True,
                    ),
                ),
                nb_answers=Count(
                    "id",
                    filter=Q(
                        question__order_stat_subcategory__isnull=True,
                    ),
                ),
                nb_key_figures=Count(
                    "id", filter=Q(question__order_stat_subcategory__gte=1)
                ),
                nb_remaining_key_figures=Count(
                    "id",
                    filter=Q(
                        date_answered__isnull=True,
                        question__order_stat_subcategory__gte=1,
                    ),
                ),
            )
        )

    @property
    def footprint_sidebar(self):
        """
        This property is used to create the menu tree in nav_evaluation

        TODO: this should not be in the model, but in a view Mixin with get_sidebar_queryset
        """
        data = self.get_sidebar_queryset()
        targets = OrderedDict()
        target_displays = {slug: label for slug, label in TARGET_CHOICE}
        # Counting targets, categories and subcategories
        for elt in data:
            target_slug = elt["target_slug"]
            category_slug = elt["category_slug"]
            subcategory_slug = elt["subcategory_slug"]
            if target_slug not in targets:
                targets[target_slug] = {
                    "slug": target_slug,
                    "label": target_displays[target_slug],
                    "categories": OrderedDict(),
                }
            categories = targets[target_slug]["categories"]
            if category_slug not in categories:
                categories[category_slug] = {
                    "id": elt["category_id"],
                    "name": elt["category_name"],
                    "slug": category_slug,
                    "subcategories": OrderedDict(),
                    "nb_remaining_answers": 0,
                    "nb_remaining_key_figures": 0,
                    "has_key_figures": False,
                }
            categories[category_slug]["nb_remaining_answers"] += elt[
                "nb_remaining_answers"
            ]
            categories[category_slug]["nb_remaining_key_figures"] += elt[
                "nb_remaining_key_figures"
            ]
            categories[category_slug]["has_key_figures"] |= bool(elt["nb_key_figures"])
            subcategories = categories[category_slug]["subcategories"]
            if elt["nb_answers"] > 0:
                subcategories[subcategory_slug] = {
                    "slug": subcategory_slug,
                    "name": elt["subcategory_name"],
                    "id": elt["subcategory_id"],
                    "nb_remaining_answers": elt["nb_remaining_answers"],
                }
        # Adding special elements (key figures and free fields)
        for target in targets.values():
            for category in target["categories"].values():
                if category["has_key_figures"]:
                    category["subcategories"][settings.KEY_FIGURES_SLUG] = {
                        "slug": settings.KEY_FIGURES_SLUG,
                        "name": settings.KEY_FIGURES_LABEL,
                        "id": None,
                        "nb_remaining_answers": category["nb_remaining_key_figures"],
                    }
                    category["subcategories"].move_to_end(
                        settings.KEY_FIGURES_SLUG, last=False
                    )
                # TODO: it would be nice if free fields are handled here instead like key figures
                # if self.sheet.type.slug != "mixity_start":
                #     # score_category.detail and score_category.aim
                #     category["subcategories"][settings.FREE_FIELDS_SLUG] = {
                #         "slug": settings.FREE_FIELDS_SLUG,
                #         "name": settings.FREE_FIELDS_LABEL,
                #         "id": None,
                #         "nb_remaining_answers": 0 if score_category.is_finished else 1,
                #     }
        return targets

    @classmethod
    def do_reset_mean_scores(cls, evaluations):

        logger.warning("RESETING MEAN SCORES (%i evaluations)", evaluations.count())
        # Reset Evaluation mean scores
        evaluations.update(mean_score=None, mean_score_in_business_line=None)

        # Reset Answer mean scores
        Answer.objects.filter(evaluation__in=evaluations).update(
            mean_score=None, mean_score_in_business_line=None
        )
        # Reset SubAnswer mean scores
        SubAnswer.objects.filter(answer__evaluation__in=evaluations).update(
            mean_score=None, mean_score_in_business_line=None
        )
        # Reset ScoreCategory mean scores
        ScoreCategory.objects.filter(evaluation__in=evaluations).update(
            mean_score=None, mean_score_in_business_line=None
        )

    def next_target_question(self, target=None):
        # la prochaine question de la target suivante qui n'a pas de reponse sur cette evaluation
        question = (
            Question.objects.filter(
                answers__date_answered=None, answers__evaluation=self, target=target
            )
            .order_by("order_num")
            .select_related("category", "subcategory")
            .first()
        )
        if question:
            return question
        else:
            return (
                Question.objects.filter(answers__evaluation=self, target=target)
                .order_by("order_num")
                .select_related("category", "subcategory")
                .first()
            )

    def do_admin_validation(self, request=None, evaluation=None):
        if (
            not self.is_validated_by_user
            and request is not None
            and evaluation is not None
        ):
            messages.warning(request, f"{evaluation.name} is not validated by user")
            return

        self.is_validated_by_admin = True
        self.save()

        if request is not None:
            messages.success(request, "Validation by admin")

        # Explicit message to keep trace (warning to locate in logs)
        logger.warning(
            "ADMIN VALIDATION (evaluation: %i, type: %s)", self.id, str(self.sheet)
        )

        # Enable all indicators
        self.answers.update(
            display=F("display") or F("question__public_display_default")
        )

        # Reset mean scores to all equivalent Evaluations
        question_ids = self.answers.values_list("question_id", flat=True)
        affected_evaluations = Evaluation.objects.filter(
            answers__question_id__in=question_ids
        ).exclude(pk=self.pk)
        self.do_reset_mean_scores(affected_evaluations)

        # Pre-compute and pre-register human filters
        if self.is_human or self.is_scan:
            # Pre-save Json filters
            pre_register_filters.delay(self.pk)

    def do_user_validation(self, force_update=False):
        """
        Compute global score and score per category.

        Important: do not compute scores for Human evaluations because of
        performance issues. It will be done in Heroku Scheduler with command 'compute_answers'.
        """
        if not force_update and (
            self.is_validated_by_user
        ):  # (self.sheet.type.is_collaborator or self.global_score):
            # Already computed
            return
        # Explicit message to keep trace (warning to locate in logs)
        logger.warning(
            "USER VALIDATION (evaluation: %i, type: %s)", self.id, str(self.sheet)
        )
        self.is_validated_by_user = True
        self.save()
        do_update_scoring.delay(
            self.id,
            update_choices=True,
            update_comments=self.is_diag,
            update_categories=True,
        )

    def do_initialize_score_categories(self, categories):
        for category in categories:
            sc, created = ScoreCategory.objects.get_or_create(
                evaluation=self, category=category, defaults={"value": 1.0}
            )

    def compute_score(self, scores):
        """
        :param scores: [
        {'category__slug': 'all', 'value': 68.3333333333333, 'category__weight_index': Decimal('1.20')},
        {'category__slug': 'gender', 'value': 55.3846153846154, 'category__weight_index': Decimal('1.25')},
        {'category__slug': 'disability', 'value': 64.5454545454545, 'category__weight_index': Decimal('0.90')},
        {'category__slug': 'cultural_diversity', 'value': 67.0, 'category__weight_index': Decimal('1.00')},
        {'category__slug': 'generational_diversity', 'value': 70.0, 'category__weight_index': Decimal('1.00')},
        {'category__slug': 'lgbt', 'value': 68.5714285714286, 'category__weight_index': Decimal('1.00')
        ]
        :return: float score
        """
        if self.sheet.type.category:
            score = (
                sum([s["value"] for s in scores])
                / sum([s["questions_weight_index"] for s in scores])
                * 100
            )
        else:
            score = mean(
                [
                    s["value"]
                    * float(s["category__weight_index"])
                    / float(s["category__weight_index"])
                    for s in scores
                ]
            )
        return score

    def apply_ratio(self):
        scores = list(
            self.scores_categories.all()
            .exclude(value=0.0)
            .values("category__slug", "value", "category__weight_index")
        )

        if self.sheet.type.category:
            for score_category in self.scores_categories.all():
                for score in scores:
                    if score["category__slug"] == score_category.category.slug:
                        score["questions_weight_index"] = float(
                            score_category.questions_weight_index
                        )
                        score["value"] = (
                            float(score["value"])
                            * score["questions_weight_index"]
                            / 100
                        )
                        break
        score = self.compute_score(scores)

        if (
            self.sheet.type.workforce_limit
        ):  # TODO DO we apply ratio on Genre or LGBT questionnaire ??
            scores_without_all = [s for s in scores if s["category__slug"] != "all"]
            score_without_all = self.compute_score(scores_without_all)
            ratio = score / score_without_all

            # update category_score by the ration see https://gitlab.com/dantooin_devs/mixity/-/issues/835
            self.scores_categories.exclude(category__slug="all").update(
                value=F("value") * ratio
            )

            new_scores = (
                self.scores_categories.all()
                .exclude(value=0.0)
                .values("category__slug", "value", "category__weight_index")
            )
            score = self.compute_score(new_scores)

        return score

    @property
    def get_mean_score(self):
        if not self.mean_score:
            self.mean_score = self._mean_score()
            if self.mean_score:
                self.save()
        return self.mean_score

    def _mean_score(self):
        tags = [self.sheet.type.tag]
        if self.is_diag:
            tags = ["diag", "global"]

        mean_score = Evaluation.objects.filter(
            is_validated_by_admin=True, sheet__type__tag__in=tags
        ).aggregate(Avg("global_score"))["global_score__avg"]

        return mean_score

    @property
    def get_mean_score_in_business_line(self):

        if not self.mean_score_in_business_line:
            self.mean_score_in_business_line = self._mean_score_in_business_line()
            if self.mean_score_in_business_line:
                self.save()
        return self.mean_score_in_business_line

    def _mean_score_in_business_line(self):
        """
        get the average scores in the main area of the business of all
         evaluations validated by the administrator and having this sector in primary in secondary

        """
        tags = [self.sheet.type.tag]
        if self.is_diag:
            tags = ["diag", "global"]

        mean_score_in_business_line = (
            Evaluation.objects.filter(
                is_validated_by_admin=True, sheet__type__tag__in=tags
            )
            .filter(
                Q(
                    entity__entity_level__structure__business_line=self.entity.entity_level.structure.business_line
                )
                | Q(
                    entity__entity_level__structure__secondary_business_lines=self.entity.entity_level.structure.business_line
                )
            )
            .aggregate(Avg("global_score"))["global_score__avg"]
        )

        return mean_score_in_business_line

    def get_questions_by_category(self, category_name: str, questions: list[Question]):
        # This method returns questions from the category name given
        final_questions = list()

        for question in questions:
            if question.category.name == category_name:
                final_questions.append(question)

        return final_questions

    def get_collaborators_profile_levels(self):
        if not self.is_scan or self.is_validated_by_admin == False:
            return None
        levels = {
            "level1": 0,
            "level2": 0,
            "level3": 0,
            "level4": 0,
        }
        collaborators = self.scan_collaborators.exclude(profile=None).all()
        profiles = [collaborator.profile for collaborator in collaborators]
        for profile in profiles:
            levels[profile.slug] += 1
        total = len(list(profiles))
        if total:
            for key in levels.keys():
                levels[key] = (levels[key] / total) * 100
        result = [value for value in levels.values()]
        return result

    def get_level(self, score):
        LEVELS = {20: "level1", 40: "level2", 60: "level3", 80: "level4", 100: "level5"}
        """Retourne le niveau basé sur le score."""
        for limit, level in sorted(LEVELS.items()):
            if score <= limit:
                return level
        return LEVELS[100]

    @cached_property
    def get_computed_values_by_skills(self):
        if (
            self.sheet.type.slug != "mixity_evaluation_scan"
            or self.is_validated_by_admin == False
        ):
            return None
        LEVELS = {20: "level1", 40: "level2", 60: "level3", 80: "level4", 100: "level5"}

        scan_collaborators = self.scan_collaborators.exclude(job=None)

        skill_distribution = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )  # structure: {job: {skill: {level: count}}}
        job_totals = defaultdict(
            lambda: defaultdict(int)
        )  # structure: {job: {skill: total_count}}

        jobs = list(set([collaborator.job for collaborator in scan_collaborators]))

        # Initialiser toutes les combinaisons possibles avec des valeurs par défaut
        for skill in Skill.objects.filter(
            questions__in=self.sheet.questions.all()
        ):  # Supposons que vous ayez un modèle Skill
            for level in LEVELS.values():
                skill_distribution["general"][skill.name][level] = 0
            for job in jobs:
                for level in LEVELS.values():
                    skill_distribution[job][skill.name][
                        level
                    ] = 0  # Initialiser les niveaux à 0
        # Calculer les skills pour chaque scan_collaborator
        for collaborator in scan_collaborators:
            skills_rate = (
                collaborator.get_skills_rate
            )  # Accède aux résultats via la méthode cached_property
            job = (
                collaborator.job
            )  # Assumons qu'il y a un champ job sur scan_collaborator

            for skill_slug, skill_data in skills_rate.items():
                score = skill_data["score"]
                skill_name = skill_data["name"]
                level = self.get_level(score)  # Obtenir le niveau en fonction du score

                # Incrémenter également dans "general"
                skill_distribution["general"][skill_name][level] += 1
                job_totals["general"][skill_name] += 1

                # Incrémenter le compteur pour le niveau de compétence par rôle
                skill_distribution[job][skill_name][level] += 1
                # Incrémenter le nombre total de collaborateurs par rôle pour cette compétence
                job_totals[job][skill_name] += 1

        # Calcul des proportions de chaque niveau par job
        final_output = []
        for job_name, skills_data in skill_distribution.items():
            job_entry = {"name": job_name, "scores": []}

            for skill, levels_data in skills_data.items():
                total_count = job_totals[job_name][skill]
                skill_entry = {skill: {}}

                for level in LEVELS.values():
                    count = levels_data[level]
                    proportion = count / total_count if total_count > 0 else 0
                    skill_entry[skill][level] = int(
                        round(proportion * 100, 0)
                    )  # Ajoute la proportion
                job_entry["scores"].append(skill_entry)

            final_output.append(job_entry)

        return final_output

    @cached_property
    def get_computed_values_by_subcategories(self):
        if (
            self.sheet.type.slug != "mixity_evaluation_scan"
            or self.is_validated_by_admin == False
        ):
            return None

        # Subquery pour la moyenne des questions QCM
        qcm_avg_subquery = Subquery(
            Question.objects.filter(
                subcategory=OuterRef("pk"),  # On lie la sous-catégorie
                type="qcm",
                answers__in=self.answers.all(),
                answers__isnull=False,
            )
            .annotate(avg_qcm=Avg("answers__choice__value"))
            .values("avg_qcm")[:1],  # On prend la première valeur de la sous-requête
            output_field=FloatField(),
        )

        # Subquery pour la moyenne des questions Multiple QCM
        multiple_qcm_avg_subquery = Subquery(
            Question.objects.filter(
                subcategory=OuterRef("pk"),  # On lie la sous-catégorie
                type="multiple_qcm",
                answers__in=self.answers.all(),
                answers__isnull=False,
            )
            .annotate(sum_choices=Sum("answers__choices__value"))
            .values("sum_choices")[
                :1
            ],  # On prend la première valeur de la sous-requête
            output_field=FloatField(),
        )

        # Subquery pour la moyenne des questions QCM
        qcm_avg_sector_meanscore_subquery = Subquery(
            Question.objects.filter(
                subcategory=OuterRef("pk"),  # On lie la sous-catégorie
                type="qcm",
                answers__evaluation__entity__entity_level__structure__business_line=self.entity.entity_level.structure.business_line,
                answers__isnull=False,
            )
            .annotate(avg_qcm=Avg("answers__choice__value"))
            .values("avg_qcm")[:1],  # On prend la première valeur de la sous-requête
            output_field=FloatField(),
        )

        # Subquery pour la moyenne des questions Multiple QCM
        multiple_qcm_avg_sector_meanscore_subquery = Subquery(
            Question.objects.filter(
                subcategory=OuterRef("pk"),  # On lie la sous-catégorie
                type="multiple_qcm",
                answers__evaluation__entity__entity_level__structure__business_line=self.entity.entity_level.structure.business_line,
                answers__isnull=False,
            )
            .annotate(sum_choices=Sum("answers__choices__value"))
            .values("sum_choices")[
                :1
            ],  # On prend la première valeur de la sous-requête
            output_field=FloatField(),
        )

        # Subquery pour la moyenne des questions QCM
        qcm_avg_global_meanscore_subquery = Subquery(
            Question.objects.filter(
                subcategory=OuterRef("pk"),  # On lie la sous-catégorie
                type="qcm",
                answers__isnull=False,
            )
            .annotate(avg_qcm=Avg("answers__choice__value"))
            .values("avg_qcm")[:1],  # On prend la première valeur de la sous-requête
            output_field=FloatField(),
        )

        # Subquery pour la moyenne des questions Multiple QCM
        multiple_qcm_avg_global_meanscore_subquery = Subquery(
            Question.objects.filter(
                subcategory=OuterRef("pk"),  # On lie la sous-catégorie
                type="multiple_qcm",
                answers__isnull=False,
            )
            .annotate(sum_choices=Sum("answers__choices__value"))
            .values("sum_choices")[
                :1
            ],  # On prend la première valeur de la sous-requête
            output_field=FloatField(),
        )

        # Calcul principal
        subcategories_with_avg = (
            SubCategory.objects.filter(
                questions__sheets=self.sheet  # Filtre sur les questions liées à cette évaluation (self.sheet)
            )
            .annotate(
                # Moyenne des QCM avec la sous-requête
                qcm_avg=qcm_avg_subquery,
                qcm_avg_sector_meanscore=qcm_avg_sector_meanscore_subquery,
                qcm_avg_global_meanscore=qcm_avg_global_meanscore_subquery,
                # Moyenne des Multiple QCM avec la sous-requête
                multiple_qcm_avg=multiple_qcm_avg_subquery,
                multiple_qcm_avg_sector_meanscore=multiple_qcm_avg_sector_meanscore_subquery,
                multiple_qcm_avg_global_meanscore=multiple_qcm_avg_global_meanscore_subquery,
                # Compter les réponses pour les multiple_qcm pour faire la moyenne de ses réponses là
                multiple_qcm_answer_count=Count(
                    Case(
                        When(
                            questions__type="multiple_qcm",
                            questions__answers__in=self.answers.all(),
                            then="questions__answers",
                        ),
                        output_field=FloatField(),
                    ),
                    distinct=True,
                ),
                multiple_qcm_answer_sector_meanscore_count=Count(
                    Case(
                        When(
                            questions__type="multiple_qcm",
                            questions__answers__evaluation__entity__entity_level__structure__business_line=self.entity.entity_level.structure.business_line,
                            then="questions__answers",
                        ),
                        output_field=FloatField(),
                    ),
                    distinct=True,
                ),
                multiple_qcm_answer_global_meanscore_count=Count(
                    Case(
                        When(questions__type="multiple_qcm", then="questions__answers"),
                        output_field=FloatField(),
                    ),
                    distinct=True,
                ),
            )
            .values(  # Cette partie transforme les objets SubCategory en dictionnaires
                "id",
                "name",
                "qcm_avg",
                "qcm_avg_sector_meanscore",
                "qcm_avg_global_meanscore",
                "multiple_qcm_avg",
                "multiple_qcm_avg_sector_meanscore",
                "multiple_qcm_avg_global_meanscore",
                "multiple_qcm_answer_count",
                "multiple_qcm_answer_sector_meanscore_count",
                "multiple_qcm_answer_global_meanscore_count",
            )
        )

        results = []
        for subcat in subcategories_with_avg:
            subcat["total_avg"] = 0
            subcat["sector_total_avg"] = 0
            subcat["global_total_avg"] = 0
            if subcat["multiple_qcm_answer_count"] > 0:
                subcat["multiple_qcm_avg"] = (
                    subcat["multiple_qcm_avg"] / subcat["multiple_qcm_answer_count"]
                )
            if subcat["multiple_qcm_answer_sector_meanscore_count"] > 0:
                subcat["multiple_qcm_avg_sector_meanscore"] = (
                    subcat["multiple_qcm_avg_sector_meanscore"]
                    / subcat["multiple_qcm_answer_sector_meanscore_count"]
                )
            if subcat["multiple_qcm_answer_global_meanscore_count"] > 0:
                subcat["multiple_qcm_avg_global_meanscore"] = (
                    subcat["multiple_qcm_avg_global_meanscore"]
                    / subcat["multiple_qcm_answer_global_meanscore_count"]
                )
            results.append(
                {
                    "id": subcat["id"],
                    "name": subcat["name"],
                    "score": round(
                        ((subcat["qcm_avg"] + subcat["multiple_qcm_avg"]) / 2) * 25, 2
                    ),
                    "sector_score": round(
                        (
                            (
                                subcat["qcm_avg_sector_meanscore"]
                                + subcat["multiple_qcm_avg_sector_meanscore"]
                            )
                            / 2
                        )
                        * 25,
                        2,
                    ),
                    "global_score": round(
                        (
                            (
                                subcat["qcm_avg_global_meanscore"]
                                + subcat["multiple_qcm_avg_global_meanscore"]
                            )
                            / 2
                        )
                        * 25,
                        2,
                    ),
                }
            )
        return results

    def export_answer_sheet_filtered(self, evaluation_list, filter):
        """
        NOTE :
            Create a downloadable Excel file with the answers given during an evaluation,
                            handles multiple entities and filters
                                            OR
                    Create an empty file without responses if no response is given
        """
        # Workbook : Container of all the worksheets
        wb = Workbook()

        # Worksheet
        ws = wb.active  # Get the current active worksheet

        # Fit height and width style
        ws.page_setup.fitToHeight = 1
        ws.page_setup.fitToWidth = 1

        # Worksheet Title
        ws.title = "Questionnaire Mixity"

        # Worksheet Columns
        ws.column_dimensions["A"].width = 100  # Questions Column
        ws.column_dimensions["B"].width = 50  # Info Bubbles Column
        ws.column_dimensions["C"].width = 50  # Choices Colum
        ws.column_dimensions["D"].width = 50  # Answers Column
        for i in range(len(evaluation_list)):  # Entities Names Column
            ws.column_dimensions[chr(ord("E") + i)].width = 50

        # Worksheet styles
        # Font color and size styles
        ft_title = Font(color="181b3d", size=32)  # Title
        ft_cat = Font(color="f67273", size=20)  # Category
        ft_subcat = Font(color="8888e2", size=16)  # Subcategory

        # Cell alignment style
        alignment = Alignment(
            horizontal="general",
            vertical="top",
            text_rotation=0,
            wrap_text=True,
            shrink_to_fit=False,
            indent=0,
        )

        # Tracking cell position in the worksheet
        ws_index = 1

        # Worksheet Content
        # Worksheet header
        pa = os.path.join(settings.STATICFILES_DIRS[0], "img/logo-mixity-258x73.png")
        img = Image(pa)

        # Cell A1
        ws.add_image(img, "A1")

        # Row 2 to 7
        for i in range(7):
            ws_index += 1
            if i == 5:
                coord = chr(ord("E") + len(evaluation_list) - 1)
                (ws.merge_cells(f"A1:{coord}{ws_index}"))
                ws.append([])
            else:
                ws.append([])

        # Getting lists of questions for each evaluation
        questions_list = [
            list(
                set(
                    _eval.get_questions_from_answers.select_related(
                        "category", "subcategory"
                    )
                )
            )
            for _eval in evaluation_list
        ]

        # Getting list of all the questions
        questions = []
        for qs in questions_list:
            for q in qs:
                if q not in questions:
                    questions.append(q)

        questions.sort(
            key=lambda q: (
                q.category.order,
                q.subcategory.order,
                q.order_num,
            )
        )

        score_categories_list = [
            _eval.scores_categories.all() for _eval in evaluation_list
        ]

        # Getting list of categories
        questions_categories = self.get_categories_values()

        # Filling Rows >= 8
        for question_category in questions_categories:
            """
            REMARK : only Mixity Diag that uses Key Figures Category
            """
            is_set_key_figures_label = False
            key_figures_questions = []
            to_review_questions = []
            not_key_figures_questions = []
            csrd_questions = []
            if filter == "key_figures":
                # Key figures questions
                key_figures_questions_list = [
                    evaluation_list[i].get_key_figures_questions_by_category(
                        questions_list[i], question_category
                    )
                    for i in range(len(evaluation_list))
                ]
                for kfs in key_figures_questions_list:
                    for kf in kfs:
                        if kf not in key_figures_questions:
                            key_figures_questions.append(kf)
                key_figures_questions.sort(
                    key=lambda question_: (
                        question_.subcategory.order,
                        question_.order_num,
                    )
                )
            elif filter == "to_review":
                # To review questions
                to_review_questions_list = [
                    evaluation_list[i].get_to_review_question_s_answer_by_category(
                        questions_list[i], question_category
                    )
                    for i in range(len(evaluation_list))
                ]
                for trs in to_review_questions_list:
                    for tr in trs:
                        if tr not in to_review_questions:
                            to_review_questions.append(tr)
                to_review_questions.sort(
                    key=lambda question_: (
                        question_.subcategory.order,
                        question_.order_num,
                    )
                )
            elif filter == "csrd":
                if str(question_category) != "CSRD":
                    continue
                # CSRD category questions
                csrd_questions_list = [
                    evaluation_list[i].get_questions_by_category(
                        "CSRD", questions_list[i]
                    )
                    for i in range(len(evaluation_list))
                ]
                for csrd_qs in csrd_questions_list:
                    for csrd_q in csrd_qs:
                        if csrd_q not in csrd_questions:
                            csrd_questions.append(csrd_q)
                csrd_questions.sort(
                    key=lambda question_: (
                        question_.subcategory.order,
                        question_.order_num,
                    )
                )
            elif filter == "classique":
                # Key figures questions without subcategories
                key_figures_questions_list = [
                    evaluation_list[i].get_key_figures_questions_by_category(
                        questions_list[i], question_category
                    )
                    for i in range(len(evaluation_list))
                ]
                for kfs in key_figures_questions_list:
                    for kf in kfs:
                        if kf not in key_figures_questions:
                            key_figures_questions.append(kf)
                key_figures_questions.sort(
                    key=lambda question_: question_.order_stat_subcategory
                )
                # Not key figures questions
                not_key_figures_questions_list = [
                    [
                        question
                        for question in questions_list[i]
                        if (
                            question not in key_figures_questions_list[i]
                            and question.category.name == question_category
                        )
                    ]
                    for i in range(len(evaluation_list))
                ]
                for nkfs in not_key_figures_questions_list:
                    for nkf in nkfs:
                        if nkf not in not_key_figures_questions:
                            not_key_figures_questions.append(nkf)
                not_key_figures_questions.sort(
                    key=lambda question_: (
                        question_.subcategory.order,
                        question_.order_num,
                    )
                )

            # Setting Category
            ws_index += 1
            # Value
            if filter == "to_review":
                ws[f"A{ws_index}"] = (
                    str(_("À revoir dans la catégorie"))
                    + " "
                    + str(_(question_category))
                )
            elif filter == "key_figures":
                ws[f"A{ws_index}"] = (
                    str(_("Chiffres clés dans la catégorie"))
                    + " "
                    + str(_(question_category))
                )
            elif filter == "csrd":
                ws[f"A{ws_index}"] = (
                    str(_("Questions de la catégorie")) + " " + str(_("CSRD"))
                )
            else:
                ws[f"A{ws_index}"] = str(_(question_category))
            ws[f"A{ws_index}"].alignment = alignment
            ws[f"A{ws_index}"].font = ft_cat
            ws[f"D{ws_index}"] = str(_("Commentaires"))
            ws[f"D{ws_index}"].alignment = alignment
            ws[f"D{ws_index}"].font = ft_subcat
            for i in range(len(evaluation_list)):
                column = chr(ord("E") + i)
                ws[f"{column}{ws_index}"] = str(_(evaluation_list[i].entity.name))
                ws[f"{column}{ws_index}"].alignment = alignment
                ws[f"{column}{ws_index}"].font = ft_subcat

            ws_index += 1

            # Tracking subcategory
            current_subcat = None

            """
                NOTE : about key figures questions
                - These questions have not a subcategory called "Chiffres-clès"
                - It's possible to distinguish them by :
                    * UI TYPE : slider or sq_select
                    * order_stat_subcategory != None
                - Also only this fictive subcategory that contains subquestions
            """

            if filter == "classique" or filter == "key_figures":
                for kf_question in key_figures_questions:
                    if (
                        filter == "key_figures"
                        and kf_question.subcategory != current_subcat
                    ):
                        # Setting Subcategory
                        ws.append([])
                        ws_index += 1
                        ws[f"A{ws_index}"] = str(_(kf_question.subcategory.name))
                        ws[f"A{ws_index}"].font = ft_subcat
                        ws[f"A{ws_index}"].alignment = alignment
                        ws_index += 1
                    if filter == "classique" and not is_set_key_figures_label:
                        # Setting key figures Subcategory
                        ws.append([])
                        ws_index += 1
                        # Value
                        ws[f"A{ws_index}"] = str(settings.KEY_FIGURES_LABEL)
                        # Styles
                        ws[f"A{ws_index}"].font = ft_subcat
                        ws[f"A{ws_index}"].alignment = alignment

                        ws_index += 1
                        is_set_key_figures_label = True
                        current_subcat = str(settings.KEY_FIGURES_LABEL)

                    # Getting current category and subcategory
                    current_subcat = kf_question.subcategory
                    # Getting choices and answers of the current question
                    choices_values = ""  # Choices of the current question

                    commented = False

                    if "qcm" in kf_question.type:
                        for choice in kf_question.choices.all():
                            choices_values += choice.label + " ; \n"
                    elif "subquestions" in kf_question.type:
                        for sq in kf_question.subquestions.all():
                            choices_values += sq.label + " ; \n "

                    # Filling values of columns
                    ws[f"A{ws_index}"] = kf_question.label
                    ws[f"B{ws_index}"] = kf_question.help_text
                    ws[f"C{ws_index}"] = choices_values
                    # Applying alignment style
                    ws[f"A{ws_index}"].alignment = alignment
                    ws[f"B{ws_index}"].alignment = alignment
                    ws[f"C{ws_index}"].alignment = alignment

                    for eval_index in range(len(evaluation_list)):
                        if kf_question not in key_figures_questions_list[eval_index]:
                            continue
                        rep = kf_question.answers.filter(
                            evaluation=evaluation_list[eval_index]
                        ).first()  # Answer
                        value = ""
                        if rep.value is None:
                            if rep.text_value:
                                value = str(rep.text_value)
                            elif rep.choice and rep.choice.label:
                                value = rep.choice.label
                        else:
                            value = str(rep.value)
                            if rep.ratio_value:
                                value += " (" + str(rep.ratio_value) + "%)"
                        if rep.value and kf_question.type == "date":
                            value = datetime.fromtimestamp(float(value)).strftime(
                                "%d/%m/%Y"
                            )
                        if "subquestions" in kf_question.type:
                            value = ""
                            for sa in rep.subanswers.all():
                                if sa.value != None:
                                    value += "{0} : {1} ; \n".format(
                                        sa.subquestion.label, sa.value
                                    )
                        column = chr(ord("E") + eval_index)
                        ws[f"{column}{ws_index}"] = value
                        ws[f"{column}{ws_index}"].alignment = alignment

                        if rep.text_value and not commented:
                            ws[f"D{ws_index}"] = str(rep.text_value)
                            ws[f"D{ws_index}"].alignment = alignment
                            commented = True

                    ws_index += 1
                for i in range(len(key_figures_questions_list)):
                    key_figures_questions_list[i].clear()
                key_figures_questions.clear()

            # TO REVIEW FILTER
            elif filter == "to_review":
                for tr_question in to_review_questions:
                    if tr_question.subcategory != current_subcat:
                        # Setting Subcategory
                        ws.append([])
                        ws_index += 1
                        ws[f"A{ws_index}"] = str(_(tr_question.subcategory.name))
                        ws[f"A{ws_index}"].font = ft_subcat
                        ws[f"A{ws_index}"].alignment = alignment
                        ws_index += 1

                    # Getting current category and subcategory
                    current_subcat = tr_question.subcategory
                    # Getting choices and answers of the current question
                    choices_values = ""  # Choices of the current question

                    commented = False

                    if "qcm" in tr_question.type:
                        for choice in tr_question.choices.all():
                            choices_values += choice.label + " ; \n"
                    elif "subquestions" in tr_question.type:
                        for sq in tr_question.subquestions.all():
                            choices_values += sq.label + " ; \n "

                    # Filling values of columns
                    ws[f"A{ws_index}"] = tr_question.label
                    ws[f"B{ws_index}"] = tr_question.help_text
                    ws[f"C{ws_index}"] = choices_values

                    # Applying alignment style
                    ws[f"A{ws_index}"].alignment = alignment
                    ws[f"B{ws_index}"].alignment = alignment
                    ws[f"C{ws_index}"].alignment = alignment

                    for eval_index in range(len(evaluation_list)):
                        if tr_question not in to_review_questions_list[eval_index]:
                            continue
                        rep = tr_question.answers.filter(
                            evaluation=evaluation_list[eval_index]
                        ).first()  # Answer
                        value = ""
                        if rep.value is None:
                            if rep.text_value:
                                value = str(rep.text_value)
                            elif rep.choice and rep.choice.label:
                                value = rep.choice.label
                        else:
                            value = str(rep.value)
                            if rep.ratio_value:
                                value += " (" + str(rep.ratio_value) + "%)"
                        if rep.value and tr_question.type == "date":
                            value = datetime.fromtimestamp(float(value)).strftime(
                                "%d/%m/%Y"
                            )
                        if "subquestions" in tr_question.type:
                            value = ""
                            for sa in rep.subanswers.all():
                                if sa.value != None:
                                    value += "{0} : {1} ; \n".format(
                                        sa.subquestion.label, sa.value
                                    )
                        column = chr(ord("E") + eval_index)
                        ws[f"{column}{ws_index}"] = value
                        ws[f"{column}{ws_index}"].alignment = alignment

                        if rep.text_value and not commented:
                            ws[f"D{ws_index}"] = str(rep.text_value)
                            ws[f"D{ws_index}"].alignment = alignment
                            commented = True

                    ws_index += 1
                for i in range(len(to_review_questions_list)):
                    to_review_questions_list[i].clear()
                to_review_questions.clear()

            if filter == "csrd":
                for csrd_question in csrd_questions:
                    if csrd_question.subcategory != current_subcat:
                        # Setting Subcategory
                        ws.append([])
                        ws_index += 1
                        ws[f"A{ws_index}"] = str(_(csrd_question.subcategory.name))
                        ws[f"A{ws_index}"].font = ft_subcat
                        ws[f"A{ws_index}"].alignment = alignment
                        ws_index += 1

                    # Getting current category and subcategory
                    current_subcat = csrd_question.subcategory
                    # Getting choices and answers of the current question
                    choices_values = ""  # Choices of the current question

                    commented = False

                    if "qcm" in csrd_question.type:
                        for choice in csrd_question.choices.all():
                            choices_values += choice.label + " ; \n"
                    elif "subquestions" in csrd_question.type:
                        for sq in csrd_question.subquestions.all():
                            choices_values += sq.label + " ; \n "

                    # Filling values of columns
                    ws[f"A{ws_index}"] = csrd_question.label
                    ws[f"B{ws_index}"] = csrd_question.help_text
                    ws[f"C{ws_index}"] = choices_values

                    # Applying alignment style
                    ws[f"A{ws_index}"].alignment = alignment
                    ws[f"B{ws_index}"].alignment = alignment
                    ws[f"C{ws_index}"].alignment = alignment

                    for eval_index in range(len(evaluation_list)):
                        if csrd_question not in csrd_questions_list[eval_index]:
                            continue
                        rep = csrd_question.answers.filter(
                            evaluation=evaluation_list[eval_index]
                        ).first()  # Answer
                        value = ""
                        if rep.value is None:
                            if rep.text_value:
                                value = str(rep.text_value)
                            elif rep.choice and rep.choice.label:
                                value = rep.choice.label
                        else:
                            value = str(rep.value)
                            if rep.ratio_value:
                                value += " (" + str(rep.ratio_value) + "%)"
                        if rep.value and csrd_question.type == "date":
                            value = datetime.fromtimestamp(float(value)).strftime(
                                "%d/%m/%Y"
                            )
                        if "subquestions" in csrd_question.type:
                            value = ""
                            for sa in rep.subanswers.all():
                                if sa.value != None:
                                    value += "{0} : {1} ; \n".format(
                                        sa.subquestion.label, sa.value
                                    )
                        column = chr(ord("E") + eval_index)
                        ws[f"{column}{ws_index}"] = value
                        ws[f"{column}{ws_index}"].alignment = alignment

                        if rep.text_value and not commented:
                            ws[f"D{ws_index}"] = str(rep.text_value)
                            ws[f"D{ws_index}"].alignment = alignment
                            commented = True

                    ws_index += 1
                for i in range(len(csrd_questions_list)):
                    csrd_questions_list[i].clear()
                csrd_questions.clear()

            if filter == "classique":
                # Not key figures questions
                for nkf_question in not_key_figures_questions:
                    # Handling change of subcategory
                    if nkf_question.subcategory != current_subcat:
                        # Setting Subcategory
                        ws.append([])
                        ws_index += 1
                        ws[f"A{ws_index}"] = str(_(nkf_question.subcategory.name))
                        ws[f"A{ws_index}"].font = ft_subcat
                        ws[f"A{ws_index}"].alignment = alignment
                        ws_index += 1

                    # Getting current category and subcategory
                    current_subcat = nkf_question.subcategory

                    # Filling Worksheet Rows with questions-bubbles info-choices-answers
                    choices_values = ""  # Choices of the current question

                    commented = False

                    if (
                        "qcm" in nkf_question.type
                        and "subquestions_qcm" not in nkf_question.type
                    ):
                        for choice in nkf_question.choices.all():
                            choices_values += choice.label + " ; \n"
                    elif (
                        "subquestions" in nkf_question.type
                        and "subquestions_qcm" not in nkf_question.type
                    ):
                        for sq in nkf_question.subquestions.all():
                            choices_values += sq.label + " ; \n "
                    elif "subquestions_qcm" in nkf_question.type:
                        for sq in nkf_question.subquestions.all():
                            choices_values += sq.label + " ; \n "

                    # Filling values of columns
                    ws[f"A{ws_index}"] = nkf_question.label
                    ws[f"B{ws_index}"] = nkf_question.help_text
                    ws[f"C{ws_index}"] = choices_values

                    # Applying alignment style
                    ws[f"A{ws_index}"].alignment = alignment
                    ws[f"B{ws_index}"].alignment = alignment
                    ws[f"C{ws_index}"].alignment = alignment

                    for eval_index in range(len(evaluation_list)):
                        if (
                            nkf_question
                            not in not_key_figures_questions_list[eval_index]
                        ):
                            continue
                        rep = nkf_question.answers.filter(
                            evaluation=evaluation_list[eval_index]
                        ).first()
                        value = ""
                        if rep.value is None:
                            if rep.text_value:
                                value = str(rep.text_value)
                            elif rep.choice and rep.choice.label:
                                value = rep.choice.label
                        else:
                            value = str(rep.value)
                            if rep.ratio_value:
                                value += " (" + str(rep.ratio_value) + "%)"
                        if rep.value and nkf_question.type == "date":
                            value = datetime.fromtimestamp(float(value)).strftime(
                                "%d/%m/%Y"
                            )
                        if "subquestions" in nkf_question.type:
                            value = ""
                            for sa in rep.subanswers.all():
                                if sa.value != None:
                                    value += "{0} : {1} ; \n".format(
                                        sa.subquestion.label, sa.value
                                    )
                        if "subquestions_qcm" in nkf_question.type:
                            if not self.is_human:
                                value = ""
                                for sa in rep.subanswers.all():
                                    if sa.value == 1:
                                        value += sa.subquestion.label + " ; \n "
                        column = chr(ord("E") + eval_index)
                        ws[f"{column}{ws_index}"] = value
                        ws[f"{column}{ws_index}"].alignment = alignment

                        if rep.text_value and not commented:
                            ws[f"D{ws_index}"] = str(rep.text_value)
                            ws[f"D{ws_index}"].alignment = alignment
                            commented = True

                    ws_index += 1

                for i in range(len(not_key_figures_questions_list)):
                    not_key_figures_questions_list[i].clear()
                not_key_figures_questions.clear()

                # General Questions
                ws.append([])
                ws_index += 1
                ws[f"A{ws_index}"] = ugettext("Général")
                ws[f"A{ws_index}"].font = ft_subcat
                ws[f"A{ws_index}"].alignment = alignment
                general_questions = [
                    ugettext(
                        "Avez-vous mis en place d'autres modes d'actions au sein de votre organisation ?"
                    ),
                    ugettext("Quels sont les objectifs que vous souhaitez atteindre ?"),
                ]
                ws_index += 1
                for general_questions_index in range(2):
                    ws[f"A{ws_index}"] = general_questions[general_questions_index]
                    ws[f"A{ws_index}"].alignment = alignment
                    for eval_index in range(len(evaluation_list)):
                        sc = (
                            score_categories_list[eval_index]
                            .filter(category__name=question_category)
                            .first()
                        )
                        if sc is not None and sc.actions.first() is not None:
                            action = sc.actions.first()
                            column = chr(ord("B") + eval_index)
                            ws[f"{column}{ws_index}"] = (
                                action.descriptif_detail[0]
                                if general_questions_index == 0
                                else action.descriptif_aim[0]
                            )
                            ws[f"{column}{ws_index}"].alignment = alignment
                    ws_index += 1

        for i in range(len(questions_list)):
            questions_list[i].clear()
        questions.clear()

        # Get the path of the temporary file
        with NamedTemporaryFile(
            mode="w", prefix="Summary_", suffix=".xlsx", delete=False
        ) as tmp_write:
            wb.save(tmp_write.name)
            tmp_write.seek(0)
            filepath = tmp_write.name

        # Save the final file
        with open(filepath, "rb") as tmp_read:
            if self.is_validated_by_user:
                self.questions_sheet.save("questionnaire.xlsx", tmp_read)
        return filepath

    def export_answer_sheet(self):
        """
        NOTE :
            Create a downloadable Excel file with the answers given during the evaluation
                                            OR
                    Create an empty file without responses if no response is given
        """
        # Workbook : Container of all the worksheets
        wb = Workbook()

        # Worksheet
        ws = wb.active  # Get the current active worksheet

        # Fit height and width style
        ws.page_setup.fitToHeight = 1
        ws.page_setup.fitToWidth = 1

        # Worksheet Title
        ws.title = "Questionnaire Mixity"

        # Worksheet Columns
        ws.column_dimensions["A"].width = 100  # Questions Column
        ws.column_dimensions["B"].width = 50  # Info Bubbles Column
        ws.column_dimensions["C"].width = 50  # Choices Colum
        if not self.is_human:
            ws.column_dimensions["D"].width = 50  # Answers Column
            ws.column_dimensions["E"].width = 50  # Comments Column

        # Getting list of questions
        if self.is_human:
            mandatory_ids = [q.id for q in self.mandatory_questions.all()]
            forbidden_ids = [q.id for q in self.forbidden_questions.all()]
            questions = self.get_questions_human(
                mandatory_question_ids=mandatory_ids,
                forbidden_question_ids=forbidden_ids,
            )
        else:
            questions = list(
                set(
                    self.get_questions_from_answers.select_related(
                        "category", "subcategory"
                    )
                )
            )
        score_categories = self.scores_categories.all()

        # Order questions according to the GSheet doc
        questions.sort(
            key=lambda question: (
                question.category.order,
                question.subcategory.order,
                question.order_num,
            )
        )

        # Getting list of categories
        questions_categories = self.get_categories_values()

        # Worksheet styles
        # Font color and size styles
        ft_title = Font(color="181b3d", size=32)  # Title
        ft_cat = Font(color="f67273", size=20)  # Category
        ft_subcat = Font(color="8888e2", size=16)  # Subcategory

        # Cell alignment style
        alignment = Alignment(
            horizontal="general",
            vertical="top",
            text_rotation=0,
            wrap_text=True,
            shrink_to_fit=False,
            indent=0,
        )

        # Tracking cell position in the worksheet
        ws_index = 1

        # Worksheet Content
        # Worksheet header
        pa = os.path.join(settings.STATICFILES_DIRS[0], "img/logo-mixity-258x73.png")
        img = Image(pa)

        # Cell A1
        ws.add_image(img, "A1")

        # Row 2 to 7
        for i in range(7):
            ws_index += 1
            if i == 5:
                (
                    ws.merge_cells(f"A1:E{ws_index}")
                    if not self.is_human
                    else ws.merge_cells(f"A1:C{ws_index}")
                )
                ws.append([])
            else:
                ws.append([])

        # Filling Rows >= 8
        for question_category in questions_categories:
            """
            REMARK : only Mixity Diag that uses Key Figures Category
            """
            is_set_key_figures_subcat = True
            if not self.is_human:
                is_set_key_figures_subcat = False  # Used to know of the key figures fictive subcategory is set for the current category or not yet

                # Key figures questions
                key_figures_questions = self.get_key_figures_questions_by_category(
                    questions, question_category
                )
                key_figures_questions.sort(
                    key=lambda question_: question_.order_stat_subcategory
                )
            else:
                key_figures_questions = []

            # Setting Category
            ws_index += 1
            # Value
            ws[f"A{ws_index}"] = str(_(question_category))
            # Styles
            ws[f"A{ws_index}"].font = ft_cat
            ws[f"A{ws_index}"].alignment = alignment
            ws[f"E{ws_index}"] = str(_("Commentaires"))
            ws[f"E{ws_index}"].alignment = alignment
            ws[f"E{ws_index}"].font = ft_subcat
            ws_index += 1

            # Tracking subcategory
            current_subcat = None

            """
                NOTE : about key figures questions
                - These questions have not a subcategory called "Chiffres-clès"
                - It's possible to distinguish them by :
                    * UI TYPE : slider or sq_select
                    * order_stat_subcategory != None
                - Also only this fictive subcategory that contains subquestions
            """
            if not self.is_human:
                for question_kf in key_figures_questions:
                    if not is_set_key_figures_subcat:
                        # Setting key figures Subcategory
                        ws.append([])
                        ws_index += 1
                        # Value
                        ws[f"A{ws_index}"] = str(settings.KEY_FIGURES_LABEL)
                        # Styles
                        ws[f"A{ws_index}"].font = ft_subcat
                        ws[f"A{ws_index}"].alignment = alignment

                        ws_index += 1
                        is_set_key_figures_subcat = True
                        current_subcat = str(settings.KEY_FIGURES_LABEL)
                    # Getting choices and answers of the current question
                    choices_values = ""  # Choices of the current question
                    rep = question_kf.answers.filter(evaluation=self).first()  # Answer
                    if not rep:
                        continue
                    value = ""
                    if rep.value is None:
                        if rep.text_value:
                            value = str(rep.text_value)
                        elif rep.choice and rep.choice.label:
                            value = rep.choice.label
                    else:
                        value = str(rep.value)
                        if rep.ratio_value:
                            value += " (" + str(rep.ratio_value) + "%)"

                    if "qcm" in question_kf.type:
                        for choice in question_kf.choices.all():
                            choices_values += choice.label + " ; \n"
                    elif "subquestions" in question_kf.type:
                        value = ""
                        for sq in question_kf.subquestions.all():
                            choices_values += sq.label + " ; \n "
                        for sa in rep.subanswers.all():
                            if sa.value != None:
                                value += "{0} : {1} ; \n".format(
                                    sa.subquestion.label, sa.value
                                )

                    # Filling Worksheet Rows with questions-bubbles info-choices-answers

                    # Filling values of columns
                    ws[f"A{ws_index}"] = question_kf.label
                    ws[f"B{ws_index}"] = question_kf.help_text
                    ws[f"C{ws_index}"] = choices_values
                    ws[f"D{ws_index}"] = value
                    if rep.text_value:
                        ws[f"E{ws_index}"] = str(rep.text_value)
                    # Applying alignment style
                    ws[f"A{ws_index}"].alignment = alignment
                    ws[f"B{ws_index}"].alignment = alignment
                    ws[f"C{ws_index}"].alignment = alignment
                    ws[f"D{ws_index}"].alignment = alignment
                    ws[f"E{ws_index}"].alignment = alignment

                    ws_index += 1

            # Not key figures questions
            not_key_figures_questions = [
                question
                for question in questions
                if (
                    question not in key_figures_questions
                    and question.category.name == question_category
                )
            ]
            not_key_figures_questions.sort(
                key=lambda question: (
                    question.subcategory.order,
                    question.order_num,
                )
            )
            key_figures_questions.clear()
            """
                NOTE :
                These questions belong to a defined subcategory and only them who contain
                questions of type subquestions_qcm
            """
            for question in not_key_figures_questions:
                # Handling change of subcategory
                if question.subcategory != current_subcat:
                    # Setting Subcategory
                    ws.append([])
                    ws_index += 1
                    ws[f"A{ws_index}"] = str(_(question.subcategory.name))
                    ws[f"A{ws_index}"].font = ft_subcat
                    ws[f"A{ws_index}"].alignment = alignment
                    ws_index += 1

                # Getting current category and subcategory
                current_subcat = question.subcategory

                # Filling Worksheet Rows with questions-bubbles info-choices-answers
                choices_values = ""  # Choices of the current question
                rep = question.answers.filter(evaluation=self).first()
                if not rep:
                    continue
                if not self.is_human:
                    value = ""
                    if rep.value is None:
                        if rep.text_value:
                            value = str(rep.text_value)
                        elif rep.choice and rep.choice.label:
                            value = rep.choice.label
                    else:
                        value = str(rep.value)
                        if rep.ratio_value:
                            value += " (" + str(rep.ratio_value) + "%)"

                if "qcm" in question.type and "subquestions_qcm" not in question.type:
                    for choice in question.choices.all():
                        choices_values += choice.label + " ; \n"
                elif (
                    "subquestions" in question.type
                    and "subquestions_qcm" not in question.type
                ):
                    for sq in question.subquestions.all():
                        choices_values += sq.label + " ; \n "
                    for sa in rep.subanswers.all():
                        if sa.value != None:
                            value += "{0} : {1} ; \n".format(
                                sa.subquestion.label, sa.value
                            )
                elif "subquestions_qcm" in question.type:
                    for sq in question.subquestions.all():
                        choices_values += sq.label + " ; \n "
                    if not self.is_human:
                        value = ""
                        for sa in rep.subanswers.all():
                            if sa.value == 1:
                                value += sa.subquestion.label + " ; \n "

                # Filling values of columns
                ws[f"A{ws_index}"] = question.label
                ws[f"B{ws_index}"] = question.help_text
                ws[f"C{ws_index}"] = choices_values
                if not self.is_human:
                    ws[f"D{ws_index}"] = value
                    if rep.text_value:
                        ws[f"E{ws_index}"] = str(rep.text_value)
                # Applying alignment style
                ws[f"A{ws_index}"].alignment = alignment
                ws[f"B{ws_index}"].alignment = alignment
                ws[f"C{ws_index}"].alignment = alignment
                if not self.is_human:
                    ws[f"D{ws_index}"].alignment = alignment
                    ws[f"E{ws_index}"].alignment = alignment
                ws_index += 1

            not_key_figures_questions.clear()

            # General Questions
            if not self.is_human:
                ws.append([])
                ws_index += 1
                ws[f"A{ws_index}"] = ugettext("Général")
                ws[f"A{ws_index}"].font = ft_subcat
                ws[f"A{ws_index}"].alignment = alignment
                ws_index += 1
                sc = score_categories.filter(category__name=question_category).first()
                general_questions = [
                    ugettext(
                        "Avez-vous mis en place d'autres modes d'actions au sein de votre organisation ?"
                    ),
                    ugettext("Quels sont les objectifs que vous souhaitez atteindre ?"),
                ]
                for i in range(2):
                    ws[f"A{ws_index}"] = general_questions[i]
                    if sc is not None and sc.actions.first() is not None:
                        action = sc.actions.first()
                        ws[f"D{ws_index}"] = (
                            action.descriptif_detail[0]
                            if i == 0
                            else action.descriptif_aim[0]
                        )
                    ws[f"A{ws_index}"].alignment = alignment
                    ws[f"D{ws_index}"].alignment = alignment
                    ws_index += 1

        questions.clear()

        # Get the path of the temporary file
        with NamedTemporaryFile(
            mode="w", prefix="Summary_", suffix=".xlsx", delete=False
        ) as tmp_write:
            wb.save(tmp_write.name)
            tmp_write.seek(0)
            filepath = tmp_write.name

        # Save the final file
        with open(filepath, "rb") as tmp_read:
            if self.is_validated_by_user:
                self.questions_sheet.save("questionnaire.xlsx", tmp_read)
        return filepath

    def export_filtered_answer_sheet_react(self, filter):
        """
        NOTE :
            Create a downloadable Excel file with the answers given during the evaluation
                                                  OR
                    Create an empty file without responses if no response is given
        """
        # Workbook : Container of all the worksheets
        wb = Workbook()

        # Worksheet
        ws = wb.active  # Get the current active worksheet

        # Fit height and width style
        ws.page_setup.fitToHeight = 1
        ws.page_setup.fitToWidth = 1

        # Worksheet Title
        ws.title = "Questionnaire Mixity"

        # Worksheet Columns
        ws.column_dimensions["A"].width = 100  # Questions Column
        ws.column_dimensions["B"].width = 50  # Info Bubbles Column
        ws.column_dimensions["C"].width = 50  # Choices Colum
        if not self.is_human:
            ws.column_dimensions["D"].width = 50  # Answers Column
            ws.column_dimensions["E"].width = 50  # Comments Column

        # Getting list of questions
        if self.is_human:
            mandatory_ids = [q.id for q in self.mandatory_questions.all()]
            forbidden_ids = [q.id for q in self.forbidden_questions.all()]
            questions = self.get_questions_human(
                mandatory_question_ids=mandatory_ids,
                forbidden_question_ids=forbidden_ids,
            )
        else:
            questions = list(
                set(
                    self.get_questions_from_answers.select_related(
                        "category", "subcategory"
                    )
                )
            )
        score_categories = self.scores_categories.all()

        # Order questions according to the GSheet doc
        questions.sort(
            key=lambda question: (
                question.category.order,
                question.subcategory.order,
                question.order_num,
            )
        )

        # Getting list of categories
        questions_categories = self.get_categories_values()

        # Worksheet styles
        # Font color and size styles
        ft_title = Font(color="181b3d", size=32)  # Title
        ft_cat = Font(color="f67273", size=20)  # Category
        ft_subcat = Font(color="8888e2", size=16)  # Subcategory

        # Cell alignment style
        alignment = Alignment(
            horizontal="general",
            vertical="top",
            text_rotation=0,
            wrap_text=True,
            shrink_to_fit=False,
            indent=0,
        )

        # Tracking cell position in the worksheet
        ws_index = 1

        # Worksheet Content
        # Worksheet header
        pa = os.path.join(settings.STATICFILES_DIRS[0], "img/logo-mixity-258x73.png")
        img = Image(pa)

        # Cell A1
        ws.add_image(img, "A1")

        # Row 2 to 7
        for i in range(7):
            ws_index += 1
            if i == 5:
                (
                    ws.merge_cells(f"A1:E{ws_index}")
                    if not self.is_human
                    else ws.merge_cells(f"A1:C{ws_index}")
                )
                ws.append([])
            else:
                ws.append([])

        # Filling Rows >= 8
        for question_category in questions_categories:
            """
            REMARK : only Mixity Diag that uses Key Figures Category
            """
            is_set_key_figures_subcat = True
            is_set_to_review_subcat = True
            if not self.is_human:
                if filter == "key_figures":
                    to_review_questions = []

                    # is_set_key_figures_subcat = False  # Used to know of the key figures fictive subcategory is set for the current category or not yet

                    # Key figures questions
                    key_figures_questions = self.get_key_figures_questions_by_category(
                        questions, question_category
                    )
                    key_figures_questions.sort(
                        key=lambda question: (
                            question.subcategory.order,
                            question.order_num,
                        )
                    )
                elif filter == "to_review":
                    key_figures_questions = []
                    # is_set_to_review_subcat = False  # Used to know of the key figures fictive subcategory is set for the current category or not yet

                    # Key figures questions
                    to_review_questions = (
                        self.get_to_review_question_s_answer_by_category(
                            questions, question_category
                        )
                    )
                    to_review_questions.sort(
                        key=lambda question: (
                            question.subcategory.order,
                            question.order_num,
                        )
                    )
                else:
                    key_figures_questions = []
                    to_review_questions = []
            else:
                key_figures_questions = []
                to_review_questions = []
            # Setting Category
            ws_index += 1
            # Value
            if filter == "to_review":
                ws[f"A{ws_index}"] = (
                    str(_("À revoir dans la catégorie"))
                    + " "
                    + str(_(question_category))
                )
            elif filter == "key_figures":
                ws[f"A{ws_index}"] = (
                    str(_("Chiffres clés dans la catégorie"))
                    + " "
                    + str(_(question_category))
                )
            # Styles
            ws[f"A{ws_index}"].font = ft_cat
            ws[f"A{ws_index}"].alignment = alignment
            ws[f"E{ws_index}"] = str(_("Commentaires"))
            ws[f"E{ws_index}"].alignment = alignment
            ws[f"E{ws_index}"].font = ft_subcat

            ws_index += 1

            # Tracking subcategory
            current_subcat = None

            """
                NOTE : about key figures questions
                - These questions have not a subcategory called "Chiffres-clès"
                - It's possible to distinguish them by :
                    * UI TYPE : slider or sq_select
                    * order_stat_subcategory != None
                - Also only this fictive subcategory that contains subquestions
            """

            if not self.is_human:
                if filter == "key_figures":
                    for question_kf in key_figures_questions:
                        # if not is_set_key_figures_subcat:
                        #     # Setting key figures Subcategory
                        #     ws.append([])
                        #     ws_index += 1
                        #     # Value
                        #     ws[f"A{ws_index}"] = str(settings.KEY_FIGURES_LABEL)
                        #     # Styles
                        #     ws[f"A{ws_index}"].font = ft_subcat
                        #     ws[f"A{ws_index}"].alignment = alignment
                        #     ws_index += 1
                        #     is_set_key_figures_subcat = True
                        if question_kf.subcategory != current_subcat:
                            # Setting Subcategory
                            ws.append([])
                            ws_index += 1
                            ws[f"A{ws_index}"] = str(_(question_kf.subcategory.name))
                            ws[f"A{ws_index}"].font = ft_subcat
                            ws[f"A{ws_index}"].alignment = alignment
                            ws_index += 1

                        # Getting current category and subcategory
                        current_subcat = question_kf.subcategory
                        # Getting choices and answers of the current question
                        choices_values = ""  # Choices of the current question

                        # MANDATORY_FLTER

                        rep = question_kf.answers.filter(
                            evaluation=self
                        ).first()  # Answer
                        if rep.value is None and rep.choice and rep.choice.label:
                            value = rep.choice.label
                        else:
                            value = str(rep.value)
                            if rep.ratio_value:
                                value += " (" + str(rep.ratio_value) + "%)"

                        if "qcm" in question_kf.type:
                            for choice in question_kf.choices.all():
                                choices_values += choice.label + " ; \n"
                        elif "subquestions" in question_kf.type:
                            value = ""
                            for sq in question_kf.subquestions.all():
                                choices_values += sq.label + " ; \n "
                            for sa in rep.subanswers.all():
                                if sa.value != None:
                                    value += "{0} : {1} ; \n".format(
                                        sa.subquestion.label, sa.value
                                    )

                        # Filling Worksheet Rows with questions-bubbles info-choices-answers

                        # Filling values of columns
                        ws[f"A{ws_index}"] = question_kf.label
                        ws[f"B{ws_index}"] = question_kf.help_text
                        ws[f"C{ws_index}"] = choices_values
                        ws[f"D{ws_index}"] = value
                        if rep.text_value:
                            ws[f"E{ws_index}"] = str(rep.text_value)
                        # Applying alignment style
                        ws[f"A{ws_index}"].alignment = alignment
                        ws[f"B{ws_index}"].alignment = alignment
                        ws[f"C{ws_index}"].alignment = alignment
                        ws[f"D{ws_index}"].alignment = alignment
                        ws[f"E{ws_index}"].alignment = alignment

                        ws_index += 1
                    key_figures_questions.clear()

                # TO REVIEW FILTER
                elif filter == "to_review":
                    for question_tr in to_review_questions:
                        # if not is_set_to_review_subcat:
                        #     # Setting key figures Subcategory
                        #     ws.append([])
                        #     ws_index += 1
                        #     # Value
                        #     ws[f"A{ws_index}"] = str(settings.TO_REVIEW_LABEL)
                        #     # Styles
                        #     ws[f"A{ws_index}"].font = ft_subcat
                        #     ws[f"A{ws_index}"].alignment = alignment
                        #     ws_index += 1
                        #     is_set_to_review_subcat = True
                        if question_tr.subcategory != current_subcat:
                            # Setting Subcategory
                            ws.append([])
                            ws_index += 1
                            ws[f"A{ws_index}"] = str(_(question_tr.subcategory.name))
                            ws[f"A{ws_index}"].font = ft_subcat
                            ws[f"A{ws_index}"].alignment = alignment
                            ws_index += 1

                        # Getting current category and subcategory
                        current_subcat = question_tr.subcategory
                        # Getting choices and answers of the current question
                        choices_values = ""  # Choices of the current question
                        rep = question_tr.answers.filter(
                            evaluation=self
                        ).first()  # Answer
                        if rep.value is None and rep.choice and rep.choice.label:
                            value = rep.choice.label
                        else:
                            value = str(rep.value)
                            if rep.ratio_value:
                                value += " (" + str(rep.ratio_value) + "%)"

                        if "qcm" in question_tr.type:
                            for choice in question_tr.choices.all():
                                choices_values += choice.label + " ; \n"
                        elif "subquestions" in question_tr.type:
                            value = ""
                            for sq in question_tr.subquestions.all():
                                choices_values += sq.label + " ; \n "
                            for sa in rep.subanswers.all():
                                if sa.value != None:
                                    value += "{0} : {1} ; \n".format(
                                        sa.subquestion.label, sa.value
                                    )

                        # Filling Worksheet Rows with questions-bubbles info-choices-answers

                        # Filling values of columns
                        ws[f"A{ws_index}"] = question_tr.label
                        ws[f"B{ws_index}"] = question_tr.help_text
                        ws[f"C{ws_index}"] = choices_values
                        ws[f"D{ws_index}"] = value
                        if rep.text_value:
                            ws[f"E{ws_index}"] = str(rep.text_value)

                        # Applying alignment style
                        ws[f"A{ws_index}"].alignment = alignment
                        ws[f"B{ws_index}"].alignment = alignment
                        ws[f"C{ws_index}"].alignment = alignment
                        ws[f"D{ws_index}"].alignment = alignment
                        ws[f"E{ws_index}"].alignment = alignment

                        ws_index += 1
                    to_review_questions.clear()
        questions.clear()

        # Get the path of the temporary file
        with NamedTemporaryFile(
            mode="w", prefix="Summary_", suffix=".xlsx", delete=False
        ) as tmp_write:
            wb.save(tmp_write.name)
            tmp_write.seek(0)
            filepath = tmp_write.name

        # Save the final file
        with open(filepath, "rb") as tmp_read:
            if self.is_validated_by_user:
                self.questions_sheet.save("questionnaire.xlsx", tmp_read)
        return filepath

    def export_filtered_questions_sheet(self, selected_filters, collab_queryset):
        """
        This function generate a filtered Excel file for human evaluations only
        """

        # Workbook : Container of all the worksheets
        wb = Workbook()

        # Worksheet
        ws = wb.active  # Get the current active worksheet

        # Fit height and width style
        (
            ws,
            questions,
            categories,
            ft_title,
            ft_title1,
            ft_title2,
            ft_question,
            ws_index,
        ) = init_worksheet_header(ws, self)

        # Row >= 8
        # Filling Number of collaborators for the first filter
        ws, ws_index, filter_filtername = header_filtered_sheet(
            ws,
            ft_title,
            ft_title2,
            ft_question,
            collab_queryset,
            selected_filters,
            ws_index,
        )

        # Filling questions
        ws.append([])  # adding a blank line
        ws_index += 1
        ws[f"A{ws_index}"] = str(_("Questions"))
        ws[f"A{ws_index}"].font = ft_title
        ws_index += 1
        for question_category in categories:
            # Setting Category
            ws_index += 1
            # Value
            ws[f"A{ws_index}"] = str(_(question_category))
            # Styles
            ws[f"A{ws_index}"].font = ft_title1
            ws_index += 1

            # Tracking subcategory
            current_subcat = None

            category_questions = [
                question
                for question in questions
                if (question.category.name == question_category)
            ]
            category_questions.sort(
                key=lambda question: (
                    question.subcategory.order,
                    question.order_num,
                )
            )
            for question in category_questions:
                # Handling change of subcategory
                if question.subcategory != current_subcat:
                    # Setting Subcategory
                    ws.append([])
                    ws_index += 1
                    ws[f"A{ws_index}"] = str(_(question.subcategory.name))
                    ws[f"A{ws_index}"].font = ft_title2
                    ws_index += 1

                # Getting current category and subcategory
                current_subcat = question.subcategory

                # Filling choices
                choices_values = []  # Choices of the current question
                sq_choices_values = []
                choices_percentage = compute_value_from_param(
                    self, question, collab_queryset, '{"type": "rate_choice"}'
                )
                ws_col_index = 2
                if "qcm" in question.type and "subquestions_qcm" not in question.type:
                    for choice in question.choices.all():
                        choices_values.append({choice.id: choice.label})
                    # Filling choices
                    for value in choices_values:
                        for k, v in value.items():
                            ws.cell(row=ws_index, column=ws_col_index).value = v
                            ws.cell(row=ws_index, column=ws_col_index).font = (
                                ft_question
                            )
                            ws = display_exported_percentage(
                                ws, choices_percentage, k, ws_index + 1, ws_col_index
                            )

                            ws_col_index += 1
                    ws_index += 1
                    # Filling question
                    ws[f"A{ws_index}"] = question.label
                    ws[f"A{ws_index}"].font = ft_question
                    ws_index += 1
                elif (
                    "subquestions" in question.type
                    and "subquestions_qcm" not in question.type
                ):
                    sub_choices_percentage = compute_value_from_param(
                        self,
                        question,
                        collab_queryset,
                        '{"type": "rate_subanswers_choice_count"}',
                    )
                    for sq in question.subquestions.all():
                        choices_values.append({"id": sq.id, "label": sq.label})
                        if not sq_choices_values:
                            sq_choices_values = [
                                value.label for value in sq.choices.all()
                            ]

                    #  Filling Subquestions choices
                    for sq_choice in sq_choices_values:
                        ws.cell(row=ws_index, column=ws_col_index).value = sq_choice
                        ws.cell(row=ws_index, column=ws_col_index).font = ft_question
                        ws_col_index += 1
                    ws_index += 1

                    # Filling question before subquestions
                    ws[f"A{ws_index}"] = question.label
                    ws[f"A{ws_index}"].font = ft_question
                    ws_index += 1
                    # Filling subquestions
                    for value in choices_values:
                        ws[f"A{ws_index}"] = value["label"]
                        ws, ws_index, ws_col_index = display_current_subchoices(
                            ws, sub_choices_percentage, value, ws_index, ws_col_index, 2
                        )
                        ws_index += 1
                elif "subquestions_qcm" in question.type:
                    sub_choices_qcm_percentage = compute_value_from_param(
                        self, question, collab_queryset, '{"type": "rate_subanswers"}'
                    )
                    for sq in question.subquestions.all():
                        choices_values.append({"id": sq.id, "label": sq.label})
                    # Filling question
                    ws[f"A{ws_index}"] = question.label
                    ws[f"A{ws_index}"].font = ft_question
                    ws_index += 1
                    # Filling QCM subquestions
                    for value in choices_values:
                        ws[f"A{ws_index}"] = value["label"]
                        ws = display_current_sub_percentage(
                            ws,
                            sub_choices_qcm_percentage,
                            value,
                            ws_index,
                            ws_col_index,
                        )

                        ws_index += 1

        # Get the path of the temporary file
        with NamedTemporaryFile(
            mode="w", prefix="Summary_", suffix=".xlsx", delete=False
        ) as tmp_write:
            wb.save(tmp_write.name)
            tmp_write.seek(0)
            filepath = tmp_write.name

        # Save the final file
        with open(filepath, "rb") as tmp_read:
            if self.is_validated_by_user:
                self.questions_sheet.save("questionnaire.xlsx", tmp_read)
        return filepath

    def export_multiple_filtered_questions_sheet(
        self,
        selected_filters,
        second_selected_filters,
        collab_queryset,
        second_collab_queryset,
    ):
        """
        This function generate a filtered Excel file with a comparaison between to filter for human evaluations only
        """

        # TODO finish this by comparing the first filter with the second one

        # Workbook : Container of all the worksheets
        wb = Workbook()

        print(
            "selected filter are : ",
            selected_filters,
            " and second selected filter are : ",
            second_selected_filters,
        )
        # Worksheet
        ws = wb.active  # Get the current active worksheet

        (
            ws,
            questions,
            categories,
            ft_title,
            ft_title1,
            ft_title2,
            ft_question,
            ws_index,
        ) = init_worksheet_header(ws, self)

        # Row >= 8
        # Filling Number of collaborators for the first filter
        ws, ws_index, filter_name = header_filtered_sheet(
            ws,
            ft_title,
            ft_title2,
            ft_question,
            collab_queryset,
            selected_filters,
            ws_index,
            filter_index=1,
        )

        # Filling Number of collaborators for the second filter
        ws, ws_index, filter_name = header_filtered_sheet(
            ws,
            ft_title,
            ft_title2,
            ft_question,
            second_collab_queryset,
            second_selected_filters,
            ws_index,
            filter_index=2,
        )

        ws[f"A{ws_index}"] = str(_("Questions"))
        ws[f"A{ws_index}"].font = ft_title
        ws_index += 1
        for question_category in categories:
            # Setting Category
            ws_index += 1
            # Value
            ws[f"A{ws_index}"] = str(_(question_category))
            # Styles
            ws[f"A{ws_index}"].font = ft_title1
            ws_index += 1

            # Tracking subcategory
            current_subcat = None

            category_questions = [
                question
                for question in questions
                if (question.category.name == question_category)
            ]
            category_questions.sort(
                key=lambda question: (
                    question.subcategory.order,
                    question.order_num,
                )
            )
            for question in category_questions:
                # Handling change of subcategory
                if question.subcategory != current_subcat:
                    # Setting Subcategory
                    ws.append([])
                    ws_index += 1
                    ws[f"A{ws_index}"] = str(_(question.subcategory.name))
                    ws[f"A{ws_index}"].font = ft_title2
                    ws_index += 1

                # Getting current category and subcategory
                current_subcat = question.subcategory

                # Filling choices
                choices_values = []  # Choices of the current question
                sq_choices_values = []
                choices_percentage = compute_value_from_param(
                    self, question, collab_queryset, '{"type": "rate_choice"}'
                )
                second_choices_percentage = compute_value_from_param(
                    self, question, second_collab_queryset, '{"type": "rate_choice"}'
                )
                ws_col_index = 3
                if "qcm" in question.type and "subquestions_qcm" not in question.type:
                    for choice in question.choices.all():
                        choices_values.append({choice.id: choice.label})
                    # Filling choices
                    ws_index += 2

                    for value in choices_values:
                        for k, v in value.items():
                            ws.cell(row=ws_index, column=ws_col_index).value = v
                            ws.cell(row=ws_index, column=ws_col_index).font = (
                                ft_question
                            )
                            # filling with the result of the first filter
                            ws = display_exported_percentage(
                                ws, choices_percentage, k, ws_index + 1, ws_col_index
                            )

                            # filling with the result of the second filter
                            ws_index += 1
                            ws = display_exported_percentage(
                                ws,
                                second_choices_percentage,
                                k,
                                ws_index + 1,
                                ws_col_index,
                            )
                            ws_col_index += 1
                            ws_index -= 1

                    # Filling question
                    ws[f"A{ws_index}"] = question.label
                    ws[f"A{ws_index}"].font = ft_question
                    ws_index += 1
                    ws.cell(row=ws_index, column=2).value = str(_("premier filtre"))
                    ws_index += 1
                    ws.cell(row=ws_index, column=2).value = str(_("second filtre"))
                elif (
                    "subquestions" in question.type
                    and "subquestions_qcm" not in question.type
                ):
                    sub_choices_percentage = compute_value_from_param(
                        self,
                        question,
                        collab_queryset,
                        '{"type": "rate_subanswers_choice_count"}',
                    )
                    second_sub_choices_percentage = compute_value_from_param(
                        self,
                        question,
                        second_collab_queryset,
                        '{"type": "rate_subanswers_choice_count"}',
                    )
                    for sq in question.subquestions.all():
                        choices_values.append({"id": sq.id, "label": sq.label})
                        if not sq_choices_values:
                            sq_choices_values = [
                                value.label for value in sq.choices.all()
                            ]
                    ws_index += 2
                    #  Filling Subquestions choices
                    for sq_choice in sq_choices_values:
                        ws.cell(row=ws_index, column=ws_col_index).value = sq_choice
                        ws.cell(row=ws_index, column=ws_col_index).font = ft_question
                        ws_col_index += 1

                    # Filling question before subquestions
                    ws[f"A{ws_index}"] = question.label
                    ws[f"A{ws_index}"].font = ft_question
                    ws_index += 1
                    # Filling subquestions
                    for value in choices_values:
                        ws[f"A{ws_index}"] = value["label"]
                        ws.cell(row=ws_index, column=2).value = str(_("premier filtre"))
                        ws, ws_index, ws_col_index = display_current_subchoices(
                            ws, sub_choices_percentage, value, ws_index, ws_col_index, 3
                        )
                        ws_index += 1

                        ws.cell(row=ws_index, column=2).value = str(_("second filtre"))
                        ws, ws_index, ws_col_index = display_current_subchoices(
                            ws,
                            second_sub_choices_percentage,
                            value,
                            ws_index,
                            ws_col_index,
                            3,
                        )

                        ws_index += 2

                elif "subquestions_qcm" in question.type:
                    sub_choices_qcm_percentage = compute_value_from_param(
                        self, question, collab_queryset, '{"type": "rate_subanswers"}'
                    )
                    second_sub_choices_qcm_percentage = compute_value_from_param(
                        self,
                        question,
                        second_collab_queryset,
                        '{"type": "rate_subanswers"}',
                    )
                    for sq in question.subquestions.all():
                        choices_values.append({"id": sq.id, "label": sq.label})
                    # Filling question
                    ws_index += 1
                    ws[f"A{ws_index}"] = question.label
                    ws[f"A{ws_index}"].font = ft_question
                    ws_index += 1

                    # Filling QCM subquestions
                    for value in choices_values:
                        ws[f"A{ws_index}"] = value["label"]
                        ws.cell(row=ws_index, column=2).value = str(_("premier filtre"))
                        ws = display_current_sub_percentage(
                            ws,
                            sub_choices_qcm_percentage,
                            value,
                            ws_index,
                            ws_col_index,
                        )
                        ws_index += 1
                        ws.cell(row=ws_index, column=2).value = str(_("second filtre"))
                        ws = display_current_sub_percentage(
                            ws,
                            second_sub_choices_qcm_percentage,
                            value,
                            ws_index,
                            ws_col_index,
                        )

                        ws_index += 2

        # Get the path of the temporary file
        with NamedTemporaryFile(
            mode="w", prefix="Summary_", suffix=".xlsx", delete=False
        ) as tmp_write:
            wb.save(tmp_write.name)
            tmp_write.seek(0)
            filepath = tmp_write.name

        # Save the final file
        with open(filepath, "rb") as tmp_read:
            if self.is_validated_by_user:
                self.questions_sheet.save("questionnaire.xlsx", tmp_read)
        return filepath

    def fill_target(self, question):
        # Filling target for campus
        if (
            question.mandatory_tags.filter(name="campus_teacher").exists()
            and question.mandatory_tags.filter(name="campus_collaborator").exists()
            and question.mandatory_tags.filter(name="campus_student").exists()
        ) or (
            not question.mandatory_tags.filter(name="campus_teacher").exists()
            and not question.mandatory_tags.filter(name="campus_collaborator").exists()
            and not question.mandatory_tags.filter(name="campus_student").exists()
            and not question.forbidden_tags.filter(name="campus_teacher").exists()
            and not question.forbidden_tags.filter(name="campus_collaborator").exists()
            and not question.forbidden_tags.filter(name="campus_student").exists()
        ):
            return str(_("Tous les répondants (f/h/nb)"))
        elif (
            question.mandatory_tags.filter(name="campus_student").exists()
            and not question.mandatory_tags.filter(name="campus_teacher").exists()
            and not question.mandatory_tags.filter(name="campus_collaborator").exists()
        ):
            return str(_("Etudiants (f/h/nb)"))
        elif (
            question.forbidden_tags.filter(name="campus_student").exists()
            and not question.forbidden_tags.filter(name="campus_teacher").exists()
            and not question.forbidden_tags.filter(name="campus_collaborator").exists()
        ) or (
            not question.mandatory_tags.filter(name="campus_student").exists()
            and question.mandatory_tags.filter(name="campus_teacher").exists()
            and question.mandatory_tags.filter(name="campus_collaborator").exists()
        ):
            return str(_("Employés (f/h/nb)"))
        else:
            return str("")

    def export_react_questions_sheet(self, paramslist, querysetlist):
        """
        This function generate a filtered Excel file with a comparaison between to filter for human evaluations only
        """
        # TODO finish this by comparing the first filter with the second one

        # Workbook : Container of all the worksheets
        wb = Workbook()

        filter_names = []

        number_of_queryset = len(querysetlist)
        # Worksheet
        ws = wb.active  # Get the current active worksheet

        (
            ws,
            questions,
            categories,
            ft_title,
            ft_title1,
            ft_title2,
            ft_question,
            ws_index,
        ) = init_worksheet_header(ws, self)

        # Cell alignment style
        alignment = Alignment(
            horizontal="general",
            vertical="top",
            text_rotation=0,
            wrap_text=True,
            shrink_to_fit=False,
            indent=0,
        )

        # Row >= 8
        # Filling Number of collaborators for the first filter
        for queryset in querysetlist:
            actual_filter = paramslist[str(querysetlist.index(queryset) + 1)]
            collab_queryset = queryset
            filter_name = ""
            nws, nws_index, filter_name = header_filtered_sheet(
                ws,
                ft_title,
                ft_title2,
                ft_question,
                collab_queryset,
                actual_filter,
                ws_index,
                filter_index=querysetlist.index(queryset) + 1,
            )
            filter_names.append(filter_name)
            ws = nws
            ws_index = nws_index
        ws[f"A{ws_index}"] = str(_("Questions"))
        ws[f"A{ws_index}"].font = ft_title
        ws_index += 1
        for question_category in categories:
            # Setting Category
            ws_index += 1
            # Value
            ws[f"A{ws_index}"] = str(_(question_category))
            # Styles
            ws[f"A{ws_index}"].font = ft_title1
            ws_index += 1

            # Tracking subcategory
            current_subcat = None

            category_questions = [
                question
                for question in questions
                if (question.category.name == question_category)
            ]
            category_questions.sort(
                key=lambda question: (
                    question.subcategory.order,
                    question.order_num,
                )
            )
            for question in category_questions:
                # Handling change of subcategory
                if question.subcategory != current_subcat:
                    # Setting Subcategory
                    ws.append([])
                    ws_index += 1
                    ws[f"A{ws_index}"] = str(_(question.subcategory.name))
                    ws[f"A{ws_index}"].font = ft_title2
                    ws[f"A{ws_index}"].alignment = alignment
                    ws_index += 1

                # Getting current category and subcategory
                current_subcat = question.subcategory

                # Filling choices
                choices_values = []  # Choices of the current question
                sq_choices_values = []
                choices_percentage_from_query = []
                for queryset in querysetlist:
                    choices_percentage_from_query.append(
                        compute_value_from_param(
                            self, question, queryset, '{"type": "rate_choice"}'
                        )
                    )

                ws_col_index = 3
                if self.is_campus:
                    ws_col_index = 4
                if "qcm" in question.type and "subquestions_qcm" not in question.type:
                    for choice in question.choices.all():
                        choices_values.append({choice.id: choice.label})
                    # Filling choices
                    ws_index += 2

                    for value in choices_values:
                        for k, v in value.items():
                            ws.cell(row=ws_index, column=ws_col_index).value = v
                            ws.cell(row=ws_index, column=ws_col_index).font = (
                                ft_question
                            )
                            # filling with the result of the first filter
                            for result_in_query in choices_percentage_from_query:
                                ws = display_exported_percentage(
                                    ws, result_in_query, k, ws_index + 1, ws_col_index
                                )
                                ws_index += 1
                            ws_index -= number_of_queryset
                            ws_col_index += 1
                    # Filling question
                    ws[f"A{ws_index}"] = question.label
                    ws[f"A{ws_index}"].font = ft_question
                    ws[f"A{ws_index}"].alignment = alignment

                    # Filling target for campus
                    if self.is_campus:
                        ws[f"C{ws_index}"] = self.fill_target(question)
                        ws[f"C{ws_index}"].font = ft_question
                        ws[f"C{ws_index}"].alignment = alignment

                    for i in range(len(querysetlist)):
                        ws_index += 1
                        ws.cell(row=ws_index, column=2).value = str(filter_names[i])
                elif (
                    "subquestions" in question.type
                    and "subquestions_qcm" not in question.type
                ):
                    sub_choice_from_query = []
                    for queryset in querysetlist:
                        sub_choice_from_query.append(
                            compute_value_from_param(
                                self,
                                question,
                                queryset,
                                '{"type": "rate_subanswers_choice_count"}',
                            )
                        )
                    for sq in question.subquestions.all():
                        choices_values.append({"id": sq.id, "label": sq.label})
                        if not sq_choices_values:
                            sq_choices_values = [
                                value.label for value in sq.choices.all()
                            ]
                    ws_index += number_of_queryset + 1
                    #  Filling Subquestions choices
                    for sq_choice in sq_choices_values:
                        ws.cell(
                            row=ws_index - number_of_queryset + 1, column=ws_col_index
                        ).value = sq_choice
                        ws.cell(
                            row=ws_index - number_of_queryset + 1, column=ws_col_index
                        ).font = ft_question
                        ws_col_index += 1

                    # Filling question before subquestions
                    ws_index -= number_of_queryset - 1
                    ws[f"A{ws_index}"] = question.label
                    ws[f"A{ws_index}"].font = ft_question
                    ws[f"A{ws_index}"].alignment = alignment

                    # Filling target for campus
                    if self.is_campus:
                        ws[f"C{ws_index}"] = self.fill_target(question)
                        ws[f"C{ws_index}"].font = ft_question
                        ws[f"C{ws_index}"].alignment = alignment

                    ws_index += 1
                    # Filling subquestions
                    for value in choices_values:
                        ws[f"A{ws_index}"] = value["label"]
                        new_ws_col_index = 3
                        if self.is_campus:
                            new_ws_col_index = 4
                        for i in range(number_of_queryset):
                            ws.cell(row=ws_index, column=2).value = str(filter_names[i])
                            ws, ws_index, ws_col_index = display_current_subchoices(
                                ws,
                                sub_choice_from_query[i],
                                value,
                                ws_index,
                                ws_col_index,
                                new_ws_col_index,
                            )
                            ws_index += 1
                        ws_index += 1

                elif "subquestions_qcm" in question.type:
                    sub_choice_qcm_percentage_from_query = []
                    for queryset in querysetlist:
                        sub_choice_qcm_percentage_from_query.append(
                            compute_value_from_param(
                                self, question, queryset, '{"type": "rate_subanswers"}'
                            )
                        )
                    for sq in question.subquestions.all():
                        choices_values.append({"id": sq.id, "label": sq.label})
                    # Filling question
                    ws_index += 1
                    ws[f"A{ws_index}"] = question.label
                    ws[f"A{ws_index}"].font = ft_question
                    ws[f"A{ws_index}"].alignment = alignment

                    # Filling target for campus
                    if self.is_campus:
                        ws[f"C{ws_index}"] = self.fill_target(question)
                        ws[f"C{ws_index}"].font = ft_question
                        ws[f"C{ws_index}"].alignment = alignment
                    ws_index += 1

                    # Filling QCM subquestions
                    for value in choices_values:
                        ws[f"A{ws_index}"] = value["label"]
                        for i in range(len(querysetlist)):
                            ws.cell(row=ws_index, column=2).value = str(filter_names[i])
                            ws = display_current_sub_percentage(
                                ws,
                                sub_choice_qcm_percentage_from_query[i],
                                value,
                                ws_index,
                                ws_col_index,
                            )
                            ws_index += 1
                        ws_index += 1

        # Get the path of the temporary file
        with NamedTemporaryFile(
            mode="w", prefix="Summary_", suffix=".xlsx", delete=False
        ) as tmp_write:
            wb.save(tmp_write.name)
            tmp_write.seek(0)
            filepath = tmp_write.name

        # Save the final file
        with open(filepath, "rb") as tmp_read:
            if self.is_validated_by_user:
                self.questions_sheet.save("questionnaire.xlsx", tmp_read)
        return filepath

    def get_synthesis_template(
        self,
        generalAnalysis: str,
        firstName: str,
        lastName: str,
        title: str,
        photo: str,
        comment: str,
        dimensionsData: dict,
        keyRecommendationsData: dict,
        bestPracticesData: dict,
        productSlug: str,
        productName: str,
        footprint: str,
        scoreDEI: int,
    ) -> str:
        style = """
            body {
                font-family: 'DM Sans', sans-serif;
                color: #181B3D;
                letter-spacing: -4%;
            }
            * {
                margin:0;
                padding:0;
                text-indent:0;
            }
            ul {
                padding-left: 1.5rem;
                display: block;
                list-style-type: disc;
            }
            li {
                font-weight: 400;
                font-size: 12px;
                line-height: 15px;
                margin-top: 0 !important;
                margin-bottom: 0.5rem !important;
                display: list-item;
            }
            p {
                font-weight: 400;
                font-size: 12px;
                line-height: 15px;
            }
            .score {
                font-weight: 500;
                font-size: 12px;
                line-height: 15px;
            }
            .title {
                font-weight: 500;
                font-size: 16px;
                line-height: 30px;
                width: fit-content;
            }
        """

        def get_dimension_template(score, category, color, content):
            stroke_offset = 289.027 * float(score) / 100.0 - 289.027
            template = f"""
                <div style="margin-bottom: 1.5rem;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;">
                        <div style="width: 26px; height: 26px;">
                            <div style="width: 100%; height: 100%;">
                                <div style="margin: 0; width: 100%; height: 100%">
                                    <div style="position: relative; width: 100%; height: 100%;">
                                        <svg viewBox="0 0 100 100">
                                            <path d="M 50,50  m 0,46  a 46,46 1 1 1 0,-92  a 46,46 1 1 1 0,92" stroke-width="8" fill-opacity="0" stroke="#F0F3FF" stroke-linecap="round"></path>
                                            <path d="M 50,50  m 0,46  a 46,46 1 1 1 0,-92  a 46,46 1 1 1 0,92" stroke-width="8" fill-opacity="0" stroke="{color}" stroke-linecap="round" stroke-dasharray="289, 289" stroke-dashoffset="{stroke_offset}"></path>
                                        </svg>
                                        <div style="position: absolute; display: flex; top: 0; width: 100%; height: 100%; justify-content: center; align-items: center;">
                                            <span style="font-weight: 700; font-size: 8px; line-height: 10px; color: {color};">
                                                {int(score)}<span style="font-weight: 700; font-size: 6px; line-height: 7px; color: {color};">%</span>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <h3 style="font-weight: 500; font-size: 14px; line-height: 18px;">{category}</h3>
                    </div>
                    <div>
                        <p>{content}</p>
                    </div>
                </div>
            """
            return template

        dimensions = ""
        for dim in dimensionsData:
            scoreCategory = self.scores_categories.filter(
                category__slug=dim["category_slug"]
            ).first()
            dimensions += (
                get_dimension_template(
                    scoreCategory.value, dim["category"], dim["color"], dim["content"]
                )
                + "\n"
            )

        def get_list_template(content):
            template = f"""
                <li>{content}</li>
            """
            return template

        keyRecommendations = ""
        for kR in keyRecommendationsData:
            keyRecommendations += get_list_template(kR) + "\n"

        bestPractices = ""
        for bP in bestPracticesData:
            bestPractices += get_list_template(bP) + "\n"

        def get_global_scores_template(score, category, color):
            template = f"""
                <div style="display: flex; flex-direction: column; gap: 2px;">
                    <div style="display: flex; justify-content: space-between;">
                        <p class="score">{category}</p>
                        <p class="score">{int(round(score))}%</p>
                    </div>
                    <svg viewBox="0 0 101 2">
                        <line x1="1" y1="1" x2="100" y2="1" stroke-width="2" stroke-linecap="round" stroke="#F0F3FF"></line>
                        <line x1="1" y1="1" x2="{int(round(score))}" y2="1" stroke-width="2" stroke-linecap="round" stroke="{color}"></line>
                    </svg>
                </div>
            """
            return template

        global_scores = ""
        scoreCategories = self.scores_categories.all()
        for sc in scoreCategories:
            if sc.category.slug == "all":
                continue
            global_scores += (
                get_global_scores_template(
                    sc.display_value(), sc.category.name, sc.category.color
                )
                + "\n"
            )

        faviconUrl = "https://app.mixity.io/static/favicon.ico"

        template = f"""
            <!DOCTYPE html>
            <html xml:lang="fr" lang="fr">
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
                <title>Synthèse évaluation</title>
                <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400;1,500;1,700&amp;display=swap" rel="stylesheet">
                <style>
                    {style}
                </style>
            </head>
            <body>
                <div style="margin-left: 2rem; margin-right: 2rem;">
                    <header style="display: flex; width: 100%; justify-content: space-between; margin-bottom: 3rem;">
                        <div style="display: flex; align-items: center; justify-content: center; align-content: center;">
                            <img src="{faviconUrl}" alt="arrow" style="width: 16px;">
                            <h1 style="font-weight: 500; font-size: 14px; margin-left: 6px; line-height: 18px;">Mixity 360</h1>
                        </div>
                        <h1 style="font-weight: 500; font-size: 14px; text-align: right;">Synthèse de mon évaluation</h1>
                    </header>
                    <div>
                        <div style="margin-bottom: 3rem;">
                            <div style="margin-bottom: 2rem;">
                                <div style="display: flex; justify-content: space-between; align-items: start;">
                                    <div style="display: flex; align-items: center;">
                                        <img src="https://app.mixity.io/static/icon/{productSlug}.svg" alt="arrow" style="width: 20px;">
                                        <h1 style="font-weight: 500; font-size: 16px; margin-left: 6px; line-height: 20px;">Mixity {productName}</h1>
                                    </div>
                                    <div style="text-align: right;">
                                        <p style="font-weight: 500; font-size: 14px; line-height: 20px; color: #9094AA; margin-top: 0; margin-bottom: 0;">Score Diversité & Inclusion</p>
                                        <p style="font-weight: 500; font-size: 20px; line-height: 26px; margin-top: 0; margin-bottom: 0;">{scoreDEI}<span style="font-weight: 700; font-size: 12px; line-height: 15px;">/100</span></p>
                                    </div>
                                </div>
                                <div style="display: flex; padding-top: 16px; width: 100%; align-items: center;">
                                    <div style="width: 50%; padding-right: 24px; gap: 16px; display: flex; flex-direction: column;">
                                        {global_scores}
                                    </div>
                                    <div style="width: 50%; padding-left: 16px;">
                                        <img src="{footprint}" alt="footprint" width="100%">
                                    </div>
                                </div>
                            </div>
                            <p>
                                {_("Votre empreinte se lit dans le sens anti-horaire. Votre score Diversité & Inclusion correpond à votre score global. Vous trouverez à gauche votre score précis dans chacune des 5 dimensions évaluées.")}
                            </p>
                        </div>
                        <div style="margin-bottom: 3rem;">
                            <div style="margin-bottom: 1rem; width: fit-content;">
                                <h2 class="title" style="border-bottom: 1px solid #8888E2;">{_("Analyse générale")}</h2>
                            </div>
                            <div>
                                <p style="word-break: break-word;">
                                    {generalAnalysis}
                                </p>
                            </div>
                        </div>
                        <div style="display: flex; margin-bottom: 3rem; padding: 16px; justify-content: space-between; gap: 32px; align-items: start; border: 1px solid transparent; border-radius: 8px; background: linear-gradient(to bottom, white, white), linear-gradient(to right, #3ACFD5, #3A4ED5); background-clip: padding-box, border-box; background-origin: padding-box, border-box;">
                            <div style="display: flex; gap: 10px; justify-content: space-between; align-items: center;">
                                <img src="https://staging.mixity.io/{photo}" alt="{firstName} {lastName}" style="width: 50px; height: 50px; border-radius: 100%;">
                                <div style="width: min-content;">
                                    <h3 style="font-weight: 700; font-size: 12px; line-height: 15px; white-space: nowrap;">{firstName}<span> <span>{lastName}</h3>
                                    <p>{title}</p>	
                                </div>
                            </div>
                            <div">
                                <p>{comment}</p>
                            </div>
                        </div>
                        <div style="margin-bottom: 3rem;">
                            <div style="margin-bottom: 1rem; width: fit-content;">
                                <h2 class="title" style="border-bottom: 1px solid #FF6F6F;">{_("Principales recommandations")}</h2>
                            </div>
                            <div>
                                <ul>
                                    {keyRecommendations}
                                </ul>
                            </div>
                        </div>
                        <div style="margin-bottom: 3rem;">
                            <div style="margin-bottom: 1rem; width: fit-content;">
                                <h2 class="title" style="border-bottom: 1px solid #0099FF;">{_("Bonnes pratiques")}</h2>
                            </div>
                            <div>
                                <ul>
                                    {bestPractices}
                                </ul>
                            </div>
                        </div>
                        <div style="margin-bottom: 3rem;">
                            <div style="margin-bottom: 1rem; width: fit-content;">
                                <h2 class="title" style="border-bottom: 1px solid #47D4FF;">{_("Analyse par dimension")}</h2>
                            </div>
                            {dimensions}
                        </div>
                    </div>
                </div>
            </body>
            </html>
        """
        return template

    def get_general_analysis_clean_version(self):
        instance = self.get_general_analysis
        if not instance:
            return None
        dimension_analysis = []
        for dim in instance.analysis_by_dimension.all():
            dimension_analysis.append(
                {
                    "category": dim.category.name,
                    "content": dim.content,
                    "pk": dim.category.pk,
                    "color": dim.category.color,
                    "category_slug": dim.category.slug,
                }
            )

        result = {
            "general_analysis": instance.content[3:-4],
            "expert": {
                "first_name": instance.expert.first_name,
                "last_name": instance.expert.last_name,
                "title": instance.expert.title,
                "photo": instance.expert.photo.url,
                "comment": instance.comment[3:-4],
            },
            "dimension_analysis": dimension_analysis,
            "key_recommendations": [
                reco.content for reco in instance.key_recommendations.all()
            ],
            "best_practices": [
                best_practice.content
                for best_practice in instance.assess_best_practices.all()
            ],
        }
        return result

    async def generate_pdf_from_html_content(self, html_content):
        filepath = None
        # Get the path of the temporary file
        with NamedTemporaryFile(
            mode="w", prefix="Synthesis_", suffix=".pdf", delete=False
        ) as tmp_write:
            tmp_write.seek(0)
            filepath = tmp_write.name
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch()
                    page = await browser.new_page()
                    await page.set_content(html_content, wait_until="networkidle")
                    await page.pdf(
                        path=filepath,
                        format="A4",
                        print_background=True,
                        margin={
                            "top": "50px",
                            "bottom": "50px",
                            "left": "20px",
                            "right": "20px",
                        },
                    )
                    await browser.close()
                return (True, filepath)
            except Exception as e:
                return (False, f"PDF generation failed: {e}")

    def export_filtered_pdf(
        self, evaluation, subscription_option, filters, cookies, webpackurl
    ):
        if subscription_option.product.slug == "human":
            result = (
                webpackurl
                + "dashboard/"
                + evaluation.entity.slug
                + "/human/assess/pdf/?filter="
                + filters
            )
        else:
            result = (
                webpackurl + "dashboard/" + evaluation.entity.slug + "/diag/assess/pdf/"
            )
        # try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(
                ignore_https_errors=True,
                viewport={"width": 1920, "height": 1080},
                java_script_enabled=True,
            )
            context.set_default_navigation_timeout(120000)
            context.add_cookies(cookies)
            page = context.new_page()
            page.goto(result)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            page.emulate_media()
            with NamedTemporaryFile(
                mode="w", prefix="Summary_", suffix=".pdf", delete=False
            ) as tmp_write:
                pdf_options = {
                    "path": tmp_write.name,
                    "scale": 1,
                    "width": "1920px",
                    "height": "1080px",
                    "margin": {
                        "top": "0",
                        "right": "0",
                        "bottom": "0",
                        "left": "0",
                    },
                    "print_background": True,
                }
                page.pdf(**pdf_options)
                browser.close()
                tmp_write.seek(0)
                input_pdf = PdfFileReader(tmp_write.name)
                output_pdf = PdfFileWriter()
                total_pages = input_pdf.getNumPages()
                merged_page = output_pdf.addBlankPage(
                    input_pdf.getPage(0).mediaBox.getWidth(),
                    input_pdf.getPage(0).mediaBox.getHeight() * (total_pages),
                )
                for i in range(total_pages):
                    actual_page = input_pdf.getPage(i)
                    merged_page.mergeTranslatedPage(
                        actual_page,
                        0,
                        input_pdf.getPage(0).mediaBox.getHeight()
                        * ((total_pages - 1) - i),
                    )
                output_pdf.write(tmp_write.name)
                filepath = tmp_write.name

        # Save the final file
        with open(filepath, "rb") as tmp_read:
            if self.is_validated_by_user:
                self.pdf_sheet.save("human_score.pdf", tmp_read)
        return filepath
        # except Exception as e:
        #     print(e)
        #     return None

    @cached_property
    def is_category_evaluation(self):
        categories_list = MAIN_CATEGORIES_SLUGS
        if self.is_scan:
            categories_list = SCAN_CATEGORIES_SLUGS
        return (
            self.scores_categories.select_related("category")
            .filter(category__slug__in=categories_list)
            .count()
            < 3
            and not self.is_trial
        )

    @cached_property
    def is_trial(self):
        return self.tags.filter(name="trial").exists()

    @property
    def footprint_type(self):
        categories_list = MAIN_CATEGORIES_SLUGS
        if self.is_scan:
            categories_list = SCAN_CATEGORIES_SLUGS
        if not self.is_category_evaluation:
            if self.is_trial:
                sc = self.scores_categories.first()
                if sc and sc.category.slug == "gender":
                    return "gender_locked"
                else:
                    return "disability_locked"
            categories = (
                self.scores_categories.filter(category__slug__in=categories_list)
                .exclude(category__slug__in=["all", "bonus_posture"])
                .order_by("category__slug")
                .values_list("category__slug", flat=True)
            )

            categories_count = len(categories)
            if categories_count == 5:
                return "standard"
            elif categories_count == 4:
                combinaisons = {
                    "gender": "four_minus_gender",
                    "disability": "four_minus_disability",
                    "cultural_diversity": "four_minus_cultural_diversity",
                    "generational_diversity": "four_minus_generational_diversity",
                    "lgbt": "four_minus_lgbt",
                }
                for key, value in combinaisons.items():
                    if key not in categories:
                        return value
            elif categories_count == 3:
                combinaisons = {
                    "gender|disability": "three_minus_gender_and_disability",
                    "gender|cultural_diversity": "three_minus_gender_and_cultural_diversity",
                    "gender|generational_diversity": "three_minus_gender_and_generational_diversity",
                    "gender|lgbt": "three_minus_gender_and_lgbt",
                    "disability|cultural_diversity": "three_minus_disability_and_cultural_diversity",
                    "disability|generational_diversity": "three_minus_disability_and_generational_diversity",
                    "disability|lgbt": "three_minus_disability_and_lgbt",
                    "cultural_diversity|generational_diversity": "three_minus_cultural_diversity_and_generational_diversity",
                    "cultural_diversity|lgbt": "three_minus_cultural_diversity_and_lgbt",
                    "generational_diversity|lgbt": "three_minus_generational_diversity_and_lgbt",
                }
                for key, value in combinaisons.items():
                    cats = key.split("|")
                    if not cats[0] in categories and not cats[1] in categories:
                        return value

        else:
            sc = (
                self.scores_categories.filter(category__slug__in=categories_list)
                .exclude(category__slug__in=["all", "bonus_posture"])
                .first()
            )
            if sc:
                return sc.category.slug
            return None

    def get_radar_data(self, target=None, score_categories=None, human_filter=None):
        def prevent_save(*args, **kwargs):
            pass

        categories_list = MAIN_CATEGORIES_SLUGS
        if self.is_scan:
            categories_list = SCAN_CATEGORIES_SLUGS

        footprint_type = None
        if self.sheet.type.category:
            score_categories = self.scores_categories.filter(
                category_id=self.sheet.type.category_id,
                category__slug__in=categories_list,
            ).first()
            footprint_type = self.sheet.type.category.slug
        elif self.is_category_evaluation:
            score_categories = (
                self.scores_categories.filter(category__slug__in=categories_list)
                .exclude(category__slug__in=["all", "bonus_posture"])
                .select_related("category")
                .first()
            )

        response = {
            "society": self.entity.name.replace("'", " "),
            "type": self.sheet.type.slug,
            "footprint_type": footprint_type or self.footprint_type,
        }  # FIXME special case of "'" creating JSON parsing problems in javascript
        if score_categories and not self.is_campus:
            measures = [
                {
                    "key": score_cat["SubCategorySlug"],
                    "value": score_cat["Value"],
                    "label": ugettext(score_cat["SubCategory"]),
                    "color": score_cat["Color"],
                    "fake": 0,
                }
                for score_cat in score_categories.get_subcategories_values
            ]
        else:
            if self.is_campus and target and not self.is_human:
                score_cats = score_categories
            else:
                score_cats = (
                    self.scores_categories.exclude(
                        category__slug__in=["all", "csrd", "bonus_posture"]
                    )
                    .select_related("category")
                    .filter(category__slug__in=categories_list)
                    .prefetch_related(
                        "category__subcategories",
                    )
                )
            if human_filter and (self.is_human or self.is_scan):
                measures = []
                for sc in score_cats.all():
                    if self.is_campus and self.is_human:
                        sc.value = sc.compute_score(
                            human_filter={
                                "age": human_filter["default"]["age"],
                                "civility": human_filter["default"]["civility"],
                                "status": human_filter["default"]["status"],
                                "human_criteria": HumanCriteriaChoice.objects.filter(
                                    pk__in=human_filter["human_criteria"]
                                ).all(),
                            },
                            in_realtime=True,
                        )
                    else:
                        sc.value = sc.compute_score(
                            human_filter={
                                "age": human_filter["default"]["age"],
                                "civility": human_filter["default"]["civility"],
                                "human_criteria": HumanCriteriaChoice.objects.filter(
                                    pk__in=human_filter["human_criteria"]
                                ).all(),
                            },
                            in_realtime=True,
                        )
                    sc.save = prevent_save
                    if sc.category.slug not in ["all", "bonus_posture"]:
                        measures.append(
                            {
                                "key": sc.category.slug,
                                "value": sc.value + sc.evolution_delta,
                                "label": ugettext(sc.category.name),
                                "color": sc.category.color,
                                "fake": 0,
                            }
                        )
            else:
                measures = [
                    {
                        "key": score_cat.category.slug,
                        "value": score_cat.value + score_cat.evolution_delta,
                        "label": ugettext(score_cat.category.name),
                        "color": score_cat.category.color,
                        "fake": 0,
                    }
                    for score_cat in score_cats
                    if score_cat.category.slug != "all"
                ]
            if self.is_trial:
                tmp_measures = []
                categories = Category.objects.filter(
                    Q(slug="gender")
                    | Q(slug="disability")
                    | Q(slug="cultural_diversity")
                    | Q(slug="generational_diversity")
                    | Q(slug="lgbt")
                )
                for category in categories:
                    if category.slug == measures[0]["key"]:
                        tmp_measures.append(measures[0])
                    else:
                        tmp_measures.append(
                            {
                                "key": category.slug,
                                "value": 50,
                                "label": ugettext(category.name),
                                "color": category.color,
                                "fake": 1,
                            }
                        )
                measures = tmp_measures
            """
            if not score_cats.filter(category__slug="lgbt").exists():
                measures.append(
                    {
                        "key": "lgbt",
                        "value": 50,
                        "label": ugettext("LGBTQIA+"),
                        "color": Category.objects.get(slug="lgbt").color,
                        "fake": 1,
                    }
                )
            """
        response["measures"] = measures
        return response

    @property
    def get_subcategories_values(self):
        answers = (
            self.answers.filter(question__sheets__in=[self.sheet])
            .values(
                "question__category__name",
                "question__category__color",
                "question__subcategory__name",
                "question__subcategory__short_name",
                "question__subcategory_id",
            )
            .annotate(
                total_weight=Sum("question__weight_index"),
                weighted_total=Sum(
                    F("question__weight_index")
                    * Coalesce(
                        F("choice__value"),
                        F("question__none_answer_value"),
                        Value(settings.DEFAULT_CHOICE_VALUE),
                    ),
                    output_field=DecimalField(),
                ),
            )
            .order_by("question__subcategory")
        )
        mean_answers = (
            Answer.objects.filter(
                # evaluation__is_validated_by_user=True,
                question__sheets__in=[self.sheet]
            )
            .values(
                "question__category__name",
                "question__category__color",
                "question__subcategory__name",
                "question__subcategory__short_name",
                "question__subcategory_id",
            )
            .annotate(
                total_weight=Sum("question__weight_index"),
                weighted_total=Sum(
                    F("question__weight_index")
                    * Coalesce(
                        F("choice__value"),
                        F("question__none_answer_value"),
                        Value(settings.DEFAULT_CHOICE_VALUE),
                    ),
                    output_field=DecimalField(),
                ),
            )
            .order_by("question__subcategory")
        )
        means_answers_in_business_line = (
            Answer.objects.filter(
                # evaluation__is_validated_by_user=True,
                question__sheets__in=[self.sheet],
            )
            .filter(
                Q(
                    evaluation__entity__entity_level__structure__business_line=self.entity.entity_level.structure.business_line
                )
                | Q(
                    evaluation__entity__entity_level__structure__secondary_business_lines=self.entity.entity_level.structure.business_line
                )
            )
            .values(
                "question__category__name",
                "question__category__color",
                "question__subcategory__name",
                "question__subcategory__short_name",
                "question__subcategory_id",
            )
            .annotate(
                total_weight=Sum("question__weight_index"),
                weighted_total=Sum(
                    F("question__weight_index")
                    * Coalesce(
                        F("choice__value"),
                        F("question__none_answer_value"),
                        Value(settings.DEFAULT_CHOICE_VALUE),
                    ),
                    output_field=DecimalField(),
                ),
            )
            .order_by("question__subcategory")
        )

        results = []
        mean_results = []
        mean_results_in_business_line = []

        for answer in answers:
            if answer["total_weight"] > 0:
                result = dict()
                result["SubCategory"] = answer["question__subcategory__short_name"]
                result["SubCategory_name"] = answer["question__subcategory__name"]
                result["Color"] = answer["question__category__color"]
                if result["Color"] == "#18FFC3":
                    result["Color"] = "#06766F"  # multicultarcolor is too shiny
                result["Category"] = answer["question__category__name"]
                result["Value"] = (
                    float(answer["weighted_total"]) / float(answer["total_weight"]) * 20
                )  # moyenne / 5 -> note / 100
                results.append(result)

        for answer in mean_answers:
            if answer["total_weight"] > 0:
                result = dict()
                result["SubCategory"] = answer["question__subcategory__short_name"]
                result["SubCategory_name"] = answer["question__subcategory__name"]
                result["Color"] = answer["question__category__color"]
                if result["Color"] == "#18FFC3":
                    result["Color"] = "#06766F"  # multicultarcolor is too shiny
                result["Category"] = answer["question__category__name"]
                result["Value"] = (
                    float(answer["weighted_total"]) / float(answer["total_weight"]) * 20
                )  # moyenne / 5 -> note / 100
                mean_results.append(result)

        for answer in means_answers_in_business_line:
            if answer["total_weight"] > 0:
                result = dict()
                result["SubCategory"] = answer["question__subcategory__short_name"]
                result["SubCategory_name"] = answer["question__subcategory__name"]
                result["Color"] = answer["question__category__color"]
                if result["Color"] == "#18FFC3":
                    result["Color"] = "#06766F"  # multicultarcolor is too shiny
                result["Category"] = answer["question__category__name"]
                result["Value"] = (
                    float(answer["weighted_total"]) / float(answer["total_weight"]) * 20
                )  # moyenne / 5 -> note / 100
                mean_results_in_business_line.append(result)
        return [results, mean_results, mean_results_in_business_line]

    def get_categories_values(self):
        """
        NOTE : This method returns all categories of the evaluation questions in the same order as the google sheet
        """
        if self.answers.all():
            return (
                self.answers.values_list("question__category__name", flat=True)
                .order_by("question__category__order")
                .distinct()
            )
        else:
            # We check only Human case cause in Enterprise there default None answers unlike Human
            if self.is_human:
                mandatory_ids = [q.id for q in self.mandatory_questions.all()]
                forbidden_ids = [q.id for q in self.forbidden_questions.all()]
                questions_ids = [
                    q.id
                    for q in self.get_questions_human(
                        mandatory_question_ids=mandatory_ids,
                        forbidden_question_ids=forbidden_ids,
                    )
                ]
                questions_queryset = Question.objects.filter(id__in=questions_ids)
                return (
                    questions_queryset.values_list("category__name", flat=True)
                    .order_by("category__order")
                    .distinct()
                )

    def create_aims_for_categorie(self, answers, category):
        exist_aims = self.aims.filter(
            answer__question__subcategory__slug=category
        ).count()
        for ans in answers:
            if exist_aims >= 6:
                break
            if ans.choice:
                aim_value = ans.choice.value
                if (
                    ans.question.recommandation is not None
                    and len(ans.question.recommandation) > 0
                    and aim_value < 5
                ):
                    if aim_value < 3:
                        value = 0
                    elif aim_value == 3:
                        value = 1
                    else:
                        value = 2
                    _, is_create = Aim.objects.get_or_create(
                        answer=ans,
                        defaults={
                            "subcategory": ans.question.subcategory,
                            "description_fr": ans.question.recommandation_fr,
                            "description_en": ans.question.recommandation_en,
                            "evaluation": ans.evaluation,
                            "order": ans.question.priority_order,
                            "priority_value": value,
                            "is_auto_generate": True,
                        },
                    )
                    if is_create:
                        exist_aims += 1

    def create_aims(self):
        self.aims.filter(is_auto_generate=True).delete()
        answers_dict = defaultdict(list)
        answers_query = self.answers.select_related(
            "choice",
            "question",
            "evaluation",
            "question__subcategory",
            "question__category",
        ).order_by("choice__value", "question__priority_order")
        for ans in answers_query:
            answers_dict[ans.question.category.slug].append(ans)
        for answers in answers_dict:
            self.create_aims_for_categorie(answers_dict[answers], answers)

    def get_key_figures_questions_by_category(self, questions, cat):
        # This method returns questions related to the key figures fictive subcategory
        key_figures_questions_by_category = list()
        for question in questions:
            # Conditions of key figures questions
            # UI conditions
            not_subquestion_ui_condition = question.ui_type == "slider"
            is_subquestion_ui_condition = question.ui_type == "sq_select"
            # Order_stat subcategory condition

            # get only key figures questions
            if question.order_stat_subcategory == None:
                continue
            # Category condition
            category_condition = question.category.name == cat
            if (
                not_subquestion_ui_condition or is_subquestion_ui_condition
            ) and category_condition:
                key_figures_questions_by_category.append(question)

        return key_figures_questions_by_category

    def get_to_review_question_s_answer_by_category(self, questions, cat):
        # This method returns questions related to the key figures fictive subcategory
        to_review_question_s_answer = list()

        for question in questions:
            # Order_stat subcategory condition
            if not question.answers.filter(evaluation=self).first().to_review:
                continue

            # Category condition
            category_condition = question.category.name == cat

            if category_condition:
                to_review_question_s_answer.append(question)

        return to_review_question_s_answer

    # def get_filtered_workforce_from_evaluation(self, human_filters):
    #     workforce_answer = self.answers.filter(
    #         *prepare_human_filters_queries(
    #             human_filters=human_filters, for_collaborators=False
    #         ),
    #     ).count()
    #     return workforce_answer

    def get_filtered_answers_count(self, human_filters):
        answers = self.get_applicable_answers
        answers = answers.filter(
            *prepare_human_filters_queries(
                human_filters=human_filters, for_collaborators=False, is_human=True
            )
        )
        if "human_criteria" in human_filters:
            criterias = self.human_criteria.filter(
                choices__id__in=human_filters["human_criteria"]
            ).annotate(
                choice_ids=ArrayAgg(
                    "choices__id",
                    filter=Q(choices__id__in=human_filters["human_criteria"]),
                )
            )
            for criteria in criterias:
                answers = answers.filter(
                    collaborator__human_criteria_choices__id__in=criteria.choice_ids
                )
        return answers.count()

    def get_filtered_collaborators_count(self, collaborators):
        return count_collaborators_with_answers(collaborators)

    @cached_property
    def is_the_last_diag(self):
        # On vérifie que l'entité soit rattachée à une structure qui a un pack avec un diag actif.
        today = timezone.now()
        if self.entity.entity_level.structure.subscription_pack.filter(
            end_date__lte=today, is_active=True
        ).exists():
            last_diag_evaluation = self.entity.last_global_evaluation
            return self == last_diag_evaluation
        return False

    def get_subscription_option(self):
        subscription_pack = (
            SubscriptionPack.objects.filter(
                structure=self.entity.entity_level.structure
            )
            .order_by("-start_date")
            .first()
        )
        if self.is_human:
            product = "human"
        else:
            product = "diag"
        return (
            SubscriptionOption.objects.filter(
                subscriptionPack=subscription_pack, product__slug=product
            )
            .order_by("-start_date")
            .first()
        )


class ComputedEvaluation(models.Model):
    """Used for comparison with computed scores"""

    name = models.CharField(
        null=True,
        blank=True,
        max_length=128,
        verbose_name="Nom explicite",
    )
    region = models.ForeignKey(
        "address.State",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Région",
        on_delete=models.CASCADE,
    )
    business_line = models.ForeignKey(
        "accounts.BusinessLine",
        related_name="computed_evaluations",
        on_delete=models.PROTECT,
        verbose_name=_("Secteur d'activité"),
        null=True,
        blank=True,
    )
    score = JSONField(null=True)

    def __str__(self):
        return self.name

    def get_radar_data(self):
        return self.score


class ScoreCategory(models.Model):
    value = models.FloatField(
        verbose_name="Valeur",
        help_text="Calculée à partir des réponses et des avis de l'évaluation",
        editable=False,
        default=0,
    )
    evolution_delta = models.FloatField(
        verbose_name="Delta d'évolution",
        help_text="Ecart à additionner/soustraire à l'évolution",
        default=0,
    )
    category = models.ForeignKey(
        "Category",
        verbose_name=_("Catégorie"),
        on_delete=models.PROTECT,
    )
    evaluation = models.ForeignKey(
        Evaluation,
        models.CASCADE,  # CASCADE car si on supprime l'attribut evaluation cela supprime les ScoreCategory
        related_name="scores_categories",
        verbose_name=_("Evaluation"),
    )
    detail = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Champ libre"),
    )
    aim = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Objectifs"),
    )

    mean_score = models.FloatField(
        null=True,
        default=None,
        verbose_name=_("Score moyen dans mon secteur"),
    )
    mean_score_in_business_line = models.FloatField(
        null=True,
        default=None,
        verbose_name=_("Score moyen dans toutes les entreprises"),
    )
    key_figures_filled = models.BooleanField(
        null=True, default=None, verbose_name=_("Chiffres clés remplis")
    )
    category_answers_rate_cache = models.FloatField(
        null=True, default=None, verbose_name=_("Taux de réponses de la catégorie")
    )
    is_evolution_delta_hidden = models.BooleanField(
        default=False, verbose_name=_("Cacher le delta d'évolution")
    )

    def display_value(self):
        # TODO: remove this method and use "value" once the score is computed with delta added in DB
        return float(self.value + self.evolution_delta)

    class Meta:
        verbose_name = _("Score par Catégorie et par Évaluation")
        unique_together = (("category", "evaluation"),)
        # Warning: this is used in sibling() to find the corresponding ScoreCategory in the previous evaluation
        ordering = ["evaluation_id", "category"]

    def __str__(self):
        return "{} - {} - {}".format(
            self.evaluation.entity.name,
            self.evaluation.name or "",
            self.category,
        )

    @property
    def questions(self):
        return self.evaluation.get_questions_from_answers.filter(
            category_id=self.category_id, display=True
        )

    @property
    def answers(self):
        return self.evaluation.get_applicable_answers.filter(
            question__category_id=self.category_id, question__display=True
        )

    @property
    def questions_weight_index(self):
        return self.answers.aggregate(Sum("question__weight_index"))[
            "question__weight_index__sum"
        ]

    # @property
    def get_scorecategory_detail(
        self, target=None, human_filters=None, in_realtime=False
    ):
        category = self.category.slug
        subcategories = []
        for subcategory_b in self.get_subcategories_values:
            subcategory = subcategory_b["SubCategorySlug"]
            if in_realtime:
                answers = (
                    self.get_filtered_answers(
                        target=target, human_filters=human_filters, in_realtime=True
                    )
                    .filter(
                        question__subcategory__slug=subcategory,
                        question__sheets=self.evaluation.sheet,
                    )
                    .select_related("question", "choice")
                )
            else:
                answers = self.answers.filter(
                    question__category__slug=category,
                    question__subcategory__slug=subcategory,
                    question__sheets=self.evaluation.sheet,
                ).select_related("question", "choice")
            total = 0
            total_max = 0
            for answer in answers:
                if answer.choice and answer.choice.value:
                    value = answer.choice.value
                elif answer.question.none_answer_value:
                    value = answer.question.none_answer_value
                else:
                    value = settings.DEFAULT_CHOICE_VALUE
                if answer.question.weight_index:
                    total += float(value) * float(answer.question.weight_index)
                    total_max += float(answer.question.weight_index)
            if total_max > 0:
                total = total / total_max * 20
            subcategories.append(
                [
                    subcategory_b["SubCategory"],
                    total,
                    subcategory_b["SubCategorySlug"],
                ]
            )
        return subcategories

    @property
    def is_finished(self):
        if self.actions.first() is not None:
            return self.actions.first().is_finished()
        return False

    @property
    def has_key_figures(self):
        return self.questions.filter(order_stat_subcategory__gte=1).count() > 0

    @property
    def category_answers_rate(self):
        if self.evaluation.sheet.type.is_collaborator:
            return 0.0
        if self.category.slug == "csrd":
            answers = self.answers.distinct("question")
        else:
            answers = self.answers.exclude(question__weight_index=0).distinct(
                "question"
            )
        # TODO check distinct working and value_text ?
        nb_answered = answers.exclude(date_answered=None).count()
        nb_questions = answers.count() or 1
        self.category_answers_rate_cache = round(nb_answered / nb_questions, 2)
        self.save()
        return self.category_answers_rate_cache

    def subcategory_answers_rate(self, subcategory):
        if self.evaluation.sheet.type.is_collaborator:
            return 0.0
        # TODO check distinct working
        answers = self.answers.distinct("question").filter(
            question__subcategory=subcategory
        )
        return answers.exclude(date_answered=None).count() / (answers.count() or 1)

    @property
    def get_non_empty_subcategories(self):
        return self.questions.values_list("subcategory", flat=True).distinct()

    def get_filtered_answers(self, target, human_filters, in_realtime):
        """
        This method prepares the answers in function of filters to be able to compute the scores in Realtime and quickly
        """
        answers = self.evaluation.get_applicable_answers
        if target and target != "all":
            answers = answers.filter(
                question__category=self.category, question__target=target
            )
        elif human_filters:
            if in_realtime:
                human_filters_queries = prepare_human_filters_queries(
                    human_filters=human_filters,
                    for_collaborators=False,
                    is_human=self.evaluation.is_human,
                )
                answers = answers.filter(
                    question__category=self.category,
                    *human_filters_queries,
                )
                if "human_criteria" in human_filters:
                    criterias = self.evaluation.human_criteria.filter(
                        choices__id__in=human_filters["human_criteria"]
                    ).annotate(
                        choice_ids=ArrayAgg(
                            "choices__id",
                            filter=Q(choices__id__in=human_filters["human_criteria"]),
                        )
                    )
                    for criteria in criterias:
                        answers = answers.filter(
                            collaborator__human_criteria_choices__id__in=criteria.choice_ids
                        )
            else:
                # Human Classic
                if self.evaluation.is_human and not self.evaluation.is_campus:
                    answers = answers.filter(
                        question__category=self.category,
                        collaborator__civility=human_filters,
                    )
                # Scan Classic
                elif self.evaluation.is_scan:
                    answers = answers.filter(
                        question__category=self.category,
                        scan_collaborator__civility=human_filters,
                    )
                # Human Campus
                elif self.evaluation.is_human and self.evaluation.is_campus:
                    filters = get_filtered_human_campus_slugs(human_filters)
                    answers = answers.filter(
                        question__category=self.category,
                        collaborator__status__in=filters,
                    )
        else:
            answers = answers.filter(question__category=self.category)
        return answers

    def compute_score(self, target=None, human_filter=None, in_realtime=False):
        answers = self.get_filtered_answers(
            target=target, human_filters=human_filter, in_realtime=in_realtime
        )
        answers = answers.values("question__category").aggregate(
            total_weight=Sum("question__weight_index"),
            weighted_total=Sum(
                F("question__weight_index")
                * Coalesce(
                    Case(
                        When(is_not_followed=False, then=F("choice__value")),
                        default=Value(None),
                    ),
                    F("question__none_answer_value"),
                    Value(settings.DEFAULT_CHOICE_VALUE),
                ),
                # TODO F('question__default_value') ??
                output_field=DecimalField(),
            ),
        )
        if answers and answers["weighted_total"] and answers["total_weight"]:
            if self.evaluation.is_scan:
                value = (
                    float(answers["weighted_total"])
                    / float(answers["total_weight"])
                    * 25
                )  # moyenne / 4 -> note / 100
            else:
                value = (
                    float(answers["weighted_total"])
                    / float(answers["total_weight"])
                    * 20
                )  # moyenne / 5 -> note / 100
        else:
            value = 0
        return value

    # Sibling needs to only be related to an evaluation of the same type (Diag needs to have a Diag Sibling, Human an Human sibling)
    @cached_property
    def sibling(self):
        score_category = (
            ScoreCategory.objects.select_related(
                "evaluation", "evaluation__sheet", "evaluation__sheet__type"
            )
            .filter(
                category__slug=self.category.slug,
                evaluation__entity_id=self.evaluation.entity_id,
                evaluation__modified_by_user_date__lt=self.evaluation.modified_by_user_date,
            )
            .exclude(evaluation=self.evaluation)
            .exclude(evaluation__is_validated_by_admin=False)
        )
        if self.evaluation.sheet.type.slug in [
            "mixity_evaluation_globale",
            "mixity_international",
        ]:
            score_category = score_category.filter(
                evaluation__sheet__type__slug__in=[
                    "mixity_evaluation_globale",
                    "mixity_international",
                ]
            )
        else:
            score_category = score_category.filter(
                evaluation__sheet__type__slug=self.evaluation.sheet.type.slug
            )
        return score_category.order_by("evaluation__modified_by_user_date").last()

    @property
    def get_mean_score(self):
        if not self.mean_score:
            self.mean_score = self._mean_score()
            if self.mean_score:
                self.save()
        return self.mean_score

    def _mean_score(self, human_filter=None, in_realtime=None):
        if human_filter:
            mean_score = 0
            scores_categories = ScoreCategory.objects.filter(
                evaluation__is_validated_by_admin=True,
                category=self.category,
                evaluation__sheet__type__tag=self.evaluation.sheet.type.tag,
            )
            for sc in scores_categories:
                mean_score += sc.compute_score(
                    human_filter=human_filter, in_realtime=in_realtime
                )

            if scores_categories.count() != 0:
                mean_score /= scores_categories.count()
        else:
            mean_score = ScoreCategory.objects.filter(
                evaluation__is_validated_by_admin=True,
                category=self.category,
                evaluation__sheet__type__tag=self.evaluation.sheet.type.tag,
            ).aggregate(Avg("value"))["value__avg"]

        return mean_score

    @property
    def get_mean_score_in_business_line(self):
        if not self.mean_score_in_business_line:
            self.mean_score_in_business_line = self._mean_score_in_business_line()
            if self.mean_score_in_business_line:
                self.save()
        return self.mean_score_in_business_line

    def _mean_score_in_business_line(self, human_filter=None, in_realtime=None):
        """
        get the average scores in the main area of the business of all
        Score category of evaluations validated by the administrator and having this sector in primary in secondary

        """
        if human_filter:
            mean_score_in_business_line = 0
            scores_categories = ScoreCategory.objects.filter(
                evaluation__is_validated_by_admin=True,
                category=self.category,
                evaluation__sheet__type__tag=self.evaluation.sheet.type.tag,
            ).filter(
                Q(
                    evaluation__entity__entity_level__structure__business_line=self.evaluation.entity.entity_level.structure.business_line
                )
                | Q(
                    evaluation__entity__entity_level__structure__secondary_business_lines=self.evaluation.entity.entity_level.structure.business_line
                )
            )

            for sc in scores_categories:
                mean_score_in_business_line += sc.compute_score(
                    human_filter=human_filter, in_realtime=in_realtime
                )

            if scores_categories.count() != 0:
                mean_score_in_business_line /= scores_categories.count()
        else:
            mean_score_in_business_line = (
                ScoreCategory.objects.select_related(
                    "evaluation",
                    "evaluation__sheet",
                    "evaluation__sheet__type",
                    "evaluation__entity",
                    "category",
                )
                .filter(
                    evaluation__is_validated_by_admin=True,
                    category=self.category,
                    evaluation__sheet__type__tag=self.evaluation.sheet.type.tag,
                )
                .filter(
                    Q(
                        evaluation__entity__entity_level__structure__business_line=self.evaluation.entity.entity_level.structure.business_line
                    )
                    | Q(
                        evaluation__entity__entity_level__structure__secondary_business_lines=self.evaluation.entity.entity_level.structure.business_line
                    )
                )
                .aggregate(Avg("value"))["value__avg"]
            )

        return mean_score_in_business_line

    @property
    def get_subcategories_details(self):
        answers = (
            self.evaluation.answers.filter(
                question__subcategory__in=self.category.subcategories.filter(
                    questions__sheets=self.evaluation.sheet
                )
            )
            .values(
                "question__subcategory__name",
                "question__subcategory__slug",
                "question__subcategory_id",
            )
            .annotate(
                total_weight=Sum("question__weight_index"),
                weighted_total=Sum(
                    F("question__weight_index")
                    * Coalesce(
                        F("choice__value"),
                        F("question__none_answer_value"),
                        Value(settings.DEFAULT_CHOICE_VALUE),
                    ),
                    output_field=DecimalField(),
                ),
            )
            .order_by("question__subcategory")
        )
        aims = (
            Aim.objects.filter(category=self.category)
            .filter(evaluation=self.evaluation)
            .values("description", "subcategory_id")
            .order_by("subcategory_id")
        )
        for answer in answers:
            answer["value"] = (
                float(answer["weighted_total"]) / float(answer["total_weight"]) * 20
            )  # moyenne / 5 -> note / 100
            answer["aims"] = [
                aim
                for aim in aims
                if aim["subcategory_id"] == answer["question__subcategory_id"]
            ]
        return answers

    @property
    def get_subcategories_values(self):
        answers = (
            self.evaluation.answers.filter(
                question__category=self.category,
                question__subcategory__in=self.category.subcategories.filter(
                    questions__sheets=self.evaluation.sheet
                ),
            )
            .values(
                "question__subcategory__name",
                "question__subcategory__color",
                "question__subcategory__slug",
                "question__subcategory_id",
            )
            .annotate(
                total_weight=Sum("question__weight_index"),
                count=Count("question"),
                weighted_total=Sum(
                    F("question__weight_index")
                    * Coalesce(
                        F("choice__value"),
                        F("question__none_answer_value"),
                        Value(settings.DEFAULT_CHOICE_VALUE),
                    ),
                    output_field=DecimalField(),
                ),
            )
            .order_by("question__subcategory")
        )
        results = []
        for answer in answers:
            if answer["total_weight"] > 0:
                result = dict()
                result["Color"] = answer["question__subcategory__color"]
                result["SubCategorySlug"] = answer["question__subcategory__slug"]
                result["SubCategory"] = ugettext(answer["question__subcategory__name"])
                result["Value"] = (
                    float(answer["weighted_total"]) / float(answer["total_weight"]) * 20
                )  # moyenne / 5 -> note / 100
                results.append(result)
        return results

    # TODO: refactor that to do only 1 query for all aims
    @property
    def get_aims(self):
        aims = self.evaluation.aims.filter(category=self.category).select_related(
            "subcategory"
        )
        aims = aims.order_by("priority_value", "order")[0:6]
        aim_count = aims.count()
        res = []
        aim_categories = [_("À mettre en place"), _("À formaliser"), _("À renforcer")]
        aim_priority = -1
        for aim in aims:
            category = ""
            if aim_priority < aim.priority_value:
                category = aim_categories[aim.priority_value]
                aim_priority = aim.priority_value
            res.append((category, aim))
        return res, aim_count


class Action(models.Model):
    scorecategory = models.ForeignKey(
        ScoreCategory,
        models.CASCADE,
        related_name="actions",
        verbose_name=_("Action"),
    )
    intitules_detail = ArrayField(
        models.TextField(
            max_length=700, blank=True, null=True, verbose_name=_("Intitulé")
        ),
        size=settings.DEFAULT_ACTION_ROW_NUMBER,
        default=init_none,
    )
    descriptif_detail = ArrayField(
        models.TextField(
            max_length=700, blank=True, null=True, verbose_name=_("Descriptif")
        ),
        size=settings.DEFAULT_ACTION_ROW_NUMBER,
        default=init_none,
    )

    intitules_aim = ArrayField(
        models.TextField(
            max_length=700, blank=True, null=True, verbose_name=_("Intitulé")
        ),
        size=settings.DEFAULT_ACTION_ROW_NUMBER,
        default=init_none,
    )
    descriptif_aim = ArrayField(
        models.TextField(
            max_length=700, blank=True, null=True, verbose_name=_("Descriptif")
        ),
        size=settings.DEFAULT_ACTION_ROW_NUMBER,
        default=init_none,
    )

    def is_finished(self):
        details_ok = False
        aim_ok = False
        for i in range(0, settings.DEFAULT_ACTION_ROW_NUMBER):
            if self.intitules_aim[i] is not None and self.descriptif_aim[i] is not None:
                aim_ok = True
            if (
                self.intitules_detail[i] is not None
                and self.descriptif_detail[i] is not None
            ):
                details_ok = True
            if details_ok and aim_ok:
                return True
        return False


class Collaborator(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    civility = models.CharField(
        max_length=125, choices=CIVILITY_CHOICES, blank=True, null=True
    )
    service = models.CharField(
        max_length=125, choices=SERVICE_CHOICES, blank=True, null=True
    )
    tag = models.ForeignKey(
        QuestionTag,
        related_name="collaborator_status",
        verbose_name="Tag",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=125, choices=CAMPUS_CHOICE, blank=True, null=True
    )
    human_criteria_choices = models.ManyToManyField(
        "accounts.HumanCriteriaChoice",
        blank=True,
        related_name="collaborators",
    )
    age = models.CharField(
        max_length=125,
        choices=AGE_CHOICES,
        blank=True,
        null=True,
        verbose_name=_("Age"),
    )

    user = models.OneToOneField(
        MixityUser,
        models.CASCADE,
        related_name="collaborator",
        verbose_name=_("Utilisateur"),
        blank=True,
        null=True,
    )

    is_lgbt = models.BooleanField(default=False)

    evaluation = models.ForeignKey(
        Evaluation,
        models.CASCADE,
        related_name="collaborators",
        verbose_name=_("Evaluation"),
    )

    def get_user(self):
        try:
            return self.user
        except Exception:
            return None

    def get_is_lgbt_display(self):
        return "LGBTQIA+" if self.is_lgbt else "Non LGBTQIA+"


class ScanCollaborator(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    civility = models.CharField(
        max_length=125, choices=CIVILITY_CHOICES, blank=True, null=True
    )
    service = models.CharField(
        max_length=125, choices=SERVICE_CHOICES, blank=True, null=True
    )
    job = models.CharField(
        max_length=125, choices=SCAN_ROLE_CHOICE, blank=True, null=True
    )
    scan_criteria_choices = models.ManyToManyField(
        "accounts.HumanCriteriaChoice",
        blank=True,
        related_name="scan_collaborators",
    )
    tag = models.ForeignKey(
        QuestionTag,
        related_name="scan_collaborator_status",
        verbose_name="Tag",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    age = models.CharField(
        max_length=125,
        choices=AGE_CHOICES,
        blank=True,
        null=True,
        verbose_name=_("Age"),
    )

    user = models.OneToOneField(
        MixityUser,
        models.CASCADE,
        related_name="scan_collaborator",
        verbose_name=_("Utilisateur"),
    )

    is_lgbt = models.BooleanField(default=False)

    evaluation = models.ForeignKey(
        Evaluation,
        models.CASCADE,
        related_name="scan_collaborators",
        verbose_name=_("Evaluation"),
    )
    profile = models.ForeignKey(
        "scoring.Profile",
        models.CASCADE,
        null=True,
        blank=True,
        related_name="scan_collaborators",
        verbose_name=_("Profil Type"),
    )

    def get_user(self):
        return self.user

    def get_is_lgbt_display(self):
        return "LGBTQIA+" if self.is_lgbt else "Non LGBTQIA+"

    def define_collaborator_profile(self):
        global_rate = self.get_global_rate(True)
        profiles = {30: "level1", 60: "level2", 90: "level3", 100: "level4"}
        for ref_value in sorted(profiles.keys()):
            if global_rate["score"] <= ref_value:
                self.profile = Profile.objects.get(slug=profiles[ref_value])
                self.save()
                return

    def get_global_rate(self, first_validation=False):
        if first_validation:
            self.get_categories_rate  # Call it to generate score_categories post first survey validation
        return self._calculate_rate("global")

    @cached_property
    def get_categories_rate(self):
        return self._calculate_rate("category")

    @cached_property
    def get_subcategories_rate(self):
        return self._calculate_rate("subcategory")

    def _calculate_rate(self, rate_type):
        summary = {}
        categories = {}
        answers = (
            self.answers.filter(question__sheets=self.evaluation.sheet)
            .select_related("question", "choice")
            .prefetch_related("choices")
            .order_by("question__category__order")
        )

        for answer in answers:
            value = 0
            if answer.choice and answer.choice.value is not None:
                value = answer.choice.value
            elif answer.question.none_answer_value:
                value = answer.question.none_answer_value
            elif answer.choices and answer.choices.count() > 0:
                for choice in answer.choices.all():
                    if choice.value:
                        value += choice.value
                if value < 0:
                    value = 0

            # Vérifier si la question a un poids
            if answer.question.weight_index:
                if rate_type == "global":
                    slug = "global"
                else:
                    attr = getattr(answer.question, rate_type)
                    slug = attr.slug
                    name = attr.name
                    color = attr.color
                    cat_id = attr.id
                    categories[cat_id] = cat_id

                if slug not in summary and rate_type != "global":
                    summary[slug] = {
                        "name": name,
                        "score": 0,
                        "total_max": 0,
                        "color": color,
                    }
                elif slug not in summary and rate_type == "global":
                    summary[slug] = {"score": 0, "total_max": 0}

                # Ajouter la valeur pondérée
                summary[slug]["score"] += float(value) * float(
                    answer.question.weight_index
                )
                summary[slug]["total_max"] += float(answer.question.weight_index)

        # Calcul du score final
        for slug, values in summary.items():
            total = values["score"]
            total_max = values["total_max"]
            if total_max > 0:
                # On multiplie par 25 au lieu de 20 pour scan
                score = (total / total_max) * 25
            else:
                score = 0
            summary[slug]["score"] = round(score, 2)
            summary[slug].pop("total_max")
        if rate_type == "global":
            return summary["global"]
        if rate_type == "category" and self.evaluation.is_scan:
            all_cat = Category.objects.filter(pk__in=categories)
            self.evaluation.do_initialize_score_categories(all_cat)

        return summary

    @cached_property
    def get_skills_rate(self):
        skills_summary = {}
        answers = (
            self.answers.filter(question__sheets=self.evaluation.sheet)
            .select_related("question", "choice")
            .prefetch_related("choices")
        )

        for answer in answers:
            value = 0
            if answer.choice and answer.choice.value is not None:
                value = answer.choice.value
            elif answer.question.none_answer_value:
                value = answer.question.none_answer_value
            elif answer.choices and answer.choices.count() > 0:
                for choice in answer.choices.all():
                    if choice.value:
                        value += choice.value
                if value < 0:
                    value = 0

            # On continue seulement si la question a un poids et des skills
            if answer.question.weight_index and answer.question.skills_weight:
                # Récupérer les skills et leurs poids
                skills_weight = answer.question.skills_weight

                for skill, weight in skills_weight.items():
                    if skill not in skills_summary:
                        skills_summary[skill] = {"total": 0, "total_max": 0}

                    # Ajouter la valeur pondérée pour chaque skill
                    weighted_value = (
                        float(value)
                        * float(weight)
                        * float(answer.question.weight_index)
                    )
                    skills_summary[skill]["total"] += weighted_value

                    # Ajouter le poids maximum pour ce skill
                    max_weighted_value = float(weight) * float(
                        answer.question.weight_index
                    )
                    skills_summary[skill]["total_max"] += max_weighted_value

        # Calcul du score final pour chaque skill
        for skill, values in skills_summary.items():
            total = values["total"]
            total_max = values["total_max"]
            if total_max > 0:
                # On multiplie par 25 au lieu de 20 pour scan car la valeur maximale pouvant être obtenue par question est 4 et non 5
                score = (total / total_max) * 25
            else:
                score = 0
            name = Skill.objects.get(slug=skill).name
            skills_summary[skill] = {"name": name, "score": round(score, 2)}

        return skills_summary


class ZoneStatistics(models.Model):
    processed_collaborators = models.IntegerField(
        verbose_name="Nombre de collaborateurs traités"
    )
    unprocessed_collaborators = models.IntegerField(
        verbose_name="Nombre de collaborateurs non-traités"
    )
    confidence = models.FloatField(verbose_name="Confiance")
    median = models.FloatField(verbose_name="Médiane des probabilités acceptées")
    raw_data = models.FileField(
        upload_to="name_data/",
        verbose_name="Statistiques brutes",
        storage=RawStorage,
        max_length=255,
    )
    computed_data = JSONField(
        verbose_name="Statistiques calculées", null=True, blank=True
    )

    credits_used = models.IntegerField(verbose_name="Crédits utilisés (théorique)")


class CollaboratorsStatistics(models.Model):
    evaluation = models.ForeignKey(
        Evaluation,
        verbose_name="Evaluation",
        on_delete=models.CASCADE,
        related_name="collaborators_statistics",
    )
    type = models.CharField(max_length=125, choices=TYPE_CHOICES)
    statistics = models.ForeignKey(
        ZoneStatistics,
        verbose_name="Statistiques",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="collaborators_statistics",
    )

    status = models.CharField(
        max_length=2048,
        verbose_name="Status actuel",
        default="processing",
    )
    can_delete = models.BooleanField(
        verbose_name="Est autorisé à re-upload les données ?",
        default=False,
    )

    class Meta:
        unique_together = ("evaluation", "type")

    @property
    def has_one_sub_region(self):
        from mixity.services.namsor.api import Namsor

        regions = set()
        if self.statistics:
            for item in self.statistics.computed_data:
                item_obj = Namsor.get_ethnicity_choices().get(item["name"])
                if item_obj:
                    regions.add(item_obj.sub_region)
            return len(regions) < 2
        logger.exception(
            "Accessing a statistics objects without having any statistics. Shouldn't happen in the company sheet."
        )
        return True

    @property
    def label(self):
        return INDICATOR_LABELS.get(self.type)


class IndicatorType(models.Model):
    slug = models.SlugField(max_length=40, verbose_name="slug")

    class Meta:
        verbose_name = _("Type d'indicateurs")
        verbose_name_plural = _("Types d'indicateurs")

    def __str__(self):
        return self.slug


class Indicator(models.Model):
    type = models.ForeignKey(
        "IndicatorType",
        verbose_name=_("Type d'Indicateur"),
        on_delete=models.CASCADE,
        related_name="indicators",
        blank=True,
        null=True,
    )
    # order = models.IntegerField(default=0)
    title = models.TextField(verbose_name=_("Titre d'Indicateur"))
    selector_labels = models.TextField(
        verbose_name=_("Titre des selecteurs"),
        blank=True,
        null=True,
    )
    selector_link = models.TextField(
        verbose_name=_("Liste des questions liées"),
        blank=True,
        null=True,
    )
    selector = models.BooleanField(default=False)
    colors = models.CharField(
        max_length=30,
        verbose_name=_("Liste d'index des couleurs"),
        blank=True,
        null=True,
    )
    question = models.ForeignKey(
        "Question",
        verbose_name=_("Question d'Indicateur"),
        on_delete=models.CASCADE,
        related_name="indicator",
        null=True,
        blank=True,
    )
    displaying_params = JSONField(
        verbose_name=_("Paramètre d'affichage"),
        null=True,
        blank=True,
    )
    params = models.TextField(
        blank=True, null=True
    )  # TextField and not JSONField to keep the same logic in HumanResultsPerIndicator that uses a json.loads

    class Meta:
        verbose_name = _("Indicateur")
        verbose_name_plural = _("Indicateurs")

    def __str__(self):
        return self.title

    @property
    def get_colors(self):
        if self.colors:
            return [int(c) for c in self.colors.split(",")]
        else:
            return [3]

    @property
    def get_selector_link(self):
        if self.selector_link:
            return [int(q) for q in self.selector_link.split(",")]
        else:
            return None

    @property
    def get_selector_labels(self):
        if self.selector_labels:
            return [l for l in self.selector_labels.split(";")]
        else:
            return [s.label for s in self.question.subquestions.all()]

    def get_results_for_2021001(self, evaluation, answer, queryset=None):
        indicator_values = []
        meanscore_sector_values = []
        meanscore_global_values = []
        params = self.params.split("\n")
        if answer.is_not_applicable or answer.is_not_followed:
            return indicator_values, meanscore_sector_values, meanscore_global_values
        for param in params[0:3]:
            values = answer.get_computed_value(
                evaluation=evaluation, param=param, queryset=queryset
            )
            if len(values) == 3:
                indicator_values.append(round(values[0][0]["value"], 2))
                meanscore_sector_values.append(round(values[1][0]["value"], 2))
                meanscore_global_values.append(round(values[2][0]["value"], 2))
            else:
                indicator_values.append(0)
                meanscore_sector_values.append(0)
                meanscore_global_values.append(0)

        return indicator_values, meanscore_sector_values, meanscore_global_values

    def get_results_for_20221001(self, evaluation, answer, queryset=None):
        business_line = evaluation.entity.entity_level.structure.business_line
        all_question_answers = (
            Answer.objects.filter(question=answer.question, display=True)
            .select_related(
                "evaluation__entity__entity_level__structure__business_line"
            )
            .prefetch_related(
                "evaluation__entity__entity_level__structure__secondary_business_lines",
                Prefetch(
                    "subanswers",
                    queryset=SubAnswer.objects.select_related("subquestion"),
                ),
            )
        )
        indicator_values = []
        meanscore_sector_values = []
        meanscore_global_values = []

        params = json.loads(self.params)

        if answer.is_not_applicable or answer.is_not_followed:
            return indicator_values, meanscore_sector_values, meanscore_global_values
        subs = [answer.subanswers.all()]
        global_subs = []
        sector_subs = []
        meanscores = defaultdict(float)
        meanscores_sector = defaultdict(float)
        for answer in all_question_answers:
            for sub in answer.subanswers.all():
                if not sub.subquestion.id in meanscores:
                    meanscores[sub.subquestion.id] = 0
                if sub.value is not None:
                    meanscores[sub.subquestion.id] += sub.value
                if not sub.subquestion.id in meanscores_sector:
                    meanscores_sector[sub.subquestion.id] = 0
                if (
                    answer.evaluation.entity.entity_level.structure.business_line
                    == business_line
                    or business_line
                    in answer.evaluation.entity.entity_level.structure.secondary_business_lines.all()
                ):
                    if sub.value is not None:
                        meanscores_sector[sub.subquestion.id] += sub.value

        temp = []
        temp_sector = []
        for subquestion_id, total_value in meanscores.items():
            temp.append(total_value)
        for subquestion_id, total_value in meanscores_sector.items():
            temp_sector.append(total_value)
        global_subs.append(temp)
        sector_subs.append(temp_sector)

        for sub in subs:
            res = 0
            for s in sub[0:3]:
                res += s.value if s.value else 0
            femmes = [round(s.value / res * 100, 2) if s.value else 0 for s in sub[0:1]]
            hommes = [round(s.value / res * 100, 2) if s.value else 0 for s in sub[1:2]]
            nb = [round(s.value / res * 100, 2) if s.value else 0 for s in sub[2:3]]
            indicator_values.append([sum(femmes)])
            indicator_values.append([sum(hommes)])
            indicator_values.append([sum(nb)])
        for sub in global_subs:
            res = 0
            for s in sub[0:3]:
                res += s if s else 0
            global_femmes = [round(s / res * 100, 2) if s else 0 for s in sub[0:1]]
            global_hommes = [round(s / res * 100, 2) if s else 0 for s in sub[1:2]]
            global_nb = [round(s / res * 100, 2) if s else 0 for s in sub[2:3]]
            meanscore_global_values.append([sum(global_femmes)])
            meanscore_global_values.append([sum(global_hommes)])
            meanscore_global_values.append([sum(global_nb)])
        for sub in sector_subs:
            res = 0
            for s in sub[0:3]:
                res += s if s else 0
            sector_femmes = [round(s / res * 100, 2) if s else 0 for s in sub[0:1]]
            sector_hommes = [round(s / res * 100, 2) if s else 0 for s in sub[1:2]]
            sector_nb = [round(s / res * 100, 2) if s else 0 for s in sub[2:3]]
            meanscore_sector_values.append([sum(sector_femmes)])
            meanscore_sector_values.append([sum(sector_hommes)])
            meanscore_sector_values.append([sum(sector_nb)])
        return indicator_values, meanscore_sector_values, meanscore_global_values

    def get_results_for_20248002(self, evaluation, answer, queryset=None):
        business_line = evaluation.entity.entity_level.structure.business_line
        all_question_answers = (
            Answer.objects.filter(question=answer.question, display=True)
            .select_related(
                "evaluation__entity__entity_level__structure__business_line"
            )
            .prefetch_related(
                "evaluation__entity__entity_level__structure__secondary_business_lines",
                Prefetch(
                    "subanswers",
                    queryset=SubAnswer.objects.select_related("subquestion"),
                ),
            )
        )
        indicator_values = []
        meanscore_sector_values = []
        meanscore_global_values = []

        params = json.loads(self.params)

        if answer.is_not_applicable or answer.is_not_followed:
            return indicator_values, meanscore_sector_values, meanscore_global_values
        subs = [answer.subanswers.all()]
        global_subs = []
        sector_subs = []
        meanscores = defaultdict(float)
        meanscores_sector = defaultdict(float)
        for answer in all_question_answers:
            for sub in answer.subanswers.all():
                if not sub.subquestion.id in meanscores:
                    meanscores[sub.subquestion.id] = 0
                if sub.value is not None:
                    meanscores[sub.subquestion.id] += sub.value
                if not sub.subquestion.id in meanscores_sector:
                    meanscores_sector[sub.subquestion.id] = 0
                if (
                    answer.evaluation.entity.entity_level.structure.business_line
                    == business_line
                    or business_line
                    in answer.evaluation.entity.entity_level.structure.secondary_business_lines.all()
                ):
                    if sub.value is not None:
                        meanscores_sector[sub.subquestion.id] += sub.value

        temp = []
        temp_sector = []
        for subquestion_id, total_value in meanscores.items():
            temp.append(total_value)
        for subquestion_id, total_value in meanscores_sector.items():
            temp_sector.append(total_value)
        global_subs.append(temp)
        sector_subs.append(temp_sector)
        for google_id in self.get_selector_link:
            temp = []
            temp_sector = []
            temp_ans = Answer.objects.filter(
                question__google_sheets_id=google_id,
                evaluation=evaluation,
            ).first()
            subs.append(temp_ans.subanswers.all())
            temp_all_question_answers = (
                Answer.objects.filter(question=temp_ans.question, display=True)
                .select_related(
                    "evaluation__entity__entity_level__structure__business_line"
                )
                .prefetch_related(
                    "evaluation__entity__entity_level__structure__secondary_business_lines",
                    Prefetch(
                        "subanswers",
                        queryset=SubAnswer.objects.select_related("subquestion"),
                    ),
                )
            )
            temp_meanscores = defaultdict(float)
            temp_meanscores_sector = defaultdict(float)
            for answer in temp_all_question_answers:
                for sub in answer.subanswers.all():
                    if not sub.subquestion.id in temp_meanscores:
                        temp_meanscores[sub.subquestion.id] = 0
                    if sub.value is not None:
                        temp_meanscores[sub.subquestion.id] += sub.value
                    if not sub.subquestion.id in temp_meanscores_sector:
                        temp_meanscores_sector[sub.subquestion.id] = 0
                    if (
                        answer.evaluation.entity.entity_level.structure.business_line
                        == business_line
                        or business_line
                        in answer.evaluation.entity.entity_level.structure.secondary_business_lines.all()
                    ):
                        if sub.value is not None:
                            temp_meanscores_sector[sub.subquestion.id] += sub.value

            for subquestion_id, total_value in temp_meanscores.items():
                temp.append(total_value)
            global_subs.append(temp)
            for subquestion_id, total_value in temp_meanscores_sector.items():
                temp_sector.append(total_value)
            sector_subs.append(temp_sector)

        for sub in subs:
            res = 0
            for s in sub:
                res += s.value if s.value else 0
            femmes = [round(s.value / res * 100, 2) if s.value else 0 for s in sub[0:4]]
            hommes = [round(s.value / res * 100, 2) if s.value else 0 for s in sub[4:8]]
            nb = [round(s.value / res * 100, 2) if s.value else 0 for s in sub[8:12]]
            femmes.append(sum(femmes))
            hommes.append(sum(hommes))
            nb.append(sum(nb))
            indicator_values.append([femmes, hommes, nb])
        for sub in global_subs:
            res = 0
            for s in sub:
                res += s if s else 0
            global_femmes = [round(s / res * 100, 2) if s else 0 for s in sub[0:4]]
            global_hommes = [round(s / res * 100, 2) if s else 0 for s in sub[4:8]]
            global_nb = [round(s / res * 100, 2) if s else 0 for s in sub[8:12]]
            global_femmes.append(sum(global_femmes))
            global_hommes.append(sum(global_hommes))
            global_nb.append(sum(global_nb))
            meanscore_global_values.append([global_femmes, global_hommes, global_nb])
        for sub in sector_subs:
            res = 0
            for s in sub:
                res += s if s else 0
            sector_femmes = [round(s / res * 100, 2) if s else 0 for s in sub[0:4]]
            sector_hommes = [round(s / res * 100, 2) if s else 0 for s in sub[4:8]]
            sector_nb = [round(s / res * 100, 2) if s else 0 for s in sub[8:12]]
            sector_femmes.append(sum(sector_femmes))
            sector_hommes.append(sum(sector_hommes))
            sector_nb.append(sum(sector_nb))
            meanscore_sector_values.append([sector_femmes, sector_hommes, sector_nb])
        return indicator_values, meanscore_sector_values, meanscore_global_values

    def get_results_for_20236002(self, evaluation, answer, queryset=None):
        business_line = evaluation.entity.entity_level.structure.business_line
        all_question_answers = (
            Answer.objects.filter(question=answer.question, display=True)
            .select_related(
                "evaluation__entity__entity_level__structure__business_line"
            )
            .prefetch_related(
                "evaluation__entity__entity_level__structure__secondary_business_lines",
                Prefetch(
                    "subanswers",
                    queryset=SubAnswer.objects.select_related("subquestion"),
                ),
            )
        )
        indicator_values = []
        meanscore_sector_values = []
        meanscore_global_values = []

        params = json.loads(self.params)

        if answer.is_not_applicable or answer.is_not_followed:
            return indicator_values, meanscore_sector_values, meanscore_global_values
        subs = [answer.subanswers.all()]
        global_subs = []
        sector_subs = []
        meanscores = defaultdict(float)
        meanscores_sector = defaultdict(float)
        for answer in all_question_answers:
            for sub in answer.subanswers.all():
                if not sub.subquestion.id in meanscores:
                    meanscores[sub.subquestion.id] = 0
                if sub.value is not None:
                    meanscores[sub.subquestion.id] += sub.value
                if not sub.subquestion.id in meanscores_sector:
                    meanscores_sector[sub.subquestion.id] = 0
                if (
                    answer.evaluation.entity.entity_level.structure.business_line
                    == business_line
                    or business_line
                    in answer.evaluation.entity.entity_level.structure.secondary_business_lines.all()
                ):
                    if sub.value is not None:
                        meanscores_sector[sub.subquestion.id] += sub.value

        temp = []
        temp_sector = []
        for subquestion_id, total_value in meanscores.items():
            temp.append(total_value)
        for subquestion_id, total_value in meanscores_sector.items():
            temp_sector.append(total_value)
        global_subs.append(temp)
        sector_subs.append(temp_sector)
        for google_id in self.get_selector_link:
            temp = []
            temp_sector = []
            temp_ans = Answer.objects.filter(
                question__google_sheets_id=google_id,
                evaluation=evaluation,
            ).first()
            subs.append(temp_ans.subanswers.all())
            temp_all_question_answers = (
                Answer.objects.filter(question=temp_ans.question, display=True)
                .select_related(
                    "evaluation__entity__entity_level__structure__business_line"
                )
                .prefetch_related(
                    "evaluation__entity__entity_level__structure__secondary_business_lines",
                    Prefetch(
                        "subanswers",
                        queryset=SubAnswer.objects.select_related("subquestion"),
                    ),
                )
            )
            temp_meanscores = defaultdict(float)
            temp_meanscores_sector = defaultdict(float)
            for answer in temp_all_question_answers:
                for sub in answer.subanswers.all():
                    if not sub.subquestion.id in temp_meanscores:
                        temp_meanscores[sub.subquestion.id] = 0
                    if sub.value is not None:
                        temp_meanscores[sub.subquestion.id] += sub.value
                    if not sub.subquestion.id in temp_meanscores_sector:
                        temp_meanscores_sector[sub.subquestion.id] = 0
                    if (
                        answer.evaluation.entity.entity_level.structure.business_line
                        == business_line
                        or business_line
                        in answer.evaluation.entity.entity_level.structure.secondary_business_lines.all()
                    ):
                        if sub.value is not None:
                            temp_meanscores_sector[sub.subquestion.id] += sub.value

            for subquestion_id, total_value in temp_meanscores.items():
                temp.append(total_value)
            global_subs.append(temp)
            for subquestion_id, total_value in temp_meanscores_sector.items():
                temp_sector.append(total_value)
            sector_subs.append(temp_sector)

        for sub in subs:
            res = 0
            for s in sub:
                res += s.value if s.value else 0
            femmes = [round(s.value / res * 100, 2) if s.value else 0 for s in sub[0:4]]
            hommes = [round(s.value / res * 100, 2) if s.value else 0 for s in sub[4:8]]
            nb = [round(s.value / res * 100, 2) if s.value else 0 for s in sub[8:12]]
            femmes.append(sum(femmes))
            hommes.append(sum(hommes))
            nb.append(sum(nb))
            indicator_values.append([femmes, hommes, nb])
        for sub in global_subs:
            res = 0
            for s in sub:
                res += s if s else 0
            global_femmes = [round(s / res * 100, 2) if s else 0 for s in sub[0:4]]
            global_hommes = [round(s / res * 100, 2) if s else 0 for s in sub[4:8]]
            global_nb = [round(s / res * 100, 2) if s else 0 for s in sub[8:12]]
            global_femmes.append(sum(global_femmes))
            global_hommes.append(sum(global_hommes))
            global_nb.append(sum(global_nb))
            meanscore_global_values.append([global_femmes, global_hommes, global_nb])
        for sub in sector_subs:
            res = 0
            for s in sub:
                res += s if s else 0
            sector_femmes = [round(s / res * 100, 2) if s else 0 for s in sub[0:4]]
            sector_hommes = [round(s / res * 100, 2) if s else 0 for s in sub[4:8]]
            sector_nb = [round(s / res * 100, 2) if s else 0 for s in sub[8:12]]
            sector_femmes.append(sum(sector_femmes))
            sector_hommes.append(sum(sector_hommes))
            sector_nb.append(sum(sector_nb))
            meanscore_sector_values.append([sector_femmes, sector_hommes, sector_nb])
        return indicator_values, meanscore_sector_values, meanscore_global_values

    def get_results(self, evaluation, answer, queryset=None):
        indicator_values = []
        meanscore_sector_values = []
        meanscore_global_values = []
        params = json.loads(self.params)
        business_lines = [
            evaluation.entity.entity_level.structure.business_line,
            *evaluation.entity.entity_level.structure.secondary_business_lines.all(),
        ]

        if evaluation.is_human:
            values = answer.get_computed_value(
                evaluation=evaluation, param=self.params, queryset=queryset
            )
            if not values:
                return (
                    indicator_values,
                    meanscore_sector_values,
                    meanscore_global_values,
                )

            if self.question.type == "subquestions":
                sub_val = [sub["choices"] for sub in values[0]]
                sub_sector = [sub["choices"] for sub in values[1]]
                sub_global = [sub["choices"] for sub in values[2]]
                for temp_val, temp_sector, temp_global in zip(
                    sub_val, sub_sector, sub_global
                ):
                    indicator_values.append(
                        [round(value["value"], 2) for value in temp_val]
                    )
                    meanscore_sector_values.append(
                        [round(value["value"], 2) for value in temp_sector]
                    )
                    meanscore_global_values.append(
                        [round(value["value"], 2) for value in temp_global]
                    )
            else:
                for value, sector, global_val in zip(values[0], values[1], values[2]):
                    if value.get("evaluation_id") and value.get("label"):
                        indicator_values.append(round(value["value"], 2))
                        meanscore_sector_values.append(round(sector["value"], 2))
                        meanscore_global_values.append(round(global_val["value"], 2))
        else:
            all_question_answers = (
                Answer.objects.filter(
                    Q(question=answer.question.sibling) | Q(question=answer.question),
                    display=True,
                )
                .select_related(
                    "evaluation__entity__entity_level__structure__business_line"
                )
                .prefetch_related(
                    "evaluation__entity__entity_level__structure__secondary_business_lines",
                    Prefetch(
                        "subanswers",
                        queryset=SubAnswer.objects.select_related("subquestion"),
                    ),
                )
            )
            if params["type"] == "ratio":
                indicator_values.append(
                    round(answer.ratio_value, 2)
                    if answer.ratio_value is not None
                    else None
                )
                meanscore = all_question_answers.exclude(ratio_value=None).aggregate(
                    avg_ratio=Avg("ratio_value")
                )["avg_ratio"]
                if meanscore:
                    meanscore_global_values.append(round(meanscore, 2))
                meanscore_sector = (
                    all_question_answers.exclude(ratio_value=None)
                    .filter(
                        evaluation__entity__entity_level__structure__business_line__in=business_lines
                    )
                    .aggregate(avg_ratio=Avg("ratio_value"))["avg_ratio"]
                )
                if meanscore_sector:
                    meanscore_sector_values.append(round(meanscore_sector, 2))
            elif params["type"] == "value":
                indicator_values.append(
                    round(answer.value, 2) if answer.value is not None else None
                )
                meanscore = all_question_answers.exclude(value=None).aggregate(
                    avg_value=Avg("value")
                )["avg_value"]
                if meanscore:
                    meanscore_global_values.append(
                        round(
                            meanscore,
                            2,
                        )
                    )
                meanscore_sector = (
                    all_question_answers.exclude(value=None)
                    .filter(
                        evaluation__entity__entity_level__structure__business_line__in=business_lines
                    )
                    .aggregate(avg_value=Avg("value"))["avg_value"]
                )
                if meanscore_sector:
                    meanscore_sector_values.append(
                        round(
                            meanscore_sector,
                            2,
                        )
                    )
            elif params["type"] == "date" and answer.value:
                date = datetime.fromtimestamp(answer.value)
                indicator_values.append(date.strftime("%d/%m/%Y"))
            elif params["type"] == "subquestions":
                for sub in answer.subanswers.all():
                    indicator_values.append(
                        round(sub.value, 2) if sub.value is not None else None
                    )
                meanscores = defaultdict(float)
                subquestion_counts = defaultdict(int)
                meanscores_sector = defaultdict(float)
                subquestion_counts_sector = defaultdict(int)

                for answer in all_question_answers:
                    for sub in answer.subanswers.all():
                        if sub.value is not None:
                            meanscores[sub.subquestion.id] += sub.value
                            subquestion_counts[sub.subquestion.id] += 1
                        if (
                            sub.value is not None
                            and answer.evaluation.entity.entity_level.structure.business_line
                            in business_lines
                        ):
                            meanscores_sector[sub.subquestion.id] += sub.value
                            subquestion_counts_sector[sub.subquestion.id] += 1

                for subquestion_id, total_value in meanscores.items():
                    count = subquestion_counts[subquestion_id]
                    if total_value and count > 0:
                        mean_value = total_value / count
                        meanscore_global_values.append(round(mean_value, 2))
                for subquestion_id, total_value in meanscores_sector.items():
                    count = subquestion_counts_sector[subquestion_id]
                    if total_value and count > 0:
                        mean_value = total_value / count
                        meanscore_sector_values.append(round(mean_value, 2))
            elif params["type"] == "subquestions_gap":
                if answer.subanswers.all().count() >= 2:
                    women = answer.subanswers.all()[0].value
                    men = answer.subanswers.all()[1].value
                    if women and men:
                        indicator_values.append(round(men - women, 2))
                    else:
                        indicator_values.append(None)

                count = 0
                count_sector = 0
                meanscore = 0
                meanscore_sector = 0
                for answer in all_question_answers:
                    subanswers = list(answer.subanswers.all())
                    if len(subanswers) >= 2:
                        women = subanswers[0].value
                        men = subanswers[1].value
                        if women and men:
                            meanscore += men - women
                            count += 1
                    if (
                        len(subanswers) >= 2
                        and answer.evaluation.entity.entity_level.structure.business_line
                        in business_lines
                    ):
                        women = subanswers[0].value
                        men = subanswers[1].value
                        if women and men:
                            meanscore_sector += ((men - women) / men) * 100
                            count_sector += 1
                if meanscore and count > 0:
                    meanscore_global_values.append(round((meanscore / count), 2))
                if meanscore_sector and count_sector > 0:
                    meanscore_sector_values.append(
                        round((meanscore_sector / count_sector), 2)
                    )
            elif params["type"] == "subquestions_gap_ratio":
                if answer.subanswers.all().count() >= 2:
                    women = answer.subanswers.all()[0].value
                    men = answer.subanswers.all()[1].value
                    if women and men:
                        indicator_values.append(round(((men - women) / men) * 100, 2))
                    else:
                        indicator_values.append(None)

                count = 0
                count_sector = 0
                meanscore = 0
                meanscore_sector = 0
                for answer in all_question_answers:
                    subanswers = list(answer.subanswers.all())
                    if len(subanswers) >= 2:
                        women = subanswers[0].value
                        men = subanswers[1].value
                        if women and men:
                            meanscore += ((men - women) / men) * 100
                            count += 1
                    if (
                        len(subanswers) >= 2
                        and answer.evaluation.entity.entity_level.structure.business_line
                        in business_lines
                    ):
                        women = subanswers[0].value
                        men = subanswers[1].value
                        if women and men:
                            meanscore_sector += ((men - women) / men) * 100
                            count_sector += 1
                if meanscore and count > 0:
                    meanscore_global_values.append(round((meanscore / count), 2))
                if meanscore_sector and count_sector > 0:
                    meanscore_sector_values.append(
                        round((meanscore_sector / count_sector), 2)
                    )
            elif params["type"] == "subquestions_group":
                if answer.subanswers.all().count() > 0:
                    femmes = [
                        (
                            round(answer.subanswers.all()[0].value, 2)
                            if answer.subanswers.all()[0].value is not None
                            else None
                        )
                    ]
                    hommes = [
                        (
                            round(answer.subanswers.all()[1].value, 2)
                            if answer.subanswers.all()[1].value is not None
                            else None
                        )
                    ]
                    nb = [
                        (
                            round(answer.subanswers.all()[2].value, 2)
                            if answer.subanswers.all()[2].value is not None
                            else None
                        )
                    ]
                    meanscores_count = [0, 0, 0]
                    meanscores = [0, 0, 0]
                    meanscores_count_sector = [0, 0, 0]
                    meanscores_sector = [0, 0, 0]
                    for answer in all_question_answers:
                        subanswers = list(answer.subanswers.all())
                        if subanswers:
                            if len(subanswers) >= 0:
                                for i in range(3):
                                    if subanswers[i].value is not None:
                                        meanscores[i] += subanswers[i].value
                                        meanscores_count[i] += 1
                        if (
                            subanswers
                            and answer.evaluation.entity.entity_level.structure.business_line
                            in business_lines
                        ):
                            if len(subanswers) >= 0:
                                for i in range(3):
                                    if subanswers[i].value is not None:
                                        meanscores_sector[i] += subanswers[i].value
                                        meanscores_count_sector[i] += 1
                    global_femmes = [
                        (
                            round(meanscores[0] / meanscores_count[0], 2)
                            if meanscores[0] != 0 and meanscores_count[0] != 0
                            else None
                        )
                    ]
                    global_hommes = [
                        (
                            round(meanscores[1] / meanscores_count[1], 2)
                            if meanscores[1] != 0 and meanscores_count[1] != 0
                            else None
                        )
                    ]
                    global_nb = [
                        (
                            round(meanscores[2] / meanscores_count[2], 2)
                            if meanscores[2] != 0 and meanscores_count[2] != 0
                            else None
                        )
                    ]
                    sector_femmes = [
                        (
                            round(meanscores_sector[0] / meanscores_count_sector[0], 2)
                            if meanscores_sector[0] != 0
                            and meanscores_count_sector[0] != 0
                            else None
                        )
                    ]
                    sector_hommes = [
                        (
                            round(meanscores_sector[1] / meanscores_count_sector[1], 2)
                            if meanscores_sector[1] != 0
                            and meanscores_count_sector[1] != 0
                            else None
                        )
                    ]
                    sector_nb = [
                        (
                            round(meanscores_sector[2] / meanscores_count_sector[2], 2)
                            if meanscores_sector[2] != 0
                            and meanscores_count_sector[2] != 0
                            else None
                        )
                    ]
                else:
                    femmes = [
                        round(answer.value, 2) if answer.value is not None else None
                    ]
                    hommes = [
                        (
                            round(100 - answer.value, 2)
                            if answer.value is not None
                            else None
                        )
                    ]
                    nb = None
                    global_nb = None
                    meanscores_count = 0
                    meanscores = [0, 0]
                    meanscores_count_sector = 0
                    meanscores_sector = [0, 0]
                    for answer in all_question_answers:
                        if answer.value is not None:
                            meanscores[0] += answer.value
                            meanscores[1] += 100 - answer.value
                            meanscores_count += 1
                        if (
                            answer.value is not None
                            and answer.evaluation.entity.entity_level.structure.business_line
                            in business_lines
                        ):
                            meanscores_sector[0] += answer.value
                            meanscores_sector[1] += 100 - answer.value
                            meanscores_count_sector += 1
                    global_femmes = [
                        (
                            round(meanscores[0] / meanscores_count, 2)
                            if meanscores[0] != 0 and meanscores_count != 0
                            else None
                        )
                    ]
                    global_hommes = [
                        (
                            round(meanscores[1] / meanscores_count, 2)
                            if meanscores[1] != 0 and meanscores_count != 0
                            else None
                        )
                    ]
                    sector_femmes = [
                        (
                            round(meanscores_sector[0] / meanscores_count_sector, 2)
                            if meanscores_sector[0] != 0
                            and meanscores_count_sector != 0
                            else None
                        )
                    ]
                    sector_hommes = [
                        (
                            round(meanscores_sector[1] / meanscores_count_sector, 2)
                            if meanscores_sector[1] != 0
                            and meanscores_count_sector != 0
                            else None
                        )
                    ]

                if self.selector_link:
                    for google_id in self.get_selector_link:
                        temp_ans = Answer.objects.filter(
                            question__google_sheets_id=google_id,
                            evaluation=evaluation,
                        ).first()
                        if temp_ans:
                            temp_all_question_answers = (
                                Answer.objects.filter(
                                    Q(question=temp_ans.question.sibling)
                                    | Q(question=temp_ans.question),
                                    display=True,
                                )
                                .select_related(
                                    "evaluation__entity__entity_level__structure__business_line"
                                )
                                .prefetch_related(
                                    "subanswers",
                                    "evaluation__entity__entity_level__structure__secondary_business_lines",
                                )
                            )
                            if temp_ans.subanswers.all().count() > 0:
                                femmes.append(
                                    round(temp_ans.subanswers.all()[0].value, 2)
                                    if temp_ans.subanswers.all()[0].value is not None
                                    else None
                                )
                                hommes.append(
                                    round(temp_ans.subanswers.all()[1].value, 2)
                                    if temp_ans.subanswers.all()[1].value is not None
                                    else None
                                )
                                nb.append(
                                    round(temp_ans.subanswers.all()[2].value, 2)
                                    if temp_ans.subanswers.all()[2].value is not None
                                    else None
                                )
                                meanscores_count = [0, 0, 0]
                                meanscores = [0, 0, 0]
                                meanscores_count_sector = [0, 0, 0]
                                meanscores_sector = [0, 0, 0]
                                for answer in temp_all_question_answers:
                                    subanswers = list(answer.subanswers.all())
                                    if subanswers:
                                        if len(subanswers) >= 0:
                                            for i in range(3):
                                                if subanswers[i].value is not None:
                                                    meanscores[i] += subanswers[i].value
                                                    meanscores_count[i] += 1
                                    if (
                                        subanswers
                                        and answer.evaluation.entity.entity_level.structure.business_line
                                        in business_lines
                                    ):
                                        if len(subanswers) >= 0:
                                            for i in range(3):
                                                if subanswers[i].value is not None:
                                                    meanscores_sector[i] += subanswers[
                                                        i
                                                    ].value
                                                    meanscores_count_sector[i] += 1
                                global_femmes.append(
                                    round(meanscores[0] / meanscores_count[0], 2)
                                    if meanscores[0] != 0 and meanscores_count[0] != 0
                                    else None
                                )
                                global_hommes.append(
                                    round(meanscores[1] / meanscores_count[1], 2)
                                    if meanscores[1] != 0 and meanscores_count[1] != 0
                                    else None
                                )
                                global_nb.append(
                                    round(meanscores[2] / meanscores_count[2], 2)
                                    if meanscores[2] != 0 and meanscores_count[2] != 0
                                    else None
                                )
                                sector_femmes.append(
                                    round(
                                        meanscores_sector[0]
                                        / meanscores_count_sector[0],
                                        2,
                                    )
                                    if meanscores_sector[0] != 0
                                    and meanscores_count_sector[0] != 0
                                    else None
                                )
                                sector_hommes.append(
                                    round(
                                        meanscores_sector[1]
                                        / meanscores_count_sector[1],
                                        2,
                                    )
                                    if meanscores_sector[1] != 0
                                    and meanscores_count_sector[1] != 0
                                    else None
                                )
                                sector_nb.append(
                                    round(
                                        meanscores_sector[2]
                                        / meanscores_count_sector[2],
                                        2,
                                    )
                                    if meanscores_sector[2] != 0
                                    and meanscores_count_sector[2] != 0
                                    else None
                                )
                            else:
                                femmes.append(
                                    round(temp_ans.value, 2)
                                    if temp_ans.value is not None
                                    else None
                                )
                                hommes.append(
                                    round(100 - temp_ans.value, 2)
                                    if temp_ans.value is not None
                                    else None
                                )
                                meanscores_count = 0
                                meanscores = [0, 0]
                                meanscores_count_sector = 0
                                meanscores_sector = [0, 0]
                                for answer in temp_all_question_answers:
                                    if answer.value is not None:
                                        meanscores[0] += answer.value
                                        meanscores[1] += 100 - answer.value
                                        meanscores_count += 1
                                    if (
                                        answer.value is not None
                                        and answer.evaluation.entity.entity_level.structure.business_line
                                        in business_lines
                                    ):
                                        meanscores_sector[0] += answer.value
                                        meanscores_sector[1] += 100 - answer.value
                                        meanscores_count_sector += 1
                                global_femmes.append(
                                    round(meanscores[0] / meanscores_count, 2)
                                    if meanscores[0] != 0 and meanscores_count != 0
                                    else None
                                )
                                global_hommes.append(
                                    round(meanscores[1] / meanscores_count, 2)
                                    if meanscores[1] != 0 and meanscores_count != 0
                                    else None
                                )
                                sector_femmes.append(
                                    round(
                                        meanscores_sector[0] / meanscores_count_sector,
                                        2,
                                    )
                                    if meanscores_sector[0] != 0
                                    and meanscores_count_sector != 0
                                    else None
                                )
                                sector_hommes.append(
                                    round(
                                        meanscores_sector[1] / meanscores_count_sector,
                                        2,
                                    )
                                    if meanscores_sector[1] != 0
                                    and meanscores_count_sector != 0
                                    else None
                                )
                if nb is None:
                    indicator_values = [femmes, hommes]
                    meanscore_global_values = [global_femmes, global_hommes]
                    meanscore_sector_values = [sector_femmes, sector_hommes]
                else:
                    indicator_values = [femmes, hommes, nb]
                    meanscore_global_values = [global_femmes, global_hommes, global_nb]
                    meanscore_sector_values = [sector_femmes, sector_hommes, sector_nb]
            elif params["type"] == "custom_label_subquestions":
                indicator_values = [
                    [
                        (
                            round(answer.subanswers.all()[0].value, 2)
                            if answer.subanswers.count() >= 2
                            and answer.subanswers.all()[0].value is not None
                            else None
                        ),
                    ],
                    [
                        (
                            round(answer.subanswers.all()[1].value, 2)
                            if answer.subanswers.count() >= 2
                            and answer.subanswers.all()[1].value is not None
                            else None
                        ),
                    ],
                ]
                if self.selector_link:
                    for google_id in self.get_selector_link:
                        temp_ans = Answer.objects.filter(
                            question__google_sheets_id=google_id,
                            evaluation=evaluation,
                        ).first()
                        if temp_ans:
                            indicator_values[0].append(
                                round(temp_ans.subanswers.all()[0].value, 2)
                                if temp_ans.subanswers.count() >= 2
                                and temp_ans.subanswers.all()[0].value is not None
                                else None
                            )
                            indicator_values[1].append(
                                round(temp_ans.subanswers.all()[1].value, 2)
                                if temp_ans.subanswers.count() >= 2
                                and temp_ans.subanswers.all()[1].value is not None
                                else None
                            )
            elif params["type"] == "value_group":
                indicator_values.append(answer.value)
                meanscore = all_question_answers.exclude(value=None).aggregate(
                    avg_ratio=Avg("value")
                )["avg_ratio"]
                if meanscore:
                    meanscore_global_values.append(round(meanscore, 2))
                meanscore_sector = (
                    all_question_answers.exclude(ratio_value=None)
                    .filter(
                        evaluation__entity__entity_level__structure__business_line__in=business_lines
                    )
                    .aggregate(avg_ratio=Avg("ratio_value"))["avg_ratio"]
                )
                if meanscore_sector:
                    meanscore_sector_values.append(round(meanscore_sector, 2))
                if self.selector_link:
                    for google_id in self.get_selector_link:
                        temp_ans = Answer.objects.filter(
                            question__google_sheets_id=google_id,
                            evaluation=evaluation,
                        ).first()
                        indicator_values.append(temp_ans.value)
                        temp_all_question_answers = (
                            Answer.objects.filter(
                                Q(question=temp_ans.question.sibling)
                                | Q(question=temp_ans.question),
                                display=True,
                            )
                            .exclude(value=None)
                            .select_related(
                                "evaluation__entity__entity_level__structure__business_line"
                            )
                        )
                        meanscore = temp_all_question_answers.aggregate(
                            avg_ratio=Avg("value")
                        )["avg_ratio"]
                        if meanscore:
                            meanscore_global_values.append(round(meanscore, 2))
                        meanscore_sector = temp_all_question_answers.filter(
                            evaluation__entity__entity_level__structure__business_line__in=business_lines
                        ).aggregate(avg_ratio=Avg("ratio_value"))["avg_ratio"]
                        if meanscore_sector:
                            meanscore_sector_values.append(round(meanscore_sector, 2))

        if (answer.is_not_applicable or answer.is_not_followed) and not params[
            "type"
        ] == "subquestions_group":
            return [None], meanscore_sector_values, meanscore_global_values
        return indicator_values, meanscore_sector_values, meanscore_global_values

    def get_all_labels(self, evaluation):
        selector_labels = self.get_selector_labels
        labels = [c.label for c in self.question.choices.all()]
        params = json.loads(self.params)
        if params["type"] == "subquestions":
            if self.selector and self.get_selector_link:
                labels = [[s.label for s in self.question.subquestions.all()]]
                for google_id in self.get_selector_link:
                    q = Question.objects.get(google_sheets_id=google_id)
                    labels.append([s.label for s in q.subquestions.all()])
            else:
                labels = [s.label for s in self.question.subquestions.all()]
        elif params["type"] == "value_group":
            labels = selector_labels
        elif self.selector:
            labels = [labels]
            for i in range(1, len(selector_labels)):
                labels.append(labels[0])
        elif params["type"] == "subquestions_group" and self.get_selector_link:
            for i, google_id in enumerate(self.get_selector_link):
                if (
                    not evaluation.answers.filter(
                        question__google_sheets_id=google_id
                    ).count()
                    > 0
                ):
                    selector_labels.remove(self.get_selector_labels[i + 1])
            labels = selector_labels
        return selector_labels, labels

    def get_json(self, evaluation, answer, queryset=None):

        def prevent_save(reset_mean_score=True):
            pass

        if self.question.google_sheets_id == 2021001:
            selector_labels = []
            labels = [_("Hommes"), _("Femmes"), _("Non-binaires")]
            (
                indicator_values,
                meanscore_sector_values,
                meanscore_global_values,
            ) = self.get_results_for_2021001(evaluation, answer, queryset)
        elif self.question.google_sheets_id == 20236155:
            selector_labels = []
            labels = [answer.custom_question_label]
            if self.selector_link:
                for google_id in self.get_selector_link:
                    temp_ans = Answer.objects.filter(
                        question__google_sheets_id=google_id,
                        evaluation=evaluation,
                    ).first()
                    if temp_ans:
                        labels.append(temp_ans.custom_question_label)
            (
                indicator_values,
                meanscore_sector_values,
                meanscore_global_values,
            ) = self.get_results(evaluation, answer, queryset)
        elif self.question.google_sheets_id == 20221042:
            selector_labels = []
            labels = [answer.custom_question_label]
            if self.selector_link:
                for google_id in self.get_selector_link:
                    temp_ans = Answer.objects.filter(
                        question__google_sheets_id=google_id,
                        evaluation=evaluation,
                    ).first()
                    if temp_ans:
                        labels.append(temp_ans.custom_question_label)
            (
                indicator_values,
                meanscore_sector_values,
                meanscore_global_values,
            ) = self.get_results(evaluation, answer, queryset)
        elif self.question.google_sheets_id == 20221001:
            selector_labels = []
            labels = [_("Total")]
            (
                indicator_values,
                meanscore_sector_values,
                meanscore_global_values,
            ) = self.get_results_for_20221001(evaluation, answer)
        elif self.question.google_sheets_id == 20248002:
            selector_labels = self.get_selector_labels
            labels = [
                _("- de 26 ans"),
                _("26 à 39 ans"),
                _("40 à 54 ans"),
                _("55 ans et +"),
                _("Total"),
            ]
            (
                indicator_values,
                meanscore_sector_values,
                meanscore_global_values,
            ) = self.get_results_for_20248002(evaluation, answer)
        elif self.question.google_sheets_id == 20236002:
            selector_labels = self.get_selector_labels
            labels = [
                _("- de 26 ans"),
                _("26 à 39 ans"),
                _("40 à 54 ans"),
                _("55 ans et +"),
                _("Total"),
            ]
            (
                indicator_values,
                meanscore_sector_values,
                meanscore_global_values,
            ) = self.get_results_for_20236002(evaluation, answer)
        elif self.selector and self.get_selector_link:
            selector_labels, labels = self.get_all_labels(evaluation)
            indicator_values = []
            meanscore_sector_values = []
            meanscore_global_values = []
            temp_val, temp_sector, temp_global = self.get_results(
                evaluation, answer, queryset
            )
            indicator_values.append(temp_val)
            meanscore_sector_values.append(temp_sector)
            meanscore_global_values.append(temp_global)
            for i, google_id in enumerate(self.get_selector_link):
                if (
                    not evaluation.answers.filter(
                        question__google_sheets_id=google_id
                    ).count()
                    > 0
                ):
                    selector_labels.remove(self.get_selector_labels[i + 1])
                    continue
                if evaluation.is_human:
                    temp_ans = Answer(
                        id=google_id,
                        question=Question.objects.get(google_sheets_id=google_id),
                        evaluation=evaluation,
                    )
                    temp_ans.save = prevent_save
                else:
                    temp_ans = Answer.objects.filter(
                        question__google_sheets_id=google_id,
                        evaluation=evaluation,
                    ).first()

                temp_val, temp_sector, temp_global = self.get_results(
                    evaluation, temp_ans, queryset
                )
                indicator_values.append(temp_val)
                meanscore_sector_values.append(temp_sector)
                meanscore_global_values.append(temp_global)
        else:
            selector_labels, labels = self.get_all_labels(evaluation)
            (
                indicator_values,
                meanscore_sector_values,
                meanscore_global_values,
            ) = self.get_results(evaluation, answer, queryset)

        if evaluation.is_human and self.type.slug == "ProgressBarChart":
            while len(selector_labels) > len(indicator_values):
                indicator_values.append(0)
            sorted_data = sorted(
                zip(selector_labels, indicator_values), key=lambda x: x[1], reverse=True
            )
            selector_labels, indicator_values = zip(*sorted_data)

        if evaluation.is_human and queryset.exclude(evaluation=evaluation).count() == 0:
            temp_queryset = Collaborator.objects.filter()
            if self.question.google_sheets_id == 2021001:
                (
                    temp_values,
                    meanscore_sector_values,
                    meanscore_global_values,
                ) = self.get_results_for_2021001(evaluation, answer, temp_queryset)
            elif self.selector and self.get_selector_link:
                meanscore_sector_values = []
                meanscore_global_values = []
                temp_val, temp_sector, temp_global = self.get_results(
                    evaluation, answer, temp_queryset
                )
                meanscore_sector_values.append(temp_sector)
                meanscore_global_values.append(temp_global)
                for i, google_id in enumerate(self.get_selector_link):
                    if (
                        not evaluation.answers.filter(
                            question__google_sheets_id=google_id
                        ).count()
                        > 0
                    ):
                        continue
                    temp_ans = Answer(
                        id=google_id,
                        question=Question.objects.get(google_sheets_id=google_id),
                        evaluation=evaluation,
                    )
                    temp_ans.save = prevent_save
                    temp_val, temp_sector, temp_global = self.get_results(
                        evaluation, temp_ans, temp_queryset
                    )
                    meanscore_sector_values.append(temp_sector)
                    meanscore_global_values.append(temp_global)
            else:
                (
                    temp_values,
                    meanscore_sector_values,
                    meanscore_global_values,
                ) = self.get_results(evaluation, answer, temp_queryset)
        result = {
            "id": self.question.google_sheets_id,
            "indicator_type": self.type.slug,
            "title": self.title,
            "colors": self.get_colors,
            "display_params": self.displaying_params,
            "labels": labels,
            "selector_labels": selector_labels,
            "selector": self.selector,
            "values": indicator_values,
            "meanscore_sector_values": meanscore_sector_values,
            "meanscore_global_values": meanscore_global_values,
        }
        return result


class GeneralAnalysis(models.Model):
    evaluation = models.OneToOneField(
        "Evaluation", on_delete=models.CASCADE, related_name="general_analysis"
    )
    content = models.TextField(verbose_name=_("Analyse"))
    comment = models.TextField(verbose_name=_("Commentaire"))
    expert = models.ForeignKey(
        "ExpertDei",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="general_analysis",
        verbose_name=_("Expert DEI"),
    )


class ExpertDei(models.Model):
    first_name = models.CharField(max_length=100, verbose_name=_("Prénom"))
    last_name = models.CharField(max_length=100, verbose_name=_("Nom"))
    photo = models.ImageField(upload_to="expert_photo/", verbose_name=_("Photo"))
    title = models.CharField(max_length=50, verbose_name=_("Titre"))

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class AnalysisByDimension(models.Model):
    analysis = models.ForeignKey(
        "GeneralAnalysis",
        on_delete=models.CASCADE,
        related_name="analysis_by_dimension",
    )
    category = models.ForeignKey(
        "Category", on_delete=models.CASCADE, related_name="analysis_by_dimension"
    )
    content = models.TextField()


class KeyRecommendation(models.Model):
    analysis = models.ForeignKey(
        "GeneralAnalysis", on_delete=models.CASCADE, related_name="key_recommendations"
    )
    content = models.TextField()


class AssessmentBestPractice(models.Model):
    analysis = models.ForeignKey(
        "GeneralAnalysis",
        on_delete=models.CASCADE,
        related_name="assess_best_practices",
    )
    content = models.TextField()


class Profile(models.Model):
    name = models.TextField(verbose_name=_("Nom du profil"))
    slug = models.SlugField()
    order = models.IntegerField(verbose_name=_("Ordre"), default=0)
    strenght = models.TextField(
        max_length=4096, blank=True, null=True, verbose_name=_("Point Fort")
    )
    improvement = models.TextField(
        max_length=4096, blank=True, null=True, verbose_name=_("Axe d'amélioration")
    )
    type = models.TextField(
        max_length=128, blank=True, null=True, verbose_name=_("Solution")
    )

    class Meta:
        verbose_name = _("Profil")
        verbose_name_plural = _("Profiles")
        ordering = ("order",)

    def __str__(self):
        return ugettext(self.name)


class Skill(models.Model):
    name = models.TextField(verbose_name=_("Nom de la compétence"))
    slug = models.SlugField()
    order = models.IntegerField(verbose_name=_("Ordre"), default=0)
    color = models.CharField(
        max_length=50,
        verbose_name="Couleur",
        default="#EBEAEA",  # light grey
        blank=True,
    )

    class Meta:
        verbose_name = _("Compétence")
        verbose_name_plural = _("Compétences")
        ordering = ("order",)

    def __str__(self):
        return ugettext(self.name)


class IAScanAnalysisElement(models.Model):
    analysis = models.ForeignKey(
        "IAScanAnalysis",
        related_name="ia_scan_analysis_elements",
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        "Category",
        null=True,
        verbose_name=_("Catégorie"),
        on_delete=models.CASCADE,
    )
    type = models.TextField(verbose_name=_("Type"))
    content = models.TextField(verbose_name=_("Analyse"))


class IAScanAnalysis(models.Model):
    evaluation = models.ForeignKey(
        "Evaluation",
        related_name="ia_scan_analysis",
        on_delete=models.CASCADE,
    )
    scan_collaborator = models.ForeignKey(
        "ScanCollaborator",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    is_validated_by_admin = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Validée par l'Admin",
    )
