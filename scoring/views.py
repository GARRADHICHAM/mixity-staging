import io
import logging
import math
import json
from django.core.exceptions import PermissionDenied
import datetime
import os.path
from time import mktime
from typing import Dict
import base64
import django_filters
from collections import defaultdict
from constance import config as constanceconfig
from dal import autocomplete
from dal_select2.widgets import Select2
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import NON_FIELD_ERRORS
from django.conf import settings
from django_rq import job
from accounts.mails import send
from django.template.loader import render_to_string
from django.db.models import Q, Prefetch, Min, F, Subquery, OuterRef, Max, Count
from django.db.models.functions import Abs
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, get_language, activate
from django.views.generic import (
    FormView,
    CreateView,
    DetailView,
    UpdateView,
    RedirectView,
    View,
)
from django.views.generic.edit import FormMixin
from django.views.generic.base import TemplateResponseMixin
from django_filters import FilterSet
from django_filters.views import FilterView

from django.core.files.base import ContentFile, File
from tempfile import NamedTemporaryFile

import requests
from playwright.sync_api import sync_playwright
from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseRedirect,
    FileResponse,
)

from accounts.mails import send_mail_mixity_start_validated
from accounts.vocabularies import (
    TARGET_CHOICE,
    MONTHS,
    CIVILITY_CHOICES,
)
from accounts.forms import CollaboratorCriteriaChoiceForm
from accounts.models import Structure, BusinessLine, Entity, HumanCriteriaChoice
from accounts.vocabularies import CATEGORY_CHOICES
from mixity.settings import (
    SMALL_COMPANY_LIMIT,
    MIDDLE_COMPANY_LIMIT,
    VERY_SMALL_COMPANY_LIMIT,
    HUMAN_FILTER_LIMIT,
    COMPANY_50_250,
)
from scoring.charts import StructureFootPrint
from scoring.forms import (
    EvaluationCreationForm,
    EvaluationFillForm,
    EvaluationCategoryConfirmForm,
    EvaluationConfirmForm,
    EvaluationSearchForm,
    EvaluationComparisonForm,
)
from scoring.models import (
    Evaluation,
    ScoreCategory,
    Category,
    SubCategory,
    Answer,
    Choice,
    Comment,
    ComputedEvaluation,
    QuestionSheet,
    SubAnswer,
    Action,
    QuestionTag,
    get_filtered_human_campus_slugs,
    get_human_campus_short_slugs,
    Collaborator,
    CollaboratorsStatistics,
    Aim,
    MAIN_CATEGORIES_SLUGS,
)
from scoring.mails import (
    alert_evaluation_created_mail,
    send_evaluation_created_mail,
    alert_evaluation_published_mail,
)
from subscriptions.permissions import CanEvaluateMixin
from subscriptions.models import SubscriptionPack, SubscriptionOption, Product
from django.utils.text import slugify
import socket

import asyncio

logger = logging.getLogger(__name__)


def get_webpack_ip():
    webpack_ip = (
        socket.gethostbyname("webpack") + ":" + str(os.environ.get("PORT", 8080))
    )
    return webpack_ip


# def filter_structure_evaluation(evaluations):
#     """
#     From a queryset given in input:
#     - Removes double structure evaluation
#     - Excludes non relevant evaluations (like French one if language != 'fr')
#     """
#     structure_ids = set([])
#     filtered_evaluations = []
#     # TODO: restore this code when some international footprint will be available
#     # if get_language() != "fr":
#     #     evaluations = evaluations.filter(sheet__type__slug="mixity_international")
#
#     # Remove doubles
#     for evaluation in evaluations:
#         if evaluation.entity.entity_level.structure.id in structure_ids:
#             continue
#         structure_ids.add(evaluation.entity.entity_level.structure.id)
#         filtered_evaluations.append(evaluation)
#     return filtered_evaluations


@job("default")
def export_pdf_with_job(
    evaluation_id, subscription_option, email, language, filter, cookies, webpackurl
):
    evaluation = Evaluation.objects.get(pk=evaluation_id)
    if evaluation:
        activate(language)
        html_content = render_to_string(
            "mails/evaluation_questions_sheet_export.html",
            {"evaluation": evaluation, "with_filters": False},
        )
        filepath = evaluation.export_filtered_pdf(
            evaluation, subscription_option, filter, cookies, webpackurl
        )
        structure_name = evaluation.entity.name
        email_list = [email]
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Summary_{structure_name}_{stamp}.pdf"
        with open(filepath, "rb") as file:
            subject = _("Votre récapitulatif {} du : {}")
            send(
                subject.format(structure_name, stamp),
                email_list,
                html_content,
                [(filename, file, "application/pdf")],
            )

        # Removing the named temporary file once the mail is sent
        os.remove(filepath)

    else:
        logger.warning("Evaluation not found !")


def pdf_sheet_available(pdf_sheet):
    """Le PDF stocké (Cloudinary) est-il encore téléchargeable ?"""
    if not pdf_sheet:
        return False
    if not pdf_sheet.url.startswith("http"):  # stockage local (développement)
        return pdf_sheet.storage.exists(pdf_sheet.name)
    try:
        response = requests.head(pdf_sheet.url, timeout=5, allow_redirects=True)
    except requests.RequestException:
        return False
    return response.status_code == 200


# Masqués dans le PDF : menu latéral, en-tête et boutons d'action.
PDF_HIDDEN_CSS = (
    "#dashboard_sider, header, nav.navbar, .assess_secondary_btn, .assess_white_btn,"
    " .dropdown, #crisp-chatbox, .crisp-client {display: none !important;}"
)


@job("default")
def regenerate_pdf_sheet_with_job(evaluation_id, language, base_url, session_key, email):
    """
    Régénère le PDF des résultats quand le fichier stocké a disparu : la page de résultats
    est imprimée avec Chromium, enregistrée sur l'évaluation puis envoyée par mail.
    """
    evaluation = Evaluation.objects.get(pk=evaluation_id)
    activate(language)
    product = "human" if evaluation.is_human else "diag"
    url = base_url.rstrip("/") + reverse(
        "dashboard:dashboard_assess",
        args=(evaluation.entity.slug, product, evaluation.display_version_slugified),
    )
    with NamedTemporaryFile(prefix="Summary_", suffix=".pdf", delete=False) as tmp:
        filepath = tmp.name
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            ignore_https_errors=True, viewport={"width": 1440, "height": 1000}
        )
        context.add_cookies(
            [
                {"name": settings.SESSION_COOKIE_NAME, "value": session_key, "url": base_url},
                {"name": settings.LANGUAGE_COOKIE_NAME, "value": language, "url": base_url},
            ]
        )
        page = context.new_page()
        page.goto(url, wait_until="load", timeout=120000)
        page.wait_for_timeout(3000)
        page.add_style_tag(content=PDF_HIDDEN_CSS)
        page.emulate_media(media="screen")
        height = page.evaluate("document.documentElement.scrollHeight")
        page.pdf(
            path=filepath,
            width="1440px",
            height=f"{height + 50}px",
            print_background=True,
        )
        browser.close()

    with open(filepath, "rb") as file:
        evaluation.pdf_sheet.save("pdf.pdf", File(file))
    html_content = render_to_string(
        "mails/evaluation_questions_sheet_export.html",
        {"evaluation": evaluation, "with_filters": False},
    )
    structure_name = evaluation.entity.name
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(filepath, "rb") as file:
        subject = _("Votre récapitulatif {} du : {}")
        send(
            subject.format(structure_name, stamp),
            [email],
            html_content,
            [(f"Summary_{structure_name}_{stamp}.pdf", file, "application/pdf")],
        )
    os.remove(filepath)


@job("default")
def export_questions_sheet_with_job(evaluation_id, email, language):
    """
    NOTE : Function using job decorator must take only simple types in arguments
    """
    evaluation = Evaluation.objects.get(pk=evaluation_id)
    if evaluation:
        activate(language)
        html_content = render_to_string(
            "mails/evaluation_questions_sheet_export.html",
            {"evaluation": evaluation, "with_filters": False},
        )
        filepath = evaluation.export_answer_sheet()
        structure_name = evaluation.entity.name
        email_list = [email]
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Summary_{structure_name}_{stamp}.xlsx"
        with open(filepath, "rb") as file:
            subject = _("Votre récapitulatif {} du : {}")
            send(
                subject.format(structure_name, stamp),
                email_list,
                html_content,
                [(filename, file, "application/ms-excel")],
            )

        # Removing the named temporary file once the mail is sent
        os.remove(filepath)

    else:
        logger.warning("Evaluation not found !")


@job("default")
def export_excel_sheet_with_job(
    main_evaluation_id, evaluation_id_list, email, language, filter
):
    """
    NOTE : Function using job decorator must take only simple types in arguments
    """
    main_evaluation = Evaluation.objects.get(pk=main_evaluation_id)
    if main_evaluation:
        activate(language)
        html_content = render_to_string(
            "mails/evaluation_questions_sheet_export.html",
            {"evaluation": main_evaluation, "with_filters": False},
        )
        if len(evaluation_id_list) == 0:
            evaluation_id_list.append(main_evaluation.id)
        evaluation_list = [Evaluation.objects.get(pk=id) for id in evaluation_id_list]
        if len(evaluation_list) == 1:
            main_evaluation = evaluation_list[0]
        filepath = main_evaluation.export_answer_sheet_filtered(evaluation_list, filter)
        structure_name = "+".join(
            [
                Evaluation.objects.get(pk=eval_id).entity.name
                for eval_id in evaluation_id_list
            ]
        )
        email_list = [email]
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Summary_{structure_name}_{stamp}.xlsx"
        with open(filepath, "rb") as file:
            subject = _("Votre récapitulatif {} du : {}")
            send(
                subject.format(structure_name, stamp),
                email_list,
                html_content,
                [(filename, file, "application/ms-excel")],
            )

        # Removing the named temporary file once the mail is sent
        os.remove(filepath)

    else:
        logger.warning("Evaluation not found !")


@job("default")
def export_react_questions_filtered_sheet_with_job(
    evaluation_id, email, language, filter
):
    """
    NOTE : Function using job decorator must take only simple types in arguments
    """
    evaluation = Evaluation.objects.get(pk=evaluation_id)
    if evaluation:
        activate(language)
        html_content = render_to_string(
            "mails/evaluation_questions_sheet_export.html",
            {"evaluation": evaluation, "with_filters": False},
        )
        filepath = evaluation.export_filtered_answer_sheet_react(filter)
        structure_name = evaluation.entity.name
        email_list = [email]
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Summary_{structure_name}_{stamp}.xlsx"
        with open(filepath, "rb") as file:
            subject = _("Votre récapitulatif {} du : {}")
            send(
                subject.format(structure_name, stamp),
                email_list,
                html_content,
                [(filename, file, "application/ms-excel")],
            )

        # Removing the named temporary file once the mail is sent
        os.remove(filepath)

    else:
        logger.warning("Evaluation not found !")


