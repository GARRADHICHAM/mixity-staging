import json

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, FormView, TemplateView
from django.utils.translation import ugettext_lazy as _, get_language, activate
from django.utils.text import slugify

from accounts.forms import CollaboratorCriteriaChoiceForm
from accounts.models import Entity
from scoring.models import Evaluation
from subscriptions.models import Product, SubscriptionOption
from scoring.views import StructureDataViewMixin
from accounts.vocabularies import CIVILITY_CHOICES, AGE_CHOICES, CAMPUS_CHOICE, MONTHS
from mixity.dashboard.views import DashboardStructureViewMixin, DashboardAccessMixin
from mixity.serializers import VersionsListSerializer


from mixity.utils import segment_tracking


class DashboardFiltersView(
    LoginRequiredMixin,
    DashboardAccessMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "dashboard/evaluation_criterias_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class CollaboratorScoreCardView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    TemplateView,
):
    template_name = "dashboard/collaborator_score_card_page.html"

    def test_func(self):
        return self.request.user.scan_collaborator


class DashboardAssessView(
    StructureDataViewMixin,
    LoginRequiredMixin,
    DashboardAccessMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DetailView,
    FormView,
):
    model = Entity
    template_name = "dashboard/dashboard_assess.html"
    form_class = CollaboratorCriteriaChoiceForm

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

    def get_object(self, **kwargs):
        self._entity = self.entity
        return self._entity

    def get_evaluation(self, **kwargs):
        # Récupérer l'évaluation en fonction des paramètres d'URL
        version = self.display_version_from_slug(self.kwargs["version"])

        if self.kwargs["product"] == "human":
            return Evaluation.objects.get(
                entity__slug=self.kwargs["slug"],
                sheet__type__slug="evaluation_collaborateurs_360",
                display_version=version,
            )
        else:
            return (
                Evaluation.objects.filter(
                    entity__slug=self.kwargs["slug"], display_version=version
                )
                .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .first()
            )

    def get_form_kwargs(self):
        kwargs = super(DashboardAssessView, self).get_form_kwargs()
        kwargs["evaluation"] = self.get_evaluation()
        kwargs["target"] = self.target
        return kwargs

    def __init__(self):
        super().__init__()
        self._evaluation = None
        self.versions_list = None
        self._entity = None
        self.collaborator_filters = {}
        self.collaborator_criteria_filters = {}

    def form_valid(self, form):
        self.collaborator_filters = {
            "civility": form.cleaned_data.get("civility"),
            "age": form.cleaned_data.get("age"),
            "status": form.cleaned_data.get("status"),
        }
        self.collaborator_criteria_filters = {}
        for field in form.cleaned_data:
            if field != "civility" and field != "age" and field != "status":
                self.collaborator_criteria_filters[field] = form.cleaned_data[field]

        context = self.get_context_data(form=form, pk=self._evaluation.pk)
        return self.render_to_response(context)

    def get_versions_list(self, *args, **kwargs):
        entity_slug = self.kwargs.get("slug")
        product_slug = self.kwargs.get("product")

        if product_slug == "human":
            evaluations = Evaluation.objects.filter(
                entity=self.entity, sheet__type__slug="evaluation_collaborateurs_360"
            ).order_by("-version")
        else:
            evaluations = (
                Evaluation.objects.filter(entity__slug=entity_slug)
                .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .order_by("-version")
            )

        serializer = VersionsListSerializer(evaluations, many=True)
        return serializer.data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.kwargs.get("product") == "human":
            context["evaluation_status"] = (
                self.entity.entity_level.structure.get_main_entity.get_human_status
            )
            context["current_page"] = "Mixity Human"

            segment_tracking(
                self.request.user,
                "Mixity Human",
                {"structure": self.entity.entity_level.structure.slug},
            )

        else:
            context["current_page"] = "Mixity Diag"
            context["evaluation_status"] = self.entity.get_global_status
            segment_tracking(
                self.request.user, "Mixity Diag", {"structure": self.entity.slug}
            )
        # Filters for exporting Human Excel file
        human_evaluation = self.get_evaluation()
        if human_evaluation and human_evaluation.is_human:
            excel_filters = {}
            # Civility, age and status are default fields
            excel_filters["civility"] = {
                "label": _("Genre"),
                "choices": [{choice[0]: choice[1]} for choice in CIVILITY_CHOICES],
                "is_human_criteria": False,
            }
            excel_filters["age"] = {
                "label": _("Âge"),
                "choices": [{choice[0]: choice[1]} for choice in AGE_CHOICES],
                "is_human_criteria": False,
            }
            if self.get_evaluation().is_campus:
                excel_filters["status"] = {
                    "label": _("Statut"),
                    "choices": [{choice[0]: choice[1]} for choice in CAMPUS_CHOICE],
                    "is_human_criteria": False,
                }

            # Human criteria filters
            for criteria in human_evaluation.human_criteria.all():
                excel_filters[criteria.label] = {
                    "label": criteria.label,
                    "choices": criteria.choices.all(),
                    "is_human_criteria": True,
                }
            context["human_excel_filters"] = excel_filters

        context["current_app"] = _("Mesurer")
        context["dashboard_header"] = True

        context["structure"] = self.entity.entity_level.structure
        context["versions_list"] = self.get_versions_list()
        context["product"] = Product.objects.get(slug=self.kwargs.get("product"))

        evaluation = self.get_evaluation()
        return context

    def dispatch(self, request, *args, **kwargs):
        # Si l'évaluation est récente, en renvoie vers la version React de la page Assess
        self.evaluation = None
        try:
            self.evaluation = self.get_evaluation()
            if self.evaluation and self.evaluation.sheet.type.slug in [
                "mixity_evaluation_diag",
                "evaluation_collaborateurs_360",
            ]:
                return redirect(
                    reverse(
                        "dashboard:dashboard_assess_test",
                        args=[
                            self.evaluation.entity.slug,
                            "diag",
                            self.evaluation.display_version_slugified,
                        ],
                    )
                )
        # Si les paramètres de l'url ne permettent pas de remonter vers une version d'évaluation existante, on redirige l'utilisateur vers la version la plus récente de son évaluation. (en fonction du paramètre produit)
        except Evaluation.DoesNotExist:
            print("Évaluation introuvable")

        if self.evaluation is None:
            if self.kwargs["product"] == "diag":
                self.evaluation = self.entity.last_global_evaluation
            elif self.kwargs["product"] == "human":
                self.evaluation = self.entity.last_human_evaluation
            else:
                self.evaluation = self.entity.last_scan_evaluation
            if self.evaluation:
                return redirect(
                    reverse(
                        "dashboard:dashboard_assess",
                        args=[
                            self.evaluation.entity.slug,
                            self.kwargs["product"],
                            self.evaluation.display_version_slugified,
                        ],
                    )
                )
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class DashboardAssessTestView(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "dashboard/assess_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        return context

    def retrieve_evaluation(self, **kwargs):
        if self.kwargs["product"] == "human":
            return Evaluation.objects.get(
                entity__slug=self.kwargs["slug"],
                display_version=self.display_version_from_slug(self.kwargs["version"]),
                sheet__type__slug="evaluation_collaborateurs_360",
            )
        elif self.kwargs["product"] == "scan":
            return Evaluation.objects.get(
                entity__slug=self.kwargs["slug"],
                display_version=self.display_version_from_slug(self.kwargs["version"]),
                sheet__type__slug="mixity_evaluation_scan",
            )
        else:
            return (
                Evaluation.objects.filter(
                    entity__slug=self.kwargs["slug"],
                    display_version=self.display_version_from_slug(
                        self.kwargs["version"]
                    ),
                )
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                .order_by("-version")
                .first()
            )

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

    def dispatch(self, request, *args, **kwargs):
        # Si l'évaluation utilise un autre question sheet type que diag/scan/360, on redirige vers l'ancienne page assess
        self.evaluation = None
        try:
            self.evaluation = self.retrieve_evaluation()

            if self.evaluation and self.evaluation.sheet.type.slug not in [
                "mixity_evaluation_diag",
                "mixity_evaluation_scan",
                "evaluation_collaborateurs_360",
            ]:
                return redirect(
                    reverse(
                        "dashboard:dashboard_assess",
                        args=[
                            self.evaluation.entity.slug,
                            "diag",
                            self.evaluation.display_version_slugified,
                        ],
                    )
                )
        # Si les paramètres de l'url ne permettent pas de remonter vers une version d'évaluation existante, on redirige l'utilisateur vers la version la plus récente de son évaluation. (en fonction du paramètre produit)
        except Evaluation.DoesNotExist:
            print("Évaluation introuvable")

        if self.evaluation is None:
            if self.kwargs["product"] == "diag":
                self.evaluation = self.entity.last_global_evaluation
            elif self.kwargs["product"] == "human":
                self.evaluation = self.entity.last_human_evaluation
            else:
                self.evaluation = self.entity.last_scan_evaluation
            if self.evaluation:
                return redirect(
                    reverse(
                        "dashboard:dashboard_assess_test",
                        args=[
                            self.evaluation.entity.slug,
                            self.kwargs["product"],
                            self.evaluation.display_version_slugified,
                        ],
                    )
                )
        # Si aucune condition précédente n'est remplie, rediriger vers la page par défaut
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class DashboardCreateIndicatorView(
    LoginRequiredMixin, DashboardAccessMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard/create_indicator_page.html"

    def get_queryset(self, request, *args, **kwargs):
        return super().get_queryset(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_staff


class EvaluationSurveyView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "dashboard/evaluation_survey.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["evaluation"] = self.evaluation
        context["no_header"] = True
        context["no_footer"] = True
        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            self.evaluation = self.get_object()
            if self.evaluation and self.evaluation.sheet.type.slug not in [
                "mixity_evaluation_diag",
                "evaluation_collaborateurs_360",
                "mixity_evaluation_scan",
            ]:
                return redirect(
                    reverse(
                        "home",
                        args=[
                            self.kwargs["slug"],
                        ],
                    )
                )
        except Evaluation.DoesNotExist:
            return redirect(
                reverse(
                    "home",
                    args=[
                        self.kwargs["slug"],
                    ],
                )
            )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        if self.kwargs["product"] == "human":
            self.evaluation = Evaluation.objects.get(
                entity__slug=self.kwargs["slug"],
                sheet__type__slug="evaluation_collaborateurs_360",
                display_version="en-cours",
            )
        elif self.kwargs["product"] == "scan":
            self.evaluation = Evaluation.objects.get(
                entity__slug=self.kwargs["slug"],
                sheet__type__slug="mixity_evaluation_scan",
                display_version="en-cours",
            )
        else:
            self.evaluation = (
                Evaluation.objects.exclude(
                    sheet__type__slug="evaluation_collaborateurs_360"
                )
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .get(
                    entity__slug=self.kwargs["slug"],
                    display_version="en-cours",
                )
            )
        return self.evaluation

    def test_func(self):
        return (
            self.request.user.scan_collaborator
            in self.evaluation.scan_collaborators.all()
        )