@job("default")
def aggregate_answers(direct_parent_entity_id, subscription_option, questions_ids):
    """
    NOTE : Function using job decorator must take only simple types in arguments
    """

    entity = Entity.objects.get(id=direct_parent_entity_id)

    # Subquery permettant de récupérer la dernière évaluation non human créée pour chaque entité
    # + pratique que last_global_evaluation pour l'intégrer aux requêtes suivantes
    latest_evaluation_date_subquery = (
        Evaluation.objects.exclude(sheet__type__slug="evaluation_collaborator_360")
        .filter(entity=OuterRef("evaluation__entity"))
        .values("entity")
        .annotate(latest_version=Max("created_date"))
        .values("latest_version")[:1]
    )

    while entity is not None:
        # Getting every children answers and every parent's answers that will get aggregated values
        answers_to_aggregate = list(
            Answer.objects.filter(
                evaluation__created_date=latest_evaluation_date_subquery,
                evaluation__entity=entity,
            )
            .select_related("question")
            .prefetch_related(
                "subanswers__choice",
                "subanswers__subquestion",
                "question__subquestions",
                "question__choices",
            )
            .filter(question__id__in=questions_ids)
        )
        children_answers = (
            Answer.objects.filter(
                evaluation__entity__in=entity.children_entities.all(),
                evaluation__created_date=latest_evaluation_date_subquery,
                question__in=questions_ids,
            )
            .select_related("question")
            .prefetch_related(
                "subanswers__choice",
                "subanswers__subquestion",
                "question__subquestions",
                "evaluation__entity",
            )
        )

        for answer in answers_to_aggregate:
            if (
                answer.question.google_sheets_id == 20236001
                or answer.blocked_aggregation
                or answer.question.display_custom_question_label
            ):
                # Dodging this one because it's a date answer
                continue

            if "subquestions" in answer.question.type:
                # Setting up the subanswers list
                subanswers_to_update = []
                if not answer.subanswers.all():
                    for subquestion in answer.question.subquestions.all():
                        subanswers_to_update.append(
                            SubAnswer(
                                value=None, subquestion=subquestion, answer=answer
                            )
                        )
                else:
                    subanswers_to_update = list(answer.subanswers.all())

                for subanswer in subanswers_to_update:
                    # Setting up the total workforce of entities that answered the current subanswer
                    total_workforce = 0
                    for child_answer in children_answers.filter(
                        question=answer.question
                    ):
                        for child_subanswer in child_answer.subanswers.filter(
                            subquestion=subanswer.subquestion
                        ):
                            if child_subanswer.value is not None:
                                total_workforce += (
                                    child_answer.evaluation.entity.workforce
                                )
                    if total_workforce <= 0:
                        continue
                    else:
                        subanswer.value = None
                    for child_answer in children_answers.filter(
                        question=answer.question
                    ):
                        # Aggregate subanswers value/choice
                        for child_subanswer in child_answer.subanswers.filter(
                            subquestion=subanswer.subquestion
                        ):
                            if (
                                "pourcentage" in subanswer.subquestion.ui_type
                                or "qcm" in subanswer.subquestion.ui_type
                            ) and child_subanswer.value is not None:
                                if subanswer.value is None:
                                    subanswer.value = 0
                                subanswer.value += round(
                                    (
                                        child_answer.evaluation.entity.workforce
                                        / total_workforce
                                    )
                                    * child_subanswer.value,
                                    2,
                                )
                            elif child_subanswer.value is not None:
                                if subanswer.value is None:
                                    subanswer.value = 0
                                subanswer.value += child_subanswer.value
                    if "qcm" in answer.question.type and subanswer.value is not None:
                        subanswer.value = round(subanswer.value)
                        if (
                            isinstance(subanswer.value, Choice)
                            and subanswer.choice != subanswer.value
                        ):
                            subanswer.choice = subanswer.value

                # Update or create the subanswers
                if answer.subanswers.all():
                    SubAnswer.objects.bulk_update(subanswers_to_update, ["value"])
                else:
                    SubAnswer.objects.bulk_create(subanswers_to_update)
            else:
                # Setting up the total workforce of entities that answered the current answer
                total_workforce = 0
                for child_answer in children_answers.filter(question=answer.question):
                    if (
                        child_answer.value is not None
                        or child_answer.choice is not None
                    ):
                        total_workforce += child_answer.evaluation.entity.workforce
                if total_workforce <= 0:
                    continue
                else:
                    answer.value = None
                # Aggregate answers value/choice
                for child_answer in children_answers.filter(question=answer.question):
                    if answer.question.aggregate_mode == "avg" and (
                        child_answer.value or child_answer.choice
                    ):
                        if answer.value is None:
                            answer.value = 0
                        if child_answer.value:
                            answer.value += round(
                                (
                                    child_answer.evaluation.entity.workforce
                                    / total_workforce
                                )
                                * child_answer.value,
                                2,
                            )
                        elif child_answer.choice:
                            answer.value += (
                                child_answer.evaluation.entity.workforce
                                / total_workforce
                            ) * child_answer.choice.value
                    elif answer.question.aggregate_mode == "sum" and (
                        child_answer.value or child_answer.choice
                    ):
                        if answer.value is None:
                            answer.value = 0
                        answer.value += child_answer.value

                # For qcm will get the right choice that correspond to the aggregated value
                if "qcm" in child_answer.question.type and answer.value is not None:
                    subquery = (
                        answer.question.choices.filter(
                            question_id=OuterRef("question_id")
                        )
                        .annotate(distance=Abs(F("value") - answer.value))
                        .order_by("distance")
                        .values("id")[:1]
                    )

                    answer.choice = answer.question.choices.filter(
                        id=Subquery(subquery)
                    ).first()
                    answer.value = None
            answer.date_answered = timezone.now()

        Answer.objects.bulk_update(
            answers_to_aggregate, ["value", "choice", "date_answered"]
        )
        if answers_to_aggregate:
            compute_answers_rate(
                answers_to_aggregate[0].evaluation_id,
                answers_to_aggregate[0].question.category_id,
            )
        entity = entity.parent_entity


# class LastSearchMixin(TemplateResponseMixin):
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # FIXMe changed for last 3 evaluations
#         # context['last_evaluation_created'] = Evaluation.objects.filter(is_validated_by_admin=True).last()

#         last_evaluations_created = Evaluation.objects.filter(public_display=True)

#         if self.request.user.is_authenticated:
#             last_evaluations_created = last_evaluations_created.exclude(
#                 entity__members=self.request.user.pk
#             )
#         context["last_evaluations"] = filter_structure_evaluation(
#             last_evaluations_created.select_related(
#                 "entity__entity_level__structure__business_line",
#                 "sheet__type__questionary",
#             ).prefetch_related(
#                 "sheet__type",
#             )
#             .filter(is_validated_by_admin=True)
#             .order_by("-first_publication_date")
#         )[:12]
#         context["last_evaluation_created"] = last_evaluations_created.last()

#         # evaluations_created_by_user = Evaluation.objects.filter(
#         #    is_validated_by_user=True,
#         #    structure__owners__pk=self.request.user.pk
#         # )

#         if context.get("last_evaluation_created"):
#             context[
#                 "last_evaluation_created_on_users_region"
#             ] = last_evaluations_created.exclude(
#                 id=context["last_evaluation_created"].id
#             ).last()

#             # evaluations_created__on_users_region = Evaluation.objects.filter(
#             #    is_validated_by_admin=True,
#             #    is_validated_by_user=True,
#             #    structure__region=self.request.user.region
#             # )
#             # evaluations_created__on_users_region =
#             # context['last_evaluation_created_on_users_region'] = evaluations_created__on_users_region.last() or \
#             #     evaluations_created_by_user.last()

#             if context.get("last_evaluation_created_on_users_region"):
#                 context["last_evaluation_created_on_users_business_line"] = (
#                     last_evaluations_created.exclude(
#                         id=context["last_evaluation_created_on_users_region"].id
#                     )
#                     .exclude(id=context["last_evaluation_created"].id)
#                     .last()
#                 )

#         # evaluations_created_on_users_business_line = Evaluation.objects.filter(
#         #     is_validated_by_admin=True,
#         #     is_validated_by_user=True,
#         #     structure__business_line=self.request.user.business_line
#         # )
#         # context['last_evaluation_created_on_users_business_line'] = evaluations_created_on_users_business_line.last() \
#         #     or evaluations_created_by_user.last()
#         return context


# class StructureAutocomplete(autocomplete.Select2QuerySetView):
#     def get_queryset(self):
#         qs = Entity.objects.all().filter(evaluations__is_validated_by_admin=True)

#         if self.q:
#             qs = qs.filter(
#                 Q(commercial_name__icontains=self.q) | Q(juridic_name__icontains=self.q)
#             )
#         return qs


# class EvaluationSearchMixin(FormMixin):
#     # Add evaluation search info in context
#     form_class = EvaluationSearchForm

#     def get_initial(self):
#         initial = self.initial.copy()
#         initial["search"] = self.request.GET.get("search", "").strip()
#         return initial

#     def get_context_data(self, **kwargs):
#         context_data = super().get_context_data(**kwargs)
#         search = self.request.GET.get("search", "").strip()
#         if search:
#             context_data["evaluations"] = Evaluation.objects.filter(
#                 Q(entity__entity_level__structure__juridic_name__icontains=search)
#                 | Q(entity__entity_level__structure__commercial_name__icontains=search)
#                 | Q(entity__entity_level__structure__siret__icontains=search)
#                 | Q(entity__entity_level__structure__duns__icontains=search)
#                 | Q(entity__entity_level__structure__num_tva_intracom__icontains=search)
#             )
#             if not (
#                 self.request.user
#                 and self.request.user.is_authenticated
#                 and self.request.user.is_staff
#             ):
#                 evaluations = (
#                     context_data["evaluations"]
#                     .filter(public_display=True)
#                     .order_by("-first_publication_date")
#                 )
#                 context_data["evaluations"] = filter_structure_evaluation(evaluations)
#           return context_data


class AdvancedEvaluationFilter(FilterSet):
    structure = django_filters.ModelChoiceFilter(
        queryset=Structure.objects.all(),
        widget=autocomplete.ModelSelect2(url="structure-autocomplete"),
    )
    business_line = django_filters.ModelChoiceFilter(
        field_name="entity__entity_level__structure__business_line",
        queryset=BusinessLine.objects.all(),
        widget=Select2(),
    )
    category = django_filters.ChoiceFilter(
        field_name="entity__entity_level__structure__category",
        choices=CATEGORY_CHOICES,
        widget=Select2(),
    )

    def is_valid(self):
        is_valid = super().is_valid()
        if is_valid:
            nb_criteria = len([v for v in self.form.cleaned_data.values() if v])
            user_subscription_option = (
                self.request.user.active_subscription_option.product
            )
            if nb_criteria > user_subscription_option.search_criteria_number:
                self.errors[NON_FIELD_ERRORS] = _(
                    "Vous êtes limité à %(search_criteria_number)s critère(s) de recherche"
                ) % {
                    "search_criteria_number": user_subscription_option.search_criteria_number,
                }
                return False
        return is_valid


class EvaluationDiagExcelSheetDownload(LoginRequiredMixin, View):
    # IMPORTANT MIGRATION
    def post(self, request, *args, **kwargs):
        params = json.loads(request.body.decode("utf-8"))
        filter = params.get("filter", "classique")
        if filter != "classique" and filter != "to_review" and filter != "key_figures" and filter != "csrd":
            return JsonResponse(
                {
                    "code": "400",
                    "status": "error",
                    "message": _("Filter not found"),
                }
            )
        evaluation = get_object_or_404(Evaluation, pk=self.kwargs["pk"])
        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.test_func_rights(evaluation.entity)
        ):
            evaluation_id_list = [
                Entity.objects.get(pk=_pk).last_global_evaluation.id
                for _pk in params["pk_list"]
            ]
            export_excel_sheet_with_job.delay(
                evaluation.id,
                evaluation_id_list,
                request.user.email,
                params.get("language_code", "fr"),
                filter,
            )
            return JsonResponse(
                {
                    "code": "200",
                    "status": "success",
                    "message": _(
                        "Préparation d'export du récapitulatif, le résultat vous sera envoyé à l'adresse: %s"
                    )
                    % (request.user.email),
                }
            )
        return JsonResponse(
            {
                "code": "404",
                "status": "error",
                "message": _("Evaluation not found"),
            }
        )


class EvaluationPdfSheetView(LoginRequiredMixin, View):
    """
    Bouton « PDF » des résultats : renvoie le fichier stocké s'il existe encore,
    sinon le régénère (worker) et l'envoie par mail au lieu d'afficher un lien cassé.
    """

    def get(self, request, *args, **kwargs):
        evaluation = get_object_or_404(Evaluation, pk=self.kwargs["pk"])
        if not request.user.test_func_rights(evaluation.entity):
            return HttpResponseNotFound()
        language = self.kwargs["language_code"]
        pdf_sheet = getattr(evaluation, f"pdf_sheet_{language}", None)
        if pdf_sheet_available(pdf_sheet):
            return HttpResponseRedirect(pdf_sheet.url)

        regenerate_pdf_sheet_with_job.delay(
            evaluation.id,
            language,
            settings.PDF_RENDER_BASE_URL or request.build_absolute_uri("/"),
            request.session.session_key,
            request.user.email,
        )
        messages.success(
            request,
            _(
                "Préparation d'export du récapitulatif, le résultat vous sera envoyé à l'adresse: %s"
            )
            % request.user.email,
        )
        product = "human" if evaluation.is_human else "diag"
        return HttpResponseRedirect(
            reverse(
                "dashboard:dashboard_assess",
                args=(evaluation.entity.slug, product, evaluation.display_version_slugified),
            )
        )


class EvaluationSheetDownloadView(LoginRequiredMixin, View):
    # IMPORTANT MIGRATION
    def get(self, request, *args, **kwargs):
        evaluation = get_object_or_404(Evaluation, pk=self.kwargs["pk"])
        if self.request.user and self.request.user.is_authenticated:
            # Activating language manually in the job
            current_language = self.kwargs.get("language_code") or get_language()
            export_questions_sheet_with_job.delay(
                evaluation.id, request.user.email, current_language
            )
            messages.success(
                request,
                _(
                    _(
                        "Préparation d'export du récapitulatif, le résultat vous sera envoyé à l'adresse: %s"
                    )
                )
                % (request.user.email),
            )
            if evaluation.sheet.type.slug == "evaluation_collaborateurs_360":
                product = "human"
            else:
                product = "diag"
            return HttpResponseRedirect(
                reverse(
                    "dashboard:dashboard_assess",
                    args=(
                        evaluation.entity.slug,
                        product,
                        evaluation.display_version_slugified,
                    ),
                )
            )
        return HttpResponseNotFound()


class EvaluationFilteredSheetDownloadViewReact(LoginRequiredMixin, View):
    # IMPORTANT MIGRATION
    def post(self, request, *args, **kwargs):
        params = json.loads(request.body.decode("utf-8"))
        filter = params.get("filter", "classique")
        if filter != "classique" and filter != "to_review" and filter != "key_figures":
            return JsonResponse(
                {
                    "code": "400",
                    "status": "error",
                    "message": _("Filter not found"),
                }
            )
        evaluation = get_object_or_404(Evaluation, pk=self.kwargs["pk"])
        if (
            self.request.user
            and self.request.user.is_authenticated
        ):
            if params.get("filter", "classique") == "classique":
                export_questions_sheet_with_job.delay(
                    evaluation.id, request.user.email, params.get("language_code", "fr")
                )
            else:
                export_react_questions_filtered_sheet_with_job.delay(
                    evaluation.id,
                    request.user.email,
                    params.get("language_code", "fr"),
                    params.get("filter", "classique"),
                )
            return JsonResponse(
                {
                    "code": "200",
                    "status": "success",
                    "message": _(
                        "Préparation d'export du récapitulatif, le résultat vous sera envoyé à l'adresse: %s"
                    )
                    % (request.user.email),
                }
            )
        return JsonResponse(
            {
                "code": "404",
                "status": "error",
                "message": _("Evaluation not found"),
            }
        )
        # EvaluationFilteredPdfDownloadViewReact


def prepare_collaborator_filters(
    evaluation, converted_collab_filters, converted_collab_human_criteria, language_code
):
    activate(language_code)
    collab_filters = {"status": None} if not evaluation.is_campus else {}
    collab_human_criteria = {}
    selected_filters = {}

    # Selected filters
    for key, value in converted_collab_filters.items():
        selected_filters[key] = []
        collab_filters[key] = []
        if value:
            for v in value:
                selected_filters[key].append(v["label"])
                collab_filters[key].append(v["slug"])

    # Collaborator Filters and Human Criteria
    for key, value in converted_collab_human_criteria.items():
        values_queryset = HumanCriteriaChoice.objects.filter(id__in=value)
        key_trans = values_queryset.first().criteria.label
        selected_filters[key_trans] = []
        if value:
            for v in value:
                current_value = HumanCriteriaChoice.objects.filter(pk=v).first()
                selected_filters[key_trans].append(current_value.label)
            collab_human_criteria[key_trans] = values_queryset

    return {
        "collab_filters": collab_filters,
        "collab_human_criteria": collab_human_criteria,
        "selected_filters": selected_filters,
    }


def generate_collaborator_filters(evaluation, collab_filters, collab_human_criteria):
    queryset = evaluation.collaborators.all()
    if collab_filters:
        for key, value in collab_filters.items():
            if value:
                queryset = queryset.filter(**{f"{key}__in": value})
    if collab_human_criteria:
        for key, value in collab_human_criteria.items():
            if value:
                queryset = queryset.filter(**{f"human_criteria_choices__in": value})
    return queryset


@job("default")
def react_export_filtered_questions_sheet_with_job(
    evaluation_pk, paramslist, email, language_code
):
    evaluation = Evaluation.objects.get(pk=evaluation_pk)
    if evaluation:
        activate(language_code)
        # Getting back dictionaries from string to dict
        converted_paramslist = json.loads(paramslist)

        html_content = render_to_string(
            "mails/evaluation_questions_sheet_export.html",
            {"evaluation": evaluation, "with_filters": True},
        )

        collabs_queryset_list = []
        for elem in converted_paramslist:
            actual_filter = converted_paramslist[elem]
            # Sans critères personnalisés pour l'entreprise, le front n'envoie pas ces clés
            collab_filters = actual_filter.get("collab_filters", {})
            collab_human_criteria = actual_filter.get("collab_human_criteria", {})
            collab_inputs = prepare_collaborator_filters(
                evaluation,
                collab_filters,
                collab_human_criteria,
                language_code,
            )

            collabs_queryset_list.append(
                generate_collaborator_filters(
                    evaluation,
                    collab_inputs["collab_filters"],
                    collab_inputs["collab_human_criteria"],
                )
            )
        enoughcollaborator = True
        for collab_queryset in collabs_queryset_list:
            if collab_queryset.count() <= HUMAN_FILTER_LIMIT:
                enoughcollaborator = False
        if enoughcollaborator:
            filepath = evaluation.export_react_questions_sheet(
                paramslist=converted_paramslist, querysetlist=collabs_queryset_list
            )
            structure_name = evaluation.entity.name
            email_list = [email]
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Filtered_summary_{structure_name}_{stamp}.xlsx"
            with open(filepath, "rb") as file:
                subject = _("Votre récapitulatif avec filtres {} du : {}")
                send(
                    subject.format(structure_name, stamp),
                    email_list,
                    html_content,
                    [(filename, file, "application/ms-excel")],
                )

            # Removing the named temporary file once the mail is sent
            os.remove(filepath)
    else:
        logger.warning("Evaluation not found !")


@job("default")
def export_filtered_questions_sheet_with_job(
    evaluation_pk,
    collab_filters_string,
    human_criteria_string,
    email,
    language_code,
    second_param_activated,
    second_collab_filters_string,
    second_human_criteria_string,
):
    evaluation = Evaluation.objects.get(pk=evaluation_pk)

    if evaluation:
        activate(language_code)
        # Getting back dictionaries from string to dict
        converted_collab_filters = json.loads(collab_filters_string)
        converted_collab_human_criteria = json.loads(human_criteria_string)
        converted_second_collab_filters = json.loads(second_collab_filters_string)
        converted_second_collab_human_criteria = json.loads(
            second_human_criteria_string
        )
        converted_second_param_activated = json.loads(second_param_activated)

        html_content = render_to_string(
            "mails/evaluation_questions_sheet_export.html",
            {"evaluation": evaluation, "with_filters": True},
        )

        collab_inputs = prepare_collaborator_filters(
            evaluation,
            converted_collab_filters,
            converted_collab_human_criteria,
            language_code,
        )
        # Filtered collaborators
        collab_queryset = generate_collaborator_filters(
            evaluation,
            collab_inputs["collab_filters"],
            collab_inputs["collab_human_criteria"],
        )

        second_collab_inputs = prepare_collaborator_filters(
            evaluation,
            converted_second_collab_filters,
            converted_second_collab_human_criteria,
            language_code,
        )
        second_collab_queryset = generate_collaborator_filters(
            evaluation,
            second_collab_inputs["collab_filters"],
            second_collab_inputs["collab_human_criteria"],
        )

        # More the 10 collab only
        if converted_second_param_activated == "true":
            if (
                collab_queryset.count() > HUMAN_FILTER_LIMIT
                and second_collab_queryset.count() > HUMAN_FILTER_LIMIT
            ):
                filepath = evaluation.export_multiple_filtered_questions_sheet(
                    selected_filters=collab_inputs["selected_filters"],
                    second_selected_filters=second_collab_inputs["selected_filters"],
                    collab_queryset=collab_queryset,
                    second_collab_queryset=second_collab_queryset,
                )
                structure_name = evaluation.entity.name
                email_list = [email]
                stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Filtered_summary_{structure_name}_{stamp}.xlsx"
                with open(filepath, "rb") as file:
                    subject = _("Votre récapitulatif avec filtres {} du : {}")
                    send(
                        subject.format(structure_name, stamp),
                        email_list,
                        html_content,
                        [(filename, file, "application/ms-excel")],
                    )

                # Removing the named temporary file once the mail is sent
                os.remove(filepath)
        else:
            if collab_queryset.count() > HUMAN_FILTER_LIMIT:
                filepath = evaluation.export_filtered_questions_sheet(
                    selected_filters=collab_inputs["selected_filters"],
                    collab_queryset=collab_queryset,
                )
                structure_name = evaluation.entity.name
                email_list = [email]
                stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Filtered_summary_{structure_name}_{stamp}.xlsx"
                with open(filepath, "rb") as file:
                    subject = _("Votre récapitulatif avec filtres {} du : {}")
                    send(
                        subject.format(structure_name, stamp),
                        email_list,
                        html_content,
                        [(filename, file, "application/ms-excel")],
                    )

                # Removing the named temporary file once the mail is sent
                os.remove(filepath)
    else:
        logger.warning("Evaluation not found !")


class ExportFilteredExcelFileApiView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        params = json.loads(request.body.decode("utf-8"))
        json_result = "close"

        if (
            "collab_filters" in params
            and "collab_human_criteria" in params
            and "pk" in params
            and "language_code" in params
            and "second_filter_activated" in params
            and "second_collab_filters" in params
            and "second_collab_human_criteria" in params
        ):
            # Getting code language
            language_code = params["language_code"]
            # Getting back dictionaries from string to dict
            export_filtered_questions_sheet_with_job.delay(
                params["pk"],
                json.dumps(params["collab_filters"]),
                json.dumps(params["collab_human_criteria"]),
                request.user.email,
                language_code,
                json.dumps(params["second_filter_activated"]),
                json.dumps(params["second_collab_filters"]),
                json.dumps(params["second_collab_human_criteria"]),
            )
            evaluation = Evaluation.objects.get(pk=params["pk"])
            collab_inputs = prepare_collaborator_filters(
                evaluation,
                params["collab_filters"],
                params["collab_human_criteria"],
                language_code,
            )
            collabs_queryset = generate_collaborator_filters(
                evaluation,
                collab_inputs["collab_filters"],
                collab_inputs["collab_human_criteria"],
            )

            second_collab_inputs = prepare_collaborator_filters(
                evaluation,
                params["second_collab_filters"],
                params["second_collab_human_criteria"],
                language_code,
            )
            second_collabs_queryset = generate_collaborator_filters(
                evaluation,
                second_collab_inputs["collab_filters"],
                second_collab_inputs["collab_human_criteria"],
            )

            if (
                collabs_queryset.count() <= HUMAN_FILTER_LIMIT
                and second_collabs_queryset.count() <= HUMAN_FILTER_LIMIT
            ):
                json_result = "failure"
                messages.warning(
                    request,
                    _(
                        "Le nombre de répondants (f/h/nb) n'est pas assez important pour générer le fichier Excel avec les filtres !"
                    ),
                )
            else:
                return JsonResponse({"result": json_result})
        return JsonResponse({"result": json_result})


class ExportReactExcelFileApiView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        params = json.loads(request.body.decode("utf-8"))
        json_result = "close"

        if "pk" in params and "filterlist" in params and "language_code" in params:
            language_code = params["language_code"]
            react_export_filtered_questions_sheet_with_job(
                params["pk"],
                json.dumps(params["filterlist"]),
                request.user.email,
                language_code,
            )
            evaluation = Evaluation.objects.get(pk=params["pk"])
            index = 0
            for elem in params["filterlist"]:
                index += 1
                actual_filter = params["filterlist"][elem]
                collab_filters = actual_filter.get("collab_filters", {})
                collab_human_criteria = actual_filter.get("collab_human_criteria", {})
                collab_inputs = prepare_collaborator_filters(
                    evaluation,
                    collab_filters,
                    collab_human_criteria,
                    language_code,
                )
                collabs_queryset = generate_collaborator_filters(
                    evaluation,
                    collab_inputs["collab_filters"],
                    collab_inputs["collab_human_criteria"],
                )
                if collabs_queryset.count() <= HUMAN_FILTER_LIMIT:
                    json_result = "failure"
                    return JsonResponse(
                        {
                            "result": json_result,
                            "reason": "not_enough_collaborators",
                            "filter_index": index,
                        }
                    )
            return JsonResponse({"result": json_result})

        return JsonResponse({"result": json_result})


class EvaluationDownloadSynthesisPdf(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        evaluation = get_object_or_404(Evaluation, pk=self.kwargs["pk"])
        if not evaluation:
            return HttpResponse(
                _("Evaluation not found"),
                status=404,
            )
        if (
            self.request.user
            and self.request.user.is_authenticated
        ):
            if evaluation.is_diag:
                product_slug = "diag"
                product_name = "Diag"
            elif evaluation.is_human:
                product_slug = "human"
                product_name = "Human"
            else:
                return HttpResponse(
                    _("Bad product"),
                    status=404,
                )
            analysis = evaluation.get_general_analysis_clean_version()
            expert = analysis["expert"]
            content = evaluation.get_synthesis_template(
                analysis["general_analysis"],
                expert["first_name"],
                expert["last_name"],
                expert["title"],
                expert["photo"],
                expert["comment"],
                analysis["dimension_analysis"],
                analysis["key_recommendations"],
                analysis["best_practices"],
                product_slug,
                product_name,
                evaluation.get_footprint_url(),
                int(evaluation.get_global_score_delta)
            )
            done, result = asyncio.run(evaluation.generate_pdf_from_html_content(content))
            if done:
                response = FileResponse(open(result, 'rb'), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="Synthese_evaluation.pdf"'
                return response
            else:
                return HttpResponse(
                    _(result),
                    status=404,
                )
        else:
            return HttpResponse(
                _("Vous n'avez pas les permissions pour télécharger ce pdf"),
                status=405,
            )


class EvaluationSendSynthesisPdfMail(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        evaluation = get_object_or_404(Evaluation, pk=self.kwargs["pk"])
        if not evaluation:
            return HttpResponse(
                _("Evaluation not found"),
                status=404,
            )
        if (
            self.request.user
            and self.request.user.is_authenticated
        ):
            if evaluation.is_diag:
                product_slug = "diag"
                product_name = "Diag"
            elif evaluation.is_human:
                product_slug = "human"
                product_name = "Human"
            else:
                return HttpResponse(
                    _("Bad product"),
                    status=404,
                )

            html_content = render_to_string(
                "mails/evaluation_synthesis.html",
                {"entity": evaluation.entity},
            )
            analysis = evaluation.get_general_analysis_clean_version()
            expert = analysis["expert"]
            content = evaluation.get_synthesis_template(
                analysis["general_analysis"],
                expert["first_name"],
                expert["last_name"],
                expert["title"],
                expert["photo"],
                expert["comment"],
                analysis["dimension_analysis"],
                analysis["key_recommendations"],
                analysis["best_practices"],
                product_slug,
                product_name,
                evaluation.get_footprint_url(),
                int(evaluation.get_global_score_delta)
            )
            done, result = asyncio.run(evaluation.generate_pdf_from_html_content(content))
            if done:
                structure_name = evaluation.entity.name
                email_list = [request.user.email]
                stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Synthesis_{structure_name}_{stamp}.pdf"
                with open(result, "rb") as file:
                    subject = _("Votre récapitulatif {} du : {}")
                    send(
                        subject.format(structure_name, stamp),
                        email_list,
                        html_content,
                        [(filename, file, "application/pdf")],
                    )
                return HttpResponse(
                    _("La synthèse a bien été envoyée."),
                    status=200,
                )
            else:
                return HttpResponse(
                    _(result),
                    status=404,
                )
        else:
            return HttpResponse(
                _("Vous n'avez pas les permissions pour télécharger ce pdf"),
                status=405,
            )


class EvaluationFilteredPdfDownloadViewReact(LoginRequiredMixin, View):
    # IMPORTANT MIGRATION
    def post(self, request, *args, **kwargs):
        # try:
        params = json.loads(request.body.decode("utf-8"))
        # print the url of the requested
        webpackurl = "https://" + get_webpack_ip() + "/"
        evaluation = get_object_or_404(Evaluation, pk=self.kwargs["pk"])
        if not evaluation:
            return JsonResponse(
                {
                    "code": "404",
                    "status": "error",
                    "message": _("Evaluation not found"),
                }
            )
        if not params.get("cookies", None) and not params.get("filter", None):
            return JsonResponse(
                {
                    "code": "400",
                    "status": "error",
                    "message": _("Missing parameters"),
                }
            )
        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user
            in evaluation.entity.entity_level.structure.owners.all()
        ):
            parsedcookies = []
            for cookie in params.get("cookies", None):
                cookie = cookie.split("=")
                parsedcookies.append(
                    {
                        "name": cookie[0].replace(" ", ""),
                        "value": cookie[1].replace(" ", ""),
                        "url": webpackurl,
                    }
                )
            if evaluation.sheet.type.slug == "evaluation_collaborateurs_360":
                product = "human"
            else:
                product = "diag"
            export_pdf_with_job.delay(
                evaluation.id,
                product,
                request.user.email,
                params.get("language_code", "fr"),
                params.get(
                    "filter",
                    '{"default":{"age":[],"civility":[]},"human_criteria":[]}',
                ),
                parsedcookies,
                webpackurl,
            )
            return JsonResponse(
                {
                    "code": "200",
                    "status": "success",
                    "message": _(
                        "Préparation d'export du récapitulatif, le résultat vous sera envoyé à l'adresse: %s"
                    )
                    % (request.user.email),
                }
            )
        else:
            return JsonResponse(
                {
                    "code": "300",
                    "status": "error",
                    "message": _(
                        "vous n'avez pas les permissions pour exporter ce pdf"
                    ),
                }
            )
        # except Exception as e:
        #     return JsonResponse(
        #         {
        #             "code": "500",
        #             "status": "error",
        #             "message": _("une erreur interne est survnue"),
        #         }
        #     )


class ExportAnswersFromQuestionView(LoginRequiredMixin, View):
    # is it the diag function to export the sheet diagsheet,
    def get(self, request, *args, **kwargs):
        answers = Answer.objects.filter(
            evaluation=self.kwargs["evaluation"], question=self.kwargs["question"]
        )
        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_staff
        ):
            from openpyxl import Workbook
            from openpyxl.styles import Alignment

            wb = Workbook()

            # grab the active worksheet
            ws = wb.active
            ws.page_setup.fitToHeight = 1
            ws.page_setup.fitToWidth = 1

            ws.column_dimensions["A"].width = 50
            ws.column_dimensions["B"].width = 50
            ws.column_dimensions["C"].width = 50
            ws.column_dimensions["D"].width = 150

            wsindex = 1
            ws[f"A1"] = answers[0].question.google_sheets_id
            ws[f"B1"] = answers[0].question.label
            wsindex += 1
            ws[f"A2"] = "value"
            ws[f"B2"] = "text_value"
            ws[f"C2"] = "choice"
            ws[f"D2"] = "subanswers"
            wsindex += 1

            for answer in answers:
                ws[f"A{wsindex}"] = answer.value
                ws[f"B{wsindex}"] = answer.text_value
                ws[f"C{wsindex}"] = answer.choice and answer.choice.label
                subanswer_text = ""
                for subanswer in answer.subanswers.all():
                    subanswer_text += (
                        subanswer.subquestion.label
                        + " : "
                        + (
                            (subanswer.value and str(subanswer.value))
                            or str(subanswer.choice and subanswer.choice.label)
                        )
                        + "\n"
                    )
                ws[f"D{wsindex}"] = subanswer_text
                ws[f"D{wsindex}"].alignment = Alignment(wrap_text=True)
                wsindex += 1

            # Save the file
            with io.BytesIO() as tmp:
                wb.save(tmp)
                tmp.seek(0)
                content = tmp.read()
            response = HttpResponse(content)
            response["Content-Type"] = "application/vnd.ms-excel"
            response["Content-Disposition"] = (
                "attachment; filename="
                + slugify(
                    "reponses_"
                    + (answers[0].evaluation.entity.name)
                    + "_"
                    + str(answers[0].question.google_sheets_id)
                    + "_"
                    + str(answers[0].evaluation.sheet.year)
                )
                + ".xlsx"
            )
            return response
        return HttpResponseNotFound()


# A modifier si utile (pas de tag sur les subscription_option)


class EvaluationPublishView(
    LoginRequiredMixin,
    RedirectView,
):
    def __init__(self):
        super(EvaluationPublishView, self).__init__()
        self._evaluation = None

    def get_object(self):
        self._evaluation = get_object_or_404(
            Evaluation.objects.select_related(
                "sheet__type",
                "entity__entity_level__structure",
            ),
            pk=self.kwargs["pk"],
        )
        return self._evaluation

    def get_redirect_url(self, *args, **kwargs):
        evaluation = self.get_object()
        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.test_func_rights(evaluation.entity)
        ):
            evaluation.public_display = not evaluation.public_display
            if not evaluation.first_publication_date:
                evaluation.first_publication_date = timezone.now()
                alert_evaluation_published_mail(
                    self.request, evaluation
                )  # TODO : add to job server
            evaluation.save()
            messages.success(self.request, "Votre évaluation a bien été mise à jour")
            if evaluation.sheet.type.slug == "evaluation_collaborateurs_360":
                product = "human"
            elif evaluation.is_scan:
                product = "scan"
            else:
                product = "diag"
        return reverse(
            "dashboard:dashboard_assess_test",
            args=(
                evaluation.entity.slug,
                product,
                evaluation.display_version_slugified,
            ),
        )


class EvaluationCreation(LoginRequiredMixin, CanEvaluateMixin, FormView):
    # Vue pour la création d'une nouvelle évaluation.

    form_class = EvaluationCreationForm
    template_name = "scoring/evaluation_create.html"

    def __init__(self):
        super(EvaluationCreation, self).__init__()
        self._subscription_option = None
        self._evaluations = None

    def dispatch(self, request, *args, **kwargs):
        self.get_subscription_option()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.get_subscription_option()
        structure = self._subscription_option.subscriptionPack.structure
        entities = Entity.objects.filter(entity_level__structure=structure)
        sheet = QuestionSheet.get_new_evaluation_question_sheet(
            self._subscription_option
        )

        display_aims_category = False
        if self._subscription_option.product.slug == "mixity_start":
            display_aims_category = True

        booleans_tags = []
        tags = []
        for key in structure.booleans:
            if structure.booleans[key]:
                tag, _ = QuestionTag.objects.get_or_create(name=key)
                booleans_tags.append(tag)

        evaluations_to_create = []
        for entity in entities:
            evaluations_to_create.append(
                Evaluation(
                    name="Évaluation pour l'année 2023",
                    entity=entity,
                    _option=self._subscription_option,
                    sheet=QuestionSheet.get_new_evaluation_question_sheet(
                        self._subscription_option
                    ),
                    display_aims_category=display_aims_category,
                )
            )

        self._evaluations = Evaluation.objects.bulk_create(evaluations_to_create)

        for evaluation in self._evaluations:
            tags = booleans_tags
            if evaluation.entity.address:
                tag, _ = QuestionTag.objects.get_or_create(
                    name=slugify(structure.address.locality.state.country.code)
                )
                tags.append(tag)
            tags += list(evaluation.entity.tags.all())
            # tags += list(self._subscription.tags.all())
            evaluation.tags.set(tags)
            evaluation.generate_answers()
        return super().form_valid(form)

    def get_success_url(self):
        first_question = self._evaluations[0].next_question
        first_category = first_question.category
        kwargs = {
            "pk": self._evaluations[0].pk,
            "category": first_category.slug,
            "subcategory": self._evaluations[0].first_subcategory_slug,
            "page": 0,
        }
        if first_question.target:
            kwargs["target"] = first_question.target
        return reverse("evaluation_fill", kwargs=kwargs)

    def get_subscription_option(self):
        if not self._subscription_option:
            self._subscription_option = SubscriptionOption.objects.select_related(
                "subscriptionPack__structure__address__locality__state__country",
            ).get(pk=self.kwargs["pk"])
        return self._subscription_option

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subscription"] = self.get_subscription_option()
        context["structure"] = context["subscription"].subscriptionPack.structure
        context["sheet"] = QuestionSheet.get_new_evaluation_question_sheet(
            context["subscription"]
        )
        context["categories"] = Category.objects.filter(slug__in=MAIN_CATEGORIES_SLUGS)
        context["no_header"] = True
        context["no_footer"] = True
        return context


class NextActionMixin:
    def get_next_action(self, context):
        subcategory = context.get("subcategory")
        category = context.get("category")
        evaluation = context.get("evaluation")
        target = context.get("target_name", "collaborator")
        if subcategory is not None and subcategory.slug != settings.KEY_FIGURES_SLUG:
            same_category, next_action = subcategory.get_next_from_evaluation(
                evaluation, category, target
            )
            if next_action and same_category:
                action = _("Continuer vers {next_action}").format(
                    next_action=next_action
                )
            elif evaluation.sheet.type.slug == "mixity_start":
                if not next_action:
                    action = _("Passer à la validation")
                elif next_action.category.has_key_figures(evaluation):
                    action = _("Continuer vers {next_action} / Chiffres-clefs").format(
                        next_action=next_action
                    )
                else:
                    cat = category.get_next_from_evaluation(evaluation, target)
                    action = _("Continuer vers {category} / {subcategory}").format(
                        category=cat,
                        subcategory=next_action,
                    )
            else:
                action = _("Continuer vers {category} / Champ libre").format(
                    category=category
                )
        elif subcategory is not None and subcategory.slug == settings.KEY_FIGURES_SLUG:
            action = _("Continuer vers {subcategory}").format(
                subcategory=category.first_subcategory_from_evaluation(
                    evaluation, target
                )
            )
        else:
            next_action = category.get_next_from_evaluation(evaluation, target)
            if next_action:
                if next_action.has_key_figures(evaluation):
                    action = _("Continuer vers {next_action} / Chiffres-clefs").format(
                        next_action=next_action
                    )
                else:
                    action = _("Continuer vers {subcategory}").format(
                        subcategory=category.get_next_from_evaluation(
                            evaluation, target
                        ).first_subcategory_from_evaluation(evaluation, target)
                    )
            else:
                questions_targets = evaluation.targets
                if target != questions_targets[-1]:
                    next_action = evaluation.next_target_question(questions_targets[-1])
                    if not next_action:
                        action = _("Passer à la validation")
                    else:
                        action = _(
                            "Continuer vers {target} / {category} / Chiffres-clefs"
                        ).format(
                            target=next_action.target,
                            category=next_action.category,
                        )
                else:
                    action = _("Passer à la validation")
        return action


class EvaluationEditorMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Réserve une action sur une évaluation (valider, rouvrir, téléverser un visuel)
    aux membres non lecteurs de l'entreprise concernée, et à l'équipe Mixity (staff).
    """

    def test_func(self):
        user = self.request.user
        if user.is_staff:
            return True
        evaluation = get_object_or_404(
            Evaluation.objects.select_related("entity__entity_level__structure"),
            pk=self.kwargs["pk"],
        )
        if evaluation.entity is None or not user.test_func_rights(evaluation.entity):
            return False
        membership = user.get_rights(evaluation.entity)
        return not (membership and membership.is_reader)


class EvaluationValidate(EvaluationEditorMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        evaluation = get_object_or_404(Evaluation, pk=kwargs["pk"])
        if not evaluation.is_validated_by_admin:
            evaluation.do_user_validation()
            if evaluation.sheet.type.slug == "evaluation_collaborateurs_360":
                product = "human"
            else:
                product = "diag"
            return reverse(
                "dashboard:dashboard_assess",
                args=(
                    evaluation.entity.slug,
                    product,
                    evaluation.display_version_slugified,
                ),
            )


class EvaluationOpen(EvaluationEditorMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        evaluation = get_object_or_404(Evaluation, pk=kwargs["pk"])
        if not evaluation.is_validated_by_admin:
            evaluation.is_validated_by_user = False
            evaluation.save()
            if evaluation.sheet.type.slug == "evaluation_collaborateurs_360":
                product = "human"
            else:
                product = "diag"
            return reverse(
                "dashboard:dashboard_assess",
                args=(
                    evaluation.entity.slug,
                    product,
                    evaluation.display_version_slugified,
                ),
            )


@job("default")
def compute_answers_rate(evaluation_id, category_id):
    evaluation = Evaluation.objects.get(id=evaluation_id)
    evaluation.answers_rate_cache = None
    evaluation.answers_rate_cache = evaluation.answers_rate
    sc = ScoreCategory.objects.get(evaluation_id=evaluation_id, category=category_id)
    sc.key_figures_filled = None
    sc.category_answers_rate_cache = None
    sc.category_answers_rate_cache = sc.category_answers_rate


class EvaluationFill(LoginRequiredMixin, CanEvaluateMixin, FormView, NextActionMixin):
    """
    Vue permettant de saisir les réponses.
    """

    form_class = EvaluationFillForm
    template_name = "scoring/evaluation_fill.html"

    def __init__(self):
        super(EvaluationFill, self).__init__()
        self._evaluation = None
        self._previous_choices = None
        self._questions = None
        self._total = None
        self._scores_categories = None
        self._category = None
        self._subcategory = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs().copy()
        kwargs["subcategory"] = self.get_subcategory()
        kwargs["target"] = self.target
        kwargs["category"] = self.get_category()
        kwargs["evaluation"] = self.get_evaluation()
        kwargs["page"] = self.get_page()
        kwargs["questions"] = self.get_questions()
        return kwargs

    def get_category(self):
        if not self._category:
            self._category = get_object_or_404(Category, slug=self.kwargs["category"])
        return self._category

    def get_scores_categories(self):
        if not self._scores_categories:
            self._scores_categories = (
                self.get_evaluation().scores_categories.select_related("category").all()
            )
        return self._scores_categories

    def get_subcategory(self):
        if not self._subcategory:
            if self.kwargs["subcategory"] != settings.KEY_FIGURES_SLUG:
                self._subcategory = get_object_or_404(
                    SubCategory,
                    slug=self.kwargs["subcategory"],
                    categories=self.get_category(),
                )
            else:
                self._subcategory = SubCategory(
                    name=settings.KEY_FIGURES_LABEL,
                    slug=settings.KEY_FIGURES_SLUG,
                )
        return self._subcategory

    def get_evaluation(self):
        if not self._evaluation:
            self._evaluation = get_object_or_404(
                Evaluation.objects.select_related(
                    "entity__entity_level__structure",
                    "entity__parent_entity",
                    "sheet",
                    "sheet__type",
                ).prefetch_related("tags"),
                pk=self.kwargs["pk"],
            )
        return self._evaluation

    def get_subscription_option(self):
        evaluation = self.get_evaluation()
        subscription_pack = (
            SubscriptionPack.objects.filter(
                structure=evaluation.entity.entity_level.structure
            )
            .order_by("-start_date")
            .first()
        )
        if evaluation.sheet.type.slug == "evaluation_collaborateurs_360":
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

    def get_page(self):
        return self.kwargs["page"]

    @property
    def target(self):
        return self.kwargs.get("target", "collaborator")

    def get_next_action(self, context):
        action = super().get_next_action(context)
        if not self.is_last_page():
            return _("Continuer vers {subcategory}").format(
                subcategory=self.get_subcategory()
            )
        return action

    def request_questions(self):
        questions = self.get_evaluation().get_questions_from_answers.filter(
            answers__evaluation=self.get_evaluation(),
            display=True,
        )
        if self.target:
            questions = questions.filter(target=self.target)
        if self.get_subcategory().slug == settings.KEY_FIGURES_SLUG:
            return questions.filter(
                order_stat_subcategory__gte=1,
                category=self.get_category(),
            ).order_by("order_stat_subcategory", "google_sheets_id")
        else:
            return questions.filter(
                order_stat_subcategory=None,
                subcategory=self.get_subcategory(),
                category=self.get_category(),
            )

    def get_questions(self):
        if self._questions is None:
            questions = self.request_questions()
            number_of_questions = float(questions.count())
            self._total = number_of_questions
            number_of_pages = math.ceil(
                number_of_questions / float(settings.QUESTIONS_PER_PAGE_LIMIT)
            )
            if number_of_pages > 0:
                questions_per_page = math.ceil(number_of_questions / number_of_pages)
                offset = questions_per_page * self.get_page()
                questions = questions[offset : offset + questions_per_page]
            self._questions = list(questions)
        return self._questions

    @staticmethod
    def set_trial_cat(evaluation, context):
        tags = [t.name for t in evaluation.tags.all()]
        if evaluation.sheet.type == "evaluation_collaborateurs_360":
            product = "human"
        else:
            product = "diag"
        subscription_option = (
            SubscriptionOption.objects.filter(
                subscriptionPack__structure=evaluation.entity.entity_level.structure,
                product__slug=product,
            )
            .order_by("-start_date")
            .first()
        )
        if subscription_option.is_trial:
            trial_cats = [
                _("Genre"),
                _("Handicap"),
                _("Origines"),
                _("Générations"),
                _("LGBTQIA+"),
            ]
            if "no_disability" in tags:
                trial_cats.remove(_("Genre"))
            else:
                trial_cats.remove(_("Handicap"))
            context["trial_cats"] = trial_cats
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs).copy()
        # context for don't display header and footer on questionnary
        context["no_header"] = True
        context["no_footer"] = True

        # TODO: renommer en "current_category"
        context["category"] = self.get_category()
        # TODO: renommer en "current_target"
        context["target_name"] = self.target
        # TODO: renommer en "current_subcategory"
        context["subcategory"] = self.get_subcategory()
        context["evaluation"] = self.get_evaluation()
        context["score_category"] = self.get_scores_categories().get(
            category=context["category"]
        )
        context = self.set_trial_cat(self.get_evaluation(), context)
        context["scores_categories"] = self.get_scores_categories()
        context["next_action"] = self.get_next_action(context)
        return context

    def is_last_page(self):
        return self.get_page() + 1 >= (self._total / settings.QUESTIONS_PER_PAGE_LIMIT)

    def get_initial(self):
        """Préremplit le formulaire avec les choix existants éventuels"""
        initial = self.initial.copy()
        for question_id, answer in self.previous_choices.items():
            tmp_subanswers = list(answer.subanswers.all())
            if len(tmp_subanswers) > 0:
                for sa in tmp_subanswers:
                    if "multiple_qcm" not in sa.subquestion.ui_type or sa.value == 1.0:
                        initial[
                            f"question_{str(question_id)}_sub_{str(sa.subquestion_id)}"
                        ] = sa.value
            else:
                initial[f"question_{str(question_id)}"] = (
                    datetime.datetime.fromtimestamp(answer.value).strftime("%Y-%m-%d")
                    if answer.value is not None and "date" in answer.question.type
                    else (
                        answer.choice
                        if answer.choice is not None and answer.value is not None
                        else answer.value if answer.value is not None else answer.text_value
                    )
                )
                if answer.currency_symbol:
                    initial[f"question_{str(question_id)}_currency"] = (
                        answer.currency_symbol
                    )
            initial[f"question_{str(question_id)}_detail"] = answer.text_value
            initial[f"question_{str(question_id)}_blocked_aggregation"] = (
                answer.blocked_aggregation
            )
            if answer.question.display_not_applicable:
                initial[f"question_{str(question_id)}_not_applicable"] = (
                    answer.is_not_applicable
                )
            if answer.question.is_indicator:
                initial[f"question_{str(question_id)}_indicator_not_followed"] = (
                    answer.is_not_followed
                )
            if answer.question.display_custom_question_label:
                initial[f"question_{str(question_id)}_custom_question_label"] = (
                    answer.custom_question_label
                )
        # XXX FIXME only for one special question is it worth ?
        initial["questionnaire_labels"] = (
            self.get_evaluation().entity.entity_level.structure.labels.all()
        )
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        data = form.cleaned_data
        evaluation = self.evaluation

        # les réponses qui existaient déjà sur cette évaluation
        existing_answers = self.previous_choices

        # Sous réponses modifiées nécéssitant un calcul du score
        subanswers_percentage_sum_check = {}
        questions_ids = []
        for field_id, value in data.items():
            # XXXX tricky exception for labels question
            if field_id == "questionnaire_labels":
                evaluation.entity.entity_level.structure.labels.set(value)
                evaluation.entity.entity_level.structure.save()
                continue

            id_elements = field_id.split("_")
            question_id = int(id_elements[1])
            questions_ids.append(question_id)
            if question_id not in existing_answers:
                continue
            answer = existing_answers.get(question_id)
            q = answer.question
            if field_id.endswith("_blocked_aggregation"):
                answer.blocked_aggregation = value
            if field_id.endswith("_custom_question_label"):
                if answer.question.display_custom_question_label:
                    answer.custom_question_label = value
            elif field_id.endswith("_not_applicable"):
                if answer.question.display_not_applicable:
                    answer.is_not_applicable = value
                    if value:
                        answer.date_answered = timezone.now()
            elif field_id.endswith("_indicator_not_followed"):
                if answer.question.is_indicator:
                    answer.is_not_followed = value
                    if value:
                        answer.date_answered = timezone.now()
            elif len(id_elements) == 3 and id_elements[2] == "currency":
                answer.currency_symbol = value
            elif len(id_elements) == 3 and id_elements[2] == "detail":
                if question_id in existing_answers:
                    if (
                        "subquestions" in q.type
                    ):  # Important si utilisateur écrit un détail sans répondre
                        answer.text_value = value
                    else:
                        answer.text_value = value
                elif (
                    f"question_{str(question_id)}" in data
                    and data[f"question_{str(question_id)}"] is not None
                ) or "subquestions" in q.type:
                    answer.text_value = value
                    answer.comment = Comment.objects.filter(
                        question_id=question_id
                    ).first()
                    answer.date_answered = timezone.now()

            elif len(id_elements) == 4 and id_elements[2] == "sub":
                answer.date_answered = timezone.now()

                subquestion_id = int(id_elements[3])
                sub_answer, created = SubAnswer.objects.select_related(
                    "answer__evaluation__entity__entity_level__structure__business_line"
                ).update_or_create(
                    subquestion_id=subquestion_id,
                    answer_id=answer.id,
                    defaults={"value": value},
                )
                if created:
                    answer.date_answered = timezone.now()
                ui_type = answer.question.subquestions.get(id=subquestion_id).ui_type
                if "pourcentage" in ui_type and not "novalidator" in ui_type:
                    if not answer in subanswers_percentage_sum_check:
                        subanswers_percentage_sum_check[answer] = 0
                    if value:
                        subanswers_percentage_sum_check[answer] += value

            elif not answer.is_not_applicable and not answer.is_not_followed:
                if "libre" in q.type or "text" in q.type:
                    if value:
                        answer.text_value = value
                        answer.date_answered = timezone.now()
                    else:
                        answer.text_value = None
                        answer.date_answered = None
                    answer.date_modified = timezone.now()
                    continue
                else:
                    text_value = None

                if isinstance(value, datetime.date):
                    # for now, date questions are not rated so we only store the value and skip everything else
                    answer.value = mktime(value.timetuple())
                    continue
                if q.choices.exists():
                    if isinstance(value, Choice):
                        if answer.choice != value:
                            answer.choice = value
                            answer.date_answered = timezone.now()
                    elif value is not None:
                        if value != answer.value:
                            answer.value = value
                            answer.date_answered = timezone.now()
                    else:
                        answer.value = None
                        if "qcm" in answer.question.type:
                            answer.choice = None
                        answer.date_answered = None

                else:
                    if value is not None or text_value is not None:
                        # comment is activated by default
                        answer.text_value = text_value
                        answer.value = value
                        answer.date_answered = timezone.now()
                        answer.comment = Comment.objects.filter(
                            question_id=question_id
                        ).first()
                    else:
                        answer.value = None
                        answer.date_answered = None

        # test percentage answers
        for answer, value in subanswers_percentage_sum_check.items():
            if value != 100:
                answer.subanswers.all().delete()

        for answer in existing_answers.values():
            answer.save()

        if (
            evaluation.entity.parent_entity
            and evaluation.sheet.slug == "mixity_evaluation_diag"
        ):
            # Will agreggate theses answers for its parent
            subscription_option = SubscriptionOption.active_objects.filter(
                product__slug="diag",
                subscriptionPack__structure=evaluation.entity.entity_level.structure,
            ).first()
            aggregate_answers(
                evaluation.entity.parent_entity.id,
                subscription_option,
                list(set(questions_ids)),
            )

        evaluation.modified_by_user_date = timezone.now()
        category = self.get_category()
        compute_answers_rate.delay(evaluation.id, category.id)
        evaluation.save()
        return response

    def get_success_url(self):
        if self.request.method != "POST":
            # TODO: we should never get here ?
            return
        if self.request.POST.get("save_leave"):
            return reverse("evaluation_confirm", kwargs={"pk": self.kwargs["pk"]})
        if not self.request.POST.get("save_next"):
            # TODO: we should never get here ?
            return
        category = self.get_category()
        subcategory = self.get_subcategory()
        target = self.target
        page = 0
        if not self.is_last_page():
            next_subcategory = subcategory
            page = self.get_page() + 1
        elif subcategory.slug != settings.KEY_FIGURES_SLUG:
            same_category, next_subcategory = subcategory.get_next_from_evaluation(
                self.get_evaluation(), category, target
            )
        else:
            next_subcategory = category.first_subcategory_from_evaluation(
                self.get_evaluation(), target
            )
        if self.evaluation.sheet.type.slug == "mixity_start" and not next_subcategory:
            return reverse("evaluation_confirm", kwargs={"pk": self.evaluation.pk})
        if not next_subcategory:
            kwargs = {
                "pk": self.evaluation.scores_categories.get(category=category).pk,
                "category": category.slug,
            }
            return reverse("evaluation_category_confirm", kwargs=kwargs)

        kwargs = {
            "pk": self.kwargs["pk"],
            "category": category.slug,
            "page": page,
        }
        if target:
            kwargs["target"] = target
        is_mixity_start = self.evaluation.sheet.type.slug == "mixity_start"
        has_key_figures = category.has_key_figures(self.evaluation)
        if (is_mixity_start and not has_key_figures) or (
            next_subcategory and category == category
        ):
            kwargs["subcategory"] = next_subcategory.slug
            return reverse("evaluation_fill", kwargs=kwargs)
        elif is_mixity_start and has_key_figures:
            kwargs["subcategory"] = settings.KEY_FIGURES_SLUG
            return reverse("evaluation_fill", kwargs=kwargs)
        else:
            kwargs["pk"] = self.evaluation.scores_categories.get(category=category).pk
            kwargs["category"] = category.slug
            del kwargs["page"]
            return reverse("evaluation_category_confirm", kwargs=kwargs)

    @property
    def evaluation(self):
        if self._evaluation is None:
            self._evaluation = (
                Evaluation.objects.select_related("sheet", "sheet__type")
                .prefetch_related("score_categories")
                .get(pk=self.kwargs["pk"])
            )
        return self._evaluation

    @property
    def previous_choices(self):
        """
        :return: mapping {question_id: choice}
        """
        if self._previous_choices is None:
            answers_qs = (
                self.evaluation.answers.filter(question__in=self.get_questions())
                .select_related("choice", "question__category", "question__subcategory")
                .prefetch_related("subanswers__subquestion")
            )
            self._previous_choices = {a.question_id: a for a in answers_qs}
        return self._previous_choices


class EvaluationCategoryConfirm(
    LoginRequiredMixin, CanEvaluateMixin, UpdateView, NextActionMixin
):
    template_name = "scoring/evaluation_category_confirm.html"
    form_class = EvaluationCategoryConfirmForm
    model = ScoreCategory
    _action_element = None

    def form_invalid(self, form):
        response = super().form_invalid(form)
        return response

    def __init__(self):
        super(EvaluationCategoryConfirm, self).__init__()
        self._score_category = None
        self._scores_categories = None

    def form_valid(self, form):
        response = super().form_valid(form)
        data = form.cleaned_data
        removed_detail_intules = list(range(0, settings.DEFAULT_ACTION_ROW_NUMBER))
        removed_detail_descriptif = list(range(0, settings.DEFAULT_ACTION_ROW_NUMBER))
        removed_aim_descriptif = list(range(0, settings.DEFAULT_ACTION_ROW_NUMBER))
        removed_aim_intitules = list(range(0, settings.DEFAULT_ACTION_ROW_NUMBER))
        for field_id, value in data.items():
            id_elements = field_id.split("_")
            scorecategory = self.get_object()
            action, _ = Action.objects.get_or_create(scorecategory=scorecategory)
            if (value is None or 0 < len(value) <= 700) and id_elements[1] != "label":
                id_array = int(id_elements[2])
                if id_elements[1] == "detail" and 0 <= id_array <= 4:
                    if id_elements[0] == "intitules":
                        action.intitules_detail[id_array] = value
                        removed_detail_intules.remove(id_array)
                    else:
                        action.descriptif_detail[id_array] = value
                        removed_detail_descriptif.remove(id_array)
                elif id_elements[1] == "aim" and 0 <= id_array <= 4:
                    if id_elements[0] == "intitules":
                        action.intitules_aim[id_array] = value
                        removed_aim_intitules.remove(id_array)
                    else:
                        action.descriptif_aim[id_array] = value
                        removed_aim_descriptif.remove(id_array)

            for i in removed_detail_descriptif:
                action.descriptif_detail[i] = None
            for i in removed_detail_intules:
                action.intitules_detail[i] = None
            for i in removed_aim_intitules:
                action.intitules_aim[i] = None
            for i in removed_aim_descriptif:
                action.descriptif_aim[i] = None
            action.save()
        return response

    def get_initial(self):
        """Préremplit le formulaire avec les choix existants éventuels"""
        initial = self.initial.copy()
        if self.action_element is not None:
            for i in range(0, settings.DEFAULT_ACTION_ROW_NUMBER):
                if len(self.action_element.intitules_detail) > i:
                    initial["intitules_detail_" + str(i)] = (
                        self.action_element.intitules_detail[i]
                    )
                if len(self.action_element.descriptif_detail) > i:
                    initial["descriptif_detail_" + str(i)] = (
                        self.action_element.descriptif_detail[i]
                    )
                if len(self.action_element.intitules_aim) > i:
                    initial["intitules_aim_" + str(i)] = (
                        self.action_element.intitules_aim[i]
                    )
                if len(self.action_element.descriptif_aim) > i:
                    initial["descriptif_aim_" + str(i)] = (
                        self.action_element.descriptif_aim[i]
                    )
        return initial

    def get_object(self, **kwargs):
        if not self._score_category:
            self._score_category = get_object_or_404(
                ScoreCategory, pk=self.kwargs["pk"]
            )
        return self._score_category

    def get_subscription_option(self):
        evaluation = self.get_object().evaluation
        subscription_pack = (
            SubscriptionPack.objects.filter(
                structure=evaluation.entity.entity_level.structure
            )
            .order_by("-start_date")
            .first()
        )
        if evaluation.sheet.type.slug == "evaluation_collaborateurs_360":
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

    @property
    def action_element(self):
        """
        :return: mapping {question_id: choice}
        """
        if self._action_element is None:
            self._action_element = (
                Action.objects.all()
                .filter(scorecategory_id=self.get_object().id)
                .first()
            )
        return self._action_element

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs().copy()
        kwargs["category"] = self.get_category()
        return kwargs

    def get_category(self):
        return get_object_or_404(Category, slug=self.kwargs["category"])

    @property
    def target(self):
        return self.kwargs.get("target", "collaborator")

    def get_structure(self):
        return self.get_object().evaluation.entity.entity_level.structure

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs).copy()
        # context for don't display header and footer on questionnary
        context["no_header"] = True
        context["no_footer"] = True

        context["score_category"] = self.get_object()
        context["evaluation"] = context["score_category"].evaluation
        context["category"] = self.get_category()
        context["target_name"] = self.target
        context["next_action"] = self.get_next_action(context)
        context["scores_categories"] = self.get_scores_categories()
        return context

    def get_scores_categories(self):
        if not self._scores_categories:
            self._scores_categories = (
                self.get_object()
                .evaluation.scores_categories.select_related("category")
                .all()
            )
        return self._scores_categories

    def get_success_url(self):
        if self.request.method != "POST":
            # TODO: we should never get here ?
            return
        if self.request.POST.get("save_leave"):
            return reverse(
                "evaluation_confirm", kwargs={"pk": self.object.evaluation.pk}
            )
        if not self.request.POST.get("save_next"):
            # TODO: we should never get here ?
            return
        category = self.get_category()
        next_category = category.get_next_from_evaluation(
            self.object.evaluation, self.target
        )
        if next_category:
            if next_category.has_key_figures(self.object.evaluation):
                next_subcategory = settings.KEY_FIGURES_SLUG
            else:
                next_subcategory = (
                    category.get_next_from_evaluation(
                        self.object.evaluation, self.target
                    )
                    .first_subcategory_from_evaluation(
                        self.object.evaluation, self.target
                    )
                    .slug
                )
            kwargs = {
                "pk": self.object.evaluation.pk,
                "category": next_category.slug,
                "subcategory": next_subcategory,
                "target": self.target,
                "page": 0,
            }
            return reverse("evaluation_fill", kwargs=kwargs)
        else:
            questions_targets = self.object.evaluation.targets
            if self.target != questions_targets[-1]:
                question = self.object.evaluation.next_target_question(
                    questions_targets[-1]
                )
                if not question:
                    return reverse(
                        "evaluation_confirm",
                        kwargs={"pk": self.object.evaluation.pk},
                    )
                kwargs = {
                    "pk": self.object.evaluation.pk,
                    "category": question.category.slug,
                    "subcategory": settings.KEY_FIGURES_SLUG,
                    "target": question.target,
                    "page": 0,
                }
                return reverse("evaluation_fill", kwargs=kwargs)
            else:
                return reverse(
                    "evaluation_confirm",
                    kwargs={"pk": self.object.evaluation.pk},
                )


class EvaluationFootprintUpload(EvaluationEditorMixin, UpdateView):
    model = Evaluation
    fields = [
        "footprint",
    ]

    def get_success_url(self):
        return reverse("evaluation_confirm", kwargs={"pk": self.get_object().pk})

    def form_valid(self, form):
        ft, imgstr = self.request.POST["footprint"].split(";base64,")
        data = ContentFile(
            base64.b64decode(imgstr + "=="), name="footprint." + ft.split("/")[-1]
        )
        evaluation = self.get_object()
        evaluation.footprint = data
        evaluation.save()
        evaluation.export_answer_sheet()
        return JsonResponse({"image": "created"})


class EvaluationPDFUpload(EvaluationEditorMixin, UpdateView):
    model = Evaluation
    fields = [
        "footprint",
    ]

    def get_success_url(self):
        return reverse("evaluation_confirm", kwargs={"pk": self.get_object().pk})

    def form_valid(self, form):
        ft, imgstr = self.request.POST["footprint"].split(";base64,")
        data = ContentFile(
            base64.b64decode(imgstr + "=="), name="pdf." + ft.split("/")[-1]
        )
        evaluation = self.get_object()
        evaluation.pdf_sheet = data
        evaluation.save()
        return JsonResponse({"image": "created"})


class EvaluationShareUpload(EvaluationEditorMixin, UpdateView):
    model = Evaluation
    fields = [
        "footprint",
    ]

    def get_success_url(self):
        return reverse("evaluation_confirm", kwargs={"pk": self.get_object().pk})

    def form_valid(self, form):
        ft, imgstr = self.request.POST["footprint"].split(";base64,")
        data = ContentFile(
            base64.b64decode(imgstr + "=="), name="share." + ft.split("/")[-1]
        )
        evaluation = self.get_object()
        evaluation.share = data
        evaluation.save()
        return JsonResponse({"image": "created"})


class EvaluationSocialThumbnailUpload(EvaluationEditorMixin, UpdateView):
    model = Evaluation
    fields = [
        "footprint",
    ]

    def get_success_url(self):
        return reverse("evaluation_confirm", kwargs={"pk": self.get_object().pk})

    def form_valid(self, form):
        ft, imgstr = self.request.POST["footprint"].split(";base64,")
        data = ContentFile(
            base64.b64decode(imgstr + "=="),
            name="socialthumbnail." + ft.split("/")[-1],
        )
        evaluation = self.get_object()
        evaluation.social_thumbnail = data
        evaluation.save()
        return JsonResponse({"image": "created"})


class EvaluationConfirm(
    LoginRequiredMixin, CanEvaluateMixin, SuccessMessageMixin, FormView
):
    template_name = "scoring/evaluation_confirm.html"
    success_message = _("Vous avez validé votre évaluation")
    form_class = EvaluationConfirmForm

    def __init__(self):
        super(EvaluationConfirm, self).__init__()
        self._evaluation = None
        self._scores_categories = None

    def get_object(self):
        if not self._evaluation:
            self._evaluation = get_object_or_404(
                Evaluation.objects.prefetch_related(
                    "scores_categories", "scores_categories__category", "tags"
                ),
                pk=self.kwargs["pk"],
            )
        return self._evaluation

    def get_structure(self):
        return self.get_object().entity.entity_level.structure

    def get_subscription_option(self):
        evaluation = self.get_object()
        subscription_pack = (
            SubscriptionPack.objects.filter(
                structure=evaluation.entity.entity_level.structure
            )
            .order_by("-start_date")
            .first()
        )
        if evaluation.sheet.type.slug == "evaluation_collaborateurs_360":
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

    def get_scores_categories(self):
        if not self._scores_categories:
            self._scores_categories = self.get_object().scores_categories.all()
        return self._scores_categories

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        # context for don't display header and footer on questionnary
        data["no_header"] = True
        data["no_footer"] = True

        data["entity"] = self.get_object().entity
        data["accessible_entities"] = []

        if self.get_object().entity:
            data["membership"] = self.request.user.get_rights(self.get_object().entity)
            if data["membership"] is None:
                # Utilisateur sans lien avec cette entreprise : accès refusé (avant : erreur 500)
                raise PermissionDenied
            if data["membership"].structure_id:
                data["accessible_entities"] = data[
                    "membership"
                ].structure.get_main_entity.get_all_children_entities
            elif data["membership"].is_owner:
                data["accessible_entities"] = data[
                    "membership"
                ].entity.get_all_children_entities
        evaluations = (
            Evaluation.objects.filter(
                entity__in=data["accessible_entities"],
                sheet__type__is_collaborator=False,
            )
            .select_related("entity")
            .order_by("-created_date")
        )
        last_global_evaluations = {}
        for evaluation in evaluations:
            if evaluation.entity_id not in last_global_evaluations:
                last_global_evaluations[evaluation.entity_id] = evaluation

        # L'évaluation affichée sert de repli pour son entité : une entreprise toute neuve n'a pas encore
        # d'autre évaluation, et une entité sans évaluation exploitable est simplement ignorée
        # (avant : KeyError, la page "Reprendre le questionnaire" plantait).
        last_global_evaluations.setdefault(self.get_object().entity_id, self.get_object())

        entities_for_selector = []
        for ellemm in data["accessible_entities"]:
            last_evaluation = last_global_evaluations.get(ellemm.id)
            if last_evaluation is None:
                continue
            parent_name = (
                str(ellemm.parent_entity) if ellemm.parent_entity is not None else "none"
            )
            entities_for_selector.append(
                {
                    "name": str(last_evaluation),
                    "pk": str(last_evaluation.pk),
                    "level": str(ellemm.entity_level.level),
                    "parent": parent_name,
                    "htmlname": str(last_evaluation).replace(" ", "_"),
                    "parenthtml": parent_name.replace(" ", "_"),
                }
            )
        # Le gabarit insère cette chaîne entre apostrophes dans du JavaScript : on échappe donc les apostrophes
        data["json_formatted"] = json.dumps(entities_for_selector).replace("'", "\\'")

        data["evaluation"] = self.get_object()
        data["min_rate"] = constanceconfig.MIXITY_MIN_ANSWER_RATE
        data = EvaluationFill.set_trial_cat(data["evaluation"], data)
        data["scores_categories"] = []
        for sc in self.get_scores_categories():
            if sc.answers.count() > 0:
                data["scores_categories"].append(sc)

        next_question = self._evaluation.next_question
        if next_question:
            kwargs = {
                "pk": self._evaluation.pk,
                "category": next_question.category.slug,
                "subcategory": self._evaluation.first_subcategory_slug,
                "page": 0,
            }
            if self._evaluation.next_question.target:
                kwargs["target"] = self._evaluation.next_question.target
            data["next_url"] = reverse("evaluation_fill", kwargs=kwargs)
            data["button_name"] = _("Reprendre le questionnaire")
        else:
            first_score = self._evaluation.scores_categories.first()
            first_subcategory = (
                first_score.category.subcategories.first() if first_score else None
            )
            if first_score and first_subcategory:
                kwargs = {
                    "pk": self._evaluation.pk,
                    "category": first_score.category.slug,
                    "subcategory": first_subcategory.slug,
                    "page": 0,
                }
                if first_score.target:
                    kwargs["target"] = first_score.target
                data["next_url"] = reverse("evaluation_fill", kwargs=kwargs)
            else:
                # Évaluation sans question ni score (ex. questionnaire non généré) : rien à reprendre
                data["next_url"] = "/"
            data["button_name"] = _("Vérifier le questionnaire")
        return data

    def form_valid(self, form):
        evaluation = self.get_object()
        must_validate_by_admin = settings.DEFAULT_ENABLED_EVALUATION
        evaluation.modified_by_user_date = timezone.now()
        evaluation.version = timezone.now()
        is_mixity_start = evaluation.sheet.type.slug == "mixity_start"
        if is_mixity_start:
            must_validate_by_admin = True
            evaluation.private_display = True
            subscription_option = SubscriptionOption.objects.get(
                start_date__lte=evaluation.created_date,
                end_date__gte=evaluation.created_date,
                product="diag",
                subscriptionPack__structure=evaluation.entity.entity_level.structure,
            )
            if subscription_option.is_trial:
                send_mail_mixity_start_validated(
                    self.request.user, subscription_option, self.request
                )
        evaluation.do_user_validation()

        if evaluation.sheet.type.slug == "evaluation_collaborateurs_360":
            product = "human"
        else:
            product = "diag"
        subscription_option = (
            SubscriptionOption.objects.filter(
                subscriptionPack__structure=evaluation.entity.entity_level.structure,
                product__slug=product,
            )
            .order_by("-start_date")
            .first()
        )

        if not (subscription_option and subscription_option.is_trial):
            send_evaluation_created_mail(self.request.user, self.request, evaluation)
        alert_evaluation_created_mail(self.request.user, self.request, evaluation)
        evaluation.create_aims()
        evaluation.export_answer_sheet()  # Used when the user validate the evaluation
        if must_validate_by_admin:
            evaluation.do_admin_validation()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("home", kwargs={"slug": self.get_object().entity.slug})


class StructureDataViewMixin:
    @property
    def is_human(self):
        return (
            self.kwargs.get("subscriptionOption.product.slug") == "human"
            or self.get_evaluation().is_human
        )

    def get_evaluation(self):
        if not self._evaluation:
            if self.request.user.is_authenticated and self.request.user.is_staff:
                queryset = self.object.evaluations.filter(is_validated_by_user=True)
            elif (
                self.request.user.is_authenticated
                and self.request.user.test_func_rights(self.object)
            ):
                queryset = self.object.evaluations.filter(
                    is_validated_by_admin=True, private_display=True
                )
            else:
                queryset = self.object.evaluations.filter(
                    is_validated_by_admin=True, public_display=True
                )

            if self.kwargs.get("subscriptionOption"):
                queryset = queryset.filter(
                    subscription_option__product__slug=self.kwargs.get(
                        "subscriptionOption"
                    )
                )

            evals = queryset.select_related(
                "sheet",
                "sheet__type__questionary",
            ).prefetch_related(
                Prefetch(
                    "scores_categories",
                    queryset=ScoreCategory.objects.select_related(
                        "category"
                    ).prefetch_related("category__subcategories"),
                ),
                Prefetch(
                    "aims",
                    queryset=Aim.objects.select_related("answer__question").all(),
                ),
            )
            if (
                queryset
                and queryset.order_by("-pk")
                .only("sheet__type")
                .first()
                .sheet.type.is_collaborator
            ):
                evals = evals.prefetch_related("human_criteria__choices")
            self._evaluation = evals.order_by("-pk").first()
        return self._evaluation

    # For public and private enterprise pages
    @property
    def target(self):
        return self.kwargs.get("target", "collaborator")

    def get_human_filters(self, evaluation=None):
        """
        Returns a list o filters for human evaluations
        """
        if not evaluation:
            evaluation = self.get_evaluation()

        if evaluation:
            if evaluation.pre_registered_filters:
                # Classic Human
                if evaluation.is_human and not evaluation.is_campus:
                    civility_dict = {
                        choice[0]: choice[1] for choice in CIVILITY_CHOICES
                    }
                    if evaluation.civility_filters_display:
                        human_filters = {}
                        for f in evaluation.civility_filters_display:
                            human_filters[f] = civility_dict[f]
                        return human_filters
                    else:
                        return civility_dict
                # Campus Human
                elif evaluation.is_human and evaluation.is_campus:
                    campus_dict = {}
                    campus_filters_slugs = get_human_campus_short_slugs()
                    for slug in campus_filters_slugs:
                        if slug == "student":
                            campus_dict[slug] = "Etudiant"
                        elif slug == "teacher":
                            campus_dict[slug] = "Enseignant"
                        elif slug == "collaborator":
                            campus_dict[slug] = "Collaborateur"

                    if evaluation.status_filters_display:
                        human_filters = {}
                        for f in evaluation.status_filters_display:
                            human_filters[f] = campus_dict[f]
                        return human_filters
                    else:
                        return campus_dict
            else:
                return None

    def get_current_human_filter(self, evaluation=None):
        """
        Returns the current human filter selected in Human evaluations for both public and private Enterprise pages
        """
        if not evaluation:
            evaluation = self.get_evaluation()
        human_filters = self.get_human_filters(evaluation)
        current_human_filter = None
        if evaluation:
            if evaluation.is_human and human_filters and "target" in self.kwargs:
                current_human_filter = self.kwargs.get("target")
        return current_human_filter

    def get_scores_categories(self, context):
        if (
            not context["evaluation"].sheet.type.workforce_limit
            and context["evaluation"].sheet.year < 2020
        ):
            excluded_slug = "all"
        else:
            excluded_slug = "your-suggestions"
        context["scores_categories"] = (
            context["evaluation"]
            .scores_categories.filter(
                category__slug__in=MAIN_CATEGORIES_SLUGS + ["your-suggestions"]
            )
            .exclude(category__slug=excluded_slug)
        )
        if context["evaluation"].is_category_evaluation:
            context["score_category"] = (
                context["evaluation"]
                .scores_categories.filter(category__slug__in=MAIN_CATEGORIES_SLUGS)
                .exclude(category__slug="all")
                .first()
            )
        return

    def get_strengths_weaknesses_and_aims(self, context):
        context["scores_categories_strengths"] = defaultdict(list)
        context["scores_categories_weaknesses"] = defaultdict(list)
        answers = (
            Answer.objects.filter(
                evaluation=context["evaluation"],
            )
            .order_by("question_id", "pk")
            .distinct("question")
            .select_related("question__category", "question__subcategory", "comment")
        )

        strengths = context["evaluation"].strengths.all()
        weaknesses = context["evaluation"].weaknesses.all()
        for strength in strengths:
            if strength.category and strength.category.slug:
                context["scores_categories_strengths"][strength.category.slug].append(
                    {
                        "subcategory__name": strength.subcategory.name,
                        "subcategory__slug": strength.subcategory.slug,
                        "description": str(strength.description),
                    }
                )
        for weakness in weaknesses:
            if weakness.category and weakness.category.slug:
                context["scores_categories_weaknesses"][weakness.category.slug].append(
                    {
                        "subcategory__name": weakness.subcategory.name,
                        "subcategory__slug": weakness.subcategory.slug,
                        "description": str(weakness.description),
                    }
                )

        # for answer in answers:
        #     if answer.comment:
        #         context[
        #             (
        #                 "scores_categories_strengths"
        #                 if answer.comment.is_good
        #                 else "scores_categories_weaknesses"
        #             )
        #         ][answer.question.category.slug].append(
        #             {
        #                 "subcategory__name": answer.question.subcategory.name,
        #                 "subcategory__slug": answer.question.subcategory.slug,
        #                 "description": str(answer.get_description_display),
        #                 "weight": answer.question.weight_index,
        #             }
        #         )

        context["scores_categories_aims"] = {}
        context["aim_count"] = {}

        def prevent_save(*args, **kwargs):
            pass

        for scores_categorie in context["scores_categories"]:
            if context["evaluation"].sheet.type.slug == "mixity_evaluation_campus":
                scores_categorie.value = scores_categorie.compute_score(
                    target=context["target_name"]
                )
                scores_categorie.save = prevent_save  # Disable any save() on thoses target specific ScoreCategories

            res, aim_count = scores_categorie.get_aims
            if res:
                context["scores_categories_aims"][scores_categorie.category.slug] = res
                context["aim_count"][scores_categorie.category.slug] = aim_count

        return

    def get_collaborators_statistics(self, context):
        if not self.is_human:
            context["collaborators_statistics"] = [
                stat
                for stat in CollaboratorsStatistics.objects.select_related(
                    "statistics"
                ).filter(evaluation=self.get_evaluation(), status="finished")
            ]
            context["collaborators_statistics_count"] = len(
                context["collaborators_statistics"]
            )

    def get_human_data(self, context):
        collaborators_queryset = generate_collaborator_filters(
            context["evaluation"],
            self.collaborator_filters,
            self.collaborator_criteria_filters,
        )
        # TODO : LATER you have to send this filtered queryset to React Component
        context["collaborators_queryset"] = collaborators_queryset
        context["human_criteria"] = (
            context["evaluation"]
            .human_criteria.all()
            .annotate(count_choice=Count("choices"))
            .order_by("count_choice")
            .select_related("evaluation")
            .prefetch_related(
                Prefetch(
                    "choices",
                    queryset=HumanCriteriaChoice.objects.annotate(
                        total=Count(
                            "collaborators",
                            filter=Q(
                                collaborators__in=collaborators_queryset
                            ),  # No need to filter by id, that make one more request
                        )
                    ).order_by("-total"),
                )
            )
        )
        context["nb_collaborator_with_filter"] = collaborators_queryset.filter(
            evaluation=context["evaluation"]
        ).count()
        human_limit = HUMAN_FILTER_LIMIT
        if context["evaluation"].is_scan:
            human_limit = 5
        context["nb_collaborator_with_filter_min"] = human_limit

    # IMPORTANT REFONTE : Envoi de tous les indicateurs
    def get_questions_and_answers(self, context):
        def prevent_save(reset_mean_score=True, *args, **kwargs):
            pass

        tag_exclude = []
        if not self._entity.entity_level.structure.is_campus:
            tag_exclude = QuestionTag.objects.filter(
                name__in=["campus_student", "campus_teacher", "campus_collaborator"]
            )

        answers = self.get_answers(
            context["evaluation"], tag_exclude, context["target_name"]
        )

        questions = (
            context["evaluation"]
            .sheet.questions.select_related("sibling")
            .prefetch_related("mandatory_tags")
            .exclude(mandatory_tags__in=tag_exclude)
        )

        if self._entity.entity_level.structure.is_campus:
            # We want to exclude questions which have exactly thoses 3 tags, not 1 of them
            questions = questions.exclude(
                Q(forbidden_tags__name__in=["campus_student"])
                & Q(forbidden_tags__name__in=["campus_teacher"])
                & Q(forbidden_tags__name__in=["campus_collaborator"])
            )

        #  Handling questions
        if context["evaluation"].tags.count() == 0:
            for question in questions:
                context[f"answer_{question.google_sheets_id}"] = Answer(
                    id=question.google_sheets_id,
                    question=question,
                    evaluation=context["evaluation"],
                )
                context[f"answer_{question.google_sheets_id}"].save = prevent_save
                # Handling siblings
                tmp_question = question
                passed_questions = [question.google_sheets_id]
                while (
                    tmp_question.sibling
                    and tmp_question.sibling.google_sheets_id not in passed_questions
                ):
                    tmp_question = tmp_question.sibling
                    passed_questions.append(tmp_question.google_sheets_id)

                if tmp_question != question:
                    context[f"answer_{tmp_question.google_sheets_id}"] = Answer(
                        id=question.google_sheets_id,
                        question=question,
                        evaluation=context["evaluation"],
                    )
                    context[f"answer_{tmp_question.google_sheets_id}"].save = (
                        prevent_save
                    )

        # Handling Mixity International and old evaluations
        if (
            context["evaluation"].sheet.year < 2021
            or context["evaluation"].sheet.slug == "mixity_international"
        ):
            find_sibling = True
        else:
            find_sibling = False

        count_sibling = 0
        # Handling Answers
        for answer in answers:
            context[f"answer_{answer.question.google_sheets_id}"] = answer

            if find_sibling:
                count_sibling += 1
                tmp_question = answer.question
                passed_questions = [answer.question.google_sheets_id]

                while (
                    tmp_question.sibling
                    and tmp_question.sibling.google_sheets_id not in passed_questions
                ):
                    tmp_question = tmp_question.sibling
                    passed_questions.append(tmp_question.google_sheets_id)

                if tmp_question != answer.question:
                    context[f"answer_{tmp_question.google_sheets_id}"] = answer

        if "answer_202130671" in context or "answer_20213067" in context:
            context["answer_202130671_20213067"] = 0

            if "answer_20213067" in context and context["answer_20213067"].value:
                context["answer_202130671_20213067"] += context["answer_20213067"].value

            if "answer_202130671" in context and context["answer_202130671"].value:
                context["answer_202130671_20213067"] -= context[
                    "answer_202130671"
                ].value

        if "answer_20215001" in context:
            subanswers = context["answer_20215001"].subanswers.all()
            if len(subanswers) >= 3:
                context["answer_20215001"].value = (
                    int(subanswers[0].value or 0)
                    + int(subanswers[1].value or 0)
                    + int(subanswers[2].value or 0)
                )

        if "answer_202151001" in context:
            subanswers = context["answer_202151001"].subanswers.all()
            if len(subanswers) >= 3:
                context["answer_202151001"].value = (
                    int(subanswers[0].value or 0)
                    + int(subanswers[1].value or 0)
                    + int(subanswers[2].value or 0)
                )

        if "answer_202151002" in context:
            subanswers = context["answer_202151002"].subanswers.all()
            if len(subanswers) >= 3:
                context["answer_202151002"].value = (
                    int(subanswers[0].value or 0)
                    + int(subanswers[1].value or 0)
                    + int(subanswers[2].value or 0)
                )

        if "answer_20214002" in context:
            subanswers = context["answer_20214002"].subanswers.all()
            if len(subanswers) >= 3:
                context["answer_20214002"].value = (
                    int(subanswers[0].value or 0)
                    + int(subanswers[1].value or 0)
                    + int(subanswers[2].value or 0)
                )

        if "answer_20220003" in context:
            subanswers = context["answer_20220003"].subanswers.all()
            if len(subanswers) >= 3:
                context["answer_20220003"].value = (
                    int(subanswers[0].value or 0)
                    + int(subanswers[1].value or 0)
                    + int(subanswers[2].value or 0)
                )

        if "answer_20221001" in context:
            subanswers = context["answer_20221001"].subanswers.all()
            if len(subanswers) >= 4:
                context["answer_20221001"].value = (
                    int(subanswers[0].value or 0)
                    + int(subanswers[1].value or 0)
                    + int(subanswers[2].value or 0)
                    + int(subanswers[3].value or 0)
                )

        if "answer_20214006" in context:
            subanswers = context["answer_20214006"].subanswers.all()
            if len(subanswers) >= 3:
                context["answer_20214006"].value = (
                    int(subanswers[0].value or 0)
                    + int(subanswers[1].value or 0)
                    + int(subanswers[2].value or 0)
                )

        nothing = True
        context["answer_ethnies_gender"] = []
        for i in range(20213025, 20213032):
            if (
                "answer_" + str(i) in context
                and context["answer_" + str(i)].subanswers.count() > 0
            ):
                nothing = False
                context["answer_ethnies_gender"].append(
                    context["answer_" + str(i)].subanswers.all()
                )
            else:
                context["answer_ethnies_gender"].append(None)
        if nothing:
            context.pop("answer_ethnies_gender")
        else:
            if context["evaluation"].tags.filter(name="us").exists():
                context["labels_ethnies_gender"] = [
                    "... White people",
                    "... Black or African Americans",
                    "... Asian people",
                    "... Hispanic or Latinx",
                    "... Multiracial",
                    "... Natives Hawaiian or other Pacific islander",
                    "... American Indian or Alaska native",
                ]
            else:
                context["labels_ethnies_gender"] = [
                    "... White people",
                    "... Black people",
                    "... Asian people",
                    None,
                    "... Minority ethnies",
                ]
        return context

    # tag_exclude is only for human, target only for evaluation with targets(like campus)
    def get_answers(self, evaluation, tag_exclude, target=None):
        if self.is_human:
            return (
                Answer.objects.select_related(
                    "question__sibling",
                    "sibling_answer",
                    "question",
                )
                .prefetch_related("question__mandatory_tags")
                .filter(evaluation_id=evaluation.id, display=True)
                .exclude(question__mandatory_tags__in=tag_exclude)
                .order_by("question_id", "pk")
                .distinct("question")
                .only(
                    "id",
                    "value",
                    "ratio_value",
                    "text_value",
                    "currency_symbol",
                    "question",
                    "sibling_answer",
                    "mean_score",
                    "mean_score_in_business_line",
                    # "perimeter",
                )
            )
        answers = (
            Answer.objects.select_related(
                "question__sibling",
                "choice__question",
                "sibling_answer",
                "evaluation__entity__entity_level__structure__business_line",
                "evaluation__sheet",
            )
            .order_by("question_id", "pk")
            .prefetch_related(
                "question__subquestions",
                Prefetch(
                    "subanswers",
                    queryset=SubAnswer.objects.select_related("subquestion").only(
                        "value",
                        "subquestion",
                        "answer",
                        "mean_score",
                        "mean_score_in_business_line",
                        "ratio_value",
                    ),
                ),
            )
            .filter(evaluation_id=evaluation.id, display=True)
            .only(
                "id",
                "choice",
                "value",
                "ratio_value",
                "text_value",
                "currency_symbol",
                "question",
                "sibling_answer",
                "mean_score",
                "mean_score_in_business_line",
                "evaluation__entity__entity_level__structure__business_line",
                "evaluation__entity__entity_level__structure__juridic_name",
                "evaluation__sheet__year",
                "perimeter",
            )
        )
        if target and target != "all":
            answers.filter(question__target=target)
        return answers

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.exclude(slug="all")

        context["evaluation"] = self.get_evaluation()
        context["target_name"] = self.target

        if context["evaluation"]:
            context["target_displays"] = {
                slug: label
                for slug, label in TARGET_CHOICE
                if slug in context["evaluation"].targets
            }
            context["display_mean_score"] = context["evaluation"].display_mean_score
            self.get_scores_categories(context)
            self.get_strengths_weaknesses_and_aims(context)
            if self.is_human:
                self.get_human_data(context)
            else:
                self.get_collaborators_statistics(context)

            self.get_questions_and_answers(context)
        if "answer_20216000" in context:
            answer_20216000_sum = 0
            subanswers_20216000 = context["answer_20216000"].subanswers.all()
            if len(subanswers_20216000) >= 3:
                if subanswers_20216000[0].value:
                    answer_20216000_sum += subanswers_20216000[0].value
                if subanswers_20216000[1].value:
                    answer_20216000_sum += subanswers_20216000[1].value
                if subanswers_20216000[2].value:
                    answer_20216000_sum += subanswers_20216000[2].value
            context["answer_20216000_sum"] = answer_20216000_sum

        if "answer_202160001" in context:
            answer_202160001_sum = 0
            subanswers_202160001 = context["answer_202160001"].subanswers.all()
            if len(subanswers_202160001) >= 3:
                if subanswers_202160001[0].value:
                    answer_202160001_sum += subanswers_202160001[0].value
                if subanswers_202160001[1].value:
                    answer_202160001_sum += subanswers_202160001[1].value
                if subanswers_202160001[2].value:
                    answer_202160001_sum += subanswers_202160001[2].value
            context["answer_202160001_sum"] = answer_202160001_sum

        if "answer_20220003" in context:
            answer_20220003_sum = 0
            subanswers_20220003 = context["answer_20220003"].subanswers.all()
            if len(subanswers_20220003) >= 3:
                if subanswers_20220003[0].value:
                    answer_20220003_sum += subanswers_20220003[0].value
                if subanswers_20220003[1].value:
                    answer_20220003_sum += subanswers_20220003[1].value
                if subanswers_20220003[2].value:
                    answer_20220003_sum += subanswers_20220003[2].value
            context["answer_20220003_sum"] = answer_20220003_sum

        if "answer_20221001" in context:
            answer_20221001_sum = 0
            subanswers_20221001 = context["answer_20221001"].subanswers.all()
            if len(subanswers_20221001) >= 3:
                if subanswers_20221001[0].value:
                    answer_20221001_sum += subanswers_20221001[0].value
                if subanswers_20221001[1].value:
                    answer_20221001_sum += subanswers_20221001[1].value
                if subanswers_20221001[2].value:
                    answer_20221001_sum += subanswers_20221001[2].value
            context["answer_20221001_sum"] = answer_20221001_sum

        # Pre-registered filters of classic Human
        context["human_filters"] = self.get_human_filters()

        # Sending pre-computed scores if a filter is chosen
        current_human_filter = self.get_current_human_filter()

        if current_human_filter:
            context["current_human_filter"] = current_human_filter
            pre_registered_filters = self.get_evaluation().pre_registered_filters[
                current_human_filter
            ]["scores"]
            context["filters_scores_categories"] = pre_registered_filters

            # Mean_score, mean_score_in_business_line and display scores
            filters_mean_score = {}
            filters_mean_score_business_line = {}
            display_scores = {}
            for sc in pre_registered_filters:
                for sc_key, sc_value in sc.items():
                    filters_mean_score[sc_key] = sc_value["mean_score"]
                    filters_mean_score_business_line[sc_key] = sc_value[
                        "mean_score_business_line"
                    ]
                    display_scores[sc_key] = sc_value["display_score"]
            context["filters_mean_score"] = filters_mean_score
            context["filters_mean_score_business_line"] = (
                filters_mean_score_business_line
            )
            context["filters_display_score"] = display_scores
            context[
                "filters_global_score"
            ] = self.get_evaluation().pre_registered_filters[current_human_filter][
                "global_score"
            ]

        return context


class StructureDetailPublicView(StructureDataViewMixin, UpdateView, FormView):
    model = Structure
    template_name = "scoring/evaluation_detail_public.html"
    form_class = CollaboratorCriteriaChoiceForm

    def get_entity(self):
        return self.get_object()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["evaluation"] = self.get_evaluation()
        kwargs["target"] = self.target
        # Send the selected human filter to the form
        kwargs["human_filter"] = self.get_current_human_filter()
        return kwargs

    def get_object(self, queryset=None):
        if not self._entity:
            self._entity = get_object_or_404(
                Entity.objects.select_related(
                    "entity_level__structure"
                ).prefetch_related("evaluations__subscription"),
                slug=self.kwargs["slug"],
            )
        return self._entity

    def __init__(self):
        super().__init__()
        self._evaluation = None
        self._entity = None
        # Used to pre-filter the form result if a human filter si selected
        self.collaborator_filters = {}
        self.collaborator_criteria_filters = {}

    def form_valid(self, form):
        self.collaborator_filters = {
            "civility": form.cleaned_data.get("civility"),
            "age": form.cleaned_data.get("age"),
            "status": form.cleaned_data.get("status"),
        }
        # Used to keep the result of the form if a human filter is selected
        if self.get_current_human_filter() and self._evaluation:
            # Human Classic
            if self._evaluation.is_human and not self._evaluation.is_campus:
                self.collaborator_filters["civility"].append(
                    self.get_current_human_filter()
                )
            # Human Campus
            elif self._evaluation.is_human and self._evaluation.is_campus:
                filters = get_filtered_human_campus_slugs(
                    self.get_current_human_filter()
                )
                self.fields["status"].initial = filters

        self.collaborator_criteria_filters = {}
        for field in form.cleaned_data:
            if field != "civility" and field != "age" and field != "status":
                self.collaborator_criteria_filters[field] = form.cleaned_data[field]

        context = self.get_context_data(form=form, pk=self._evaluation.pk)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        # Initialize the form if a human filter is selected
        if self.get_current_human_filter():
            # Human Classic
            if self._evaluation.is_human and not self._evaluation.is_campus:
                self.collaborator_filters = {
                    "civility": [self.get_current_human_filter()],
                    "age": [],
                    "status": None,
                }
            # Human Campus
            elif self._evaluation.is_human and self._evaluation.is_campus:
                filters = get_filtered_human_campus_slugs(
                    self.get_current_human_filter()
                )
                self.collaborator_filters = {
                    "civility": [],
                    "age": [],
                    "status": filters,
                }

        context = super().get_context_data(**kwargs)
        if context["evaluation"]:
            if self.get_evaluation().subscription.is_trial:
                context["trial_cats"] = Category.objects.filter(
                    slug__in=MAIN_CATEGORIES_SLUGS
                ).exclude(
                    Q(slug="all")
                    | Q(slug=context["scores_categories"][0].category.slug)
                )

            items = context["evaluation"].scores_categories.count()
            subcategories = 0

            for sc in context["evaluation"].scores_categories.all():
                subcategories += sc.category.subcategories.count()
            context["subcategories_count"] = (
                "Items : " + str(items) + "\\nSous catégories : " + str(subcategories)
            )

            if context["evaluation"].social_thumbnail:
                context["og_image"] = context["evaluation"].social_thumbnail.url

        if "evaluation" in context and context["evaluation"]:
            context["upload_url"] = reverse(
                "structure_pdf_upload", kwargs={"pk": context["evaluation"].pk}
            )
        context["target"] = self.target

        # Used to distinguish between Public Urls and Private Urls
        context["is_private"] = False
        return context


class StructureDetailPrivateView(LoginRequiredMixin, StructureDetailPublicView):
    def get_object(self, queryset=None):
        if not self._entity:
            self._entity = get_object_or_404(
                Entity.objects.select_related(
                    "entity_level__structure",
                ),
                evaluations__id=self.kwargs["pk"],
            )
        return self._entity

    def get_evaluation(self):
        if not self._evaluation:
            self._evaluation = get_object_or_404(
                Evaluation.objects.select_related(
                    "sheet",
                    "sheet__type",
                    "subscription__structure",
                ).prefetch_related(
                    Prefetch(
                        "scores_categories",
                        queryset=ScoreCategory.objects.select_related(
                            "category"
                        ).prefetch_related("category__subcategories"),
                    ),
                    "human_criteria__choices",
                ),
                pk=self.kwargs["pk"],
            )
        if (
            self.request.user.is_authenticated
            and self._evaluation.is_validated_by_admin
            and self._evaluation.private_display
            and self.request.user.test_func_rights(self.object)
        ):
            return self._evaluation
        elif (
            self.request.user.is_authenticated
            and self.request.user.is_staff
            and self._evaluation.is_validated_by_user
        ):
            return self._evaluation

        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk"] = self.kwargs["pk"]
        context["target"] = self.target
        context["is_private"] = True
        return context


class EvaluationDetailView(LoginRequiredMixin, StructureDetailPublicView):
    @staticmethod
    def display_version_from_slug(version):
        if version != "en-cours":
            year, month_slug = version.split("-")
            result = year + "-"

            actual_language = get_language()
            activate("fr")
            for month in MONTHS:
                if slugify(month) == month_slug:
                    return result + month
            activate(actual_language)
        else:
            return "en-cours"

    def get_object(self, queryset=None):
        if not self._entity:
            self._entity = get_object_or_404(Entity, slug=self.kwargs["entity"])
        return self._entity

    def get_evaluation(self):
        if not self._evaluation:
            self._evaluation = self._entity.evaluations.filter(
                display_version=self.display_version_from_slug(self.kwargs["version"])
            ).first()
        return self._evaluation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk"] = self._evaluation.pk
        context["target"] = self.target
        context["is_private"] = True
        context["version"] = self.kwargs["version"]
        context["type"] = self.kwargs["type"]
        return context
