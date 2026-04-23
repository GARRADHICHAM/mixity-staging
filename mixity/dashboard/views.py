import json
import time
from copy import copy
from functools import cached_property

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog

from accounts.models import Structure, Entity
from mixity.utils import segment_tracking
from django.urls import reverse

from django.utils.translation import ugettext_lazy as _, get_language, activate

from django.utils.text import slugify

from accounts.vocabularies import MONTHS

from scoring.models import Collaborator, Evaluation
from accounts.models import Membership


class DashboardAccessMixin:
    def dispatch(self, request, no_success_redirect=False, *args, **kwargs):
        user = request.user
        user_membership = None
        collaborator = None
        try:
            user_membership = Membership.objects.filter(user=user)
            collaborator = Collaborator.objects.get(user=user)
        except Membership.DoesNotExist:
            user_membership = None
        except Collaborator.DoesNotExist:
            collaborator = None
        if user_membership != None and user_membership.count() == 0:
            if collaborator != None and collaborator.evaluation != None:
                evaluation_url = (
                    "https://"
                    + request.get_host()
                    + collaborator.evaluation.collaborator_url
                )
                return redirect(evaluation_url)
            else:
                if no_success_redirect:
                    return
                return super().dispatch(request, *args, **kwargs)
        if no_success_redirect:
            return
        return super().dispatch(request, *args, **kwargs)


class DashboardAssessViewMixin:
    @cached_property
    def assess_evaluation(self):
        if self.entity:
            if self.kwargs.get("product") == "human":
                return (
                    self.entity.entity_level.structure.get_main_entity.last_human_evaluation
                )
            elif self.kwargs.get("product") == "scan":
                return (
                    self.entity.entity_level.structure.get_main_entity.last_scan_evaluation
                )
            else:
                return self.entity.last_validated_by_admin_global_evaluation

    @property
    def target(self):
        return self.kwargs.get("target", "collaborator")

    def collaborators(self, evaluation=None, queryset=None):
        if queryset:
            return queryset
        else:
            return Collaborator.objects.filter(evaluation=evaluation)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.assess_evaluation:
            context["assess_evaluation"] = self.assess_evaluation
            context["collaborator_queryset"] = Collaborator.objects.filter(
                evaluation=context["assess_evaluation"]
            )
        if self.target:
            context["target_name"] = self.target
        return context


class DashboardStructureViewMixin:
    @cached_property
    def entity(self):
        current_entity_slug = self.kwargs.get("slug")
        if current_entity_slug:
            return get_object_or_404(
                Entity.objects.select_related("entity_level__structure"),
                slug=current_entity_slug,
            )
        if self.request.user.structures.first():
            return self.request.user.structures.first().get_main_entity
        elif self.request.user.entities.first():
            return self.request.user.entities.first()
        return None

    @cached_property
    def structure(self):
        current_structure_slug = self.kwargs.get("slug")
        if current_structure_slug:
            return get_object_or_404(Structure, slug=current_structure_slug)
        return self.request.user.structures.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["accessible_entities"] = []
        if self.entity:
            context["membership"] = self.request.user.get_rights(self.entity)
            if context["membership"].structure_id:
                context["accessible_entities"] = context[
                    "membership"
                ].structure.get_main_entity.get_all_children_entities
            else:
                entities = Entity.objects.filter(
                    entity_level__structure=self.entity.entity_level.structure,
                    members=self.request.user,
                )
                if entities.count() > 1:
                    for entity in entities:
                        if entity not in context["accessible_entities"]:
                            if self.request.user.get_rights(entity).is_owner:
                                children = entity.get_all_children_entities
                                for child in children:
                                    if (
                                        child == entity
                                        or child not in context["accessible_entities"]
                                    ):
                                        context["accessible_entities"].append(child)
                            else:
                                context["accessible_entities"].append(entity)
                elif context["membership"].is_owner:
                    for entity in entities:
                        context[
                            "accessible_entities"
                        ] += entity.get_all_children_entities
            context["solver"] = self.entity.entity_level.structure.is_solver
            context["global"] = self.entity.last_global_evaluation
            context["human"] = (
                self.entity.entity_level.structure.get_main_entity.last_human_evaluation
            )
            context["scan"] = (
                self.entity.entity_level.structure.get_main_entity.last_scan_evaluation
            )
            diag_evaluations = self.entity.evaluations.exclude(
                sheet__type__slug="evaluation_collaborateurs_360"
            ).exclude(sheet__type__slug="mixity_evaluation_scan")

            if diag_evaluations != None:
                # Cherche l'évaluation en cours si elle existe, sinon prend la dernière par version
                context["diag_evaluation"] = (
                    diag_evaluations.filter(display_version="en-cours").first()
                    or diag_evaluations.order_by("-version").first()
                )

            human_evaluations = self.entity.evaluations.filter(
                sheet__type__slug="evaluation_collaborateurs_360"
            )

            if human_evaluations != None:
                # Cherche l'évaluation en cours si elle existe, sinon prend la dernière par version
                context["human_evaluation"] = (
                    human_evaluations.filter(display_version="en-cours").first()
                    or human_evaluations.order_by("-version").first()
                )

            scan_evaluations = self.entity.evaluations.filter(
                sheet__type__slug="mixity_evaluation_scan"
            )

            if scan_evaluations != None:
                # Cherche l'évaluation en cours si elle existe, sinon prend la dernière par version
                context["scan_evaluation"] = (
                    scan_evaluations.filter(display_version="en-cours").first()
                    or scan_evaluations.order_by("-version").first()
                )

            context["global_status"] = self.entity.get_global_status
            context["human_status"] = (
                self.entity.entity_level.structure.get_main_entity.get_human_status
            )
            context["scan_status"] = (
                self.entity.entity_level.structure.get_main_entity.get_scan_status
            )
            context["entity"] = self.entity
            context["logo"] = self.entity.entity_level.structure.get_logo_url()
        elif self.structure:
            context["structure"] = self.structure
            context["solver"] = self.entity.is_solver

            diag_evaluations = self.entity.evaluations.exclude(
                sheet__type__slug="evaluation_collaborateurs_360"
            ).exclude(sheet__type__slug="mixity_evaluation_scan")

            if diag_evaluations != None:
                # Cherche l'évaluation en cours si elle existe, sinon prend la dernière par version
                context["diag_evaluation"] = (
                    diag_evaluations.filter(display_version="en-cours").first()
                    or diag_evaluations.order_by("-version").first()
                )

            human_evaluations = self.entity.evaluations.filter(
                sheet__type__slug="evaluation_collaborateurs_360"
            )

            if human_evaluations != None:
                # Cherche l'évaluation en cours si elle existe, sinon prend la dernière par version
                context["human_evaluation"] = (
                    human_evaluations.filter(display_version="en-cours").first()
                    or human_evaluations.order_by("-version").first()
                )

            scan_evaluations = self.entity.evaluations.filter(
                sheet__type__slug="mixity_evaluation_scan"
            )

            if scan_evaluations != None:
                # Cherche l'évaluation en cours si elle existe, sinon prend la dernière par version
                context["scan_evaluation"] = (
                    scan_evaluations.filter(display_version="en-cours").first()
                    or scan_evaluations.order_by("-version").first()
                )

            context["logo"] = self.entity.get_logo_url()
        ordered_entities = []
        for ent in context["accessible_entities"]:
            if (
                ent.parent_entity
                and ent.parent_entity in context["accessible_entities"]
            ):
                index = ordered_entities.index(ent.parent_entity)
                ordered_entities.insert(index + 1, ent)
            else:
                ordered_entities.append(ent)
        context["accessible_entities"] = ordered_entities
        return context


class DashboardHome(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "index.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        response = DashboardAccessMixin.dispatch(
            self, request, no_success_redirect=True, *args, **kwargs
        )
        if response:
            return response
        if not self.entity:
            return redirect(reverse("dashboard:account:update_profile"))
        if (
            self.entity.entity_level.structure.is_solver
            and not self.entity.entity_level.structure.active_subscription_pack
        ):
            return redirect(
                reverse("dashboard:act:solver_solutions", args=[self.entity.slug])
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        segment_tracking(
            self.request.user,
            "Dashboard HomePage",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class NameAnalyzerView(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "name_analyzer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        context["has_evaluation"] = (
            "true" if self.entity.last_global_evaluation else "false"
        )
        context["entity"] = self.entity
        if self.entity.last_global_evaluation:
            context["version"] = (
                self.entity.last_global_evaluation.display_version_slugified
            )
            context["eval_id"] = self.entity.last_global_evaluation.id
        segment_tracking(
            self.request.user,
            "Namsor page d'accueil",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class NameAnalyzerUploadView(NameAnalyzerView):
    template_name = "name_analyzer_upload.html"

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        display_version = self.display_version_from_slug(kwargs["version"])
        context["type"] = kwargs["type"]
        context["currentVersion"] = kwargs["version"]
        context["eval_id"] = Evaluation.objects.filter(entity=self.entity, display_version=display_version).first().id
        segment_tracking(
            self.request.user,
            f"Namsor téléchargement du fichier",
            {
                "structure": self.entity.entity_level.structure.slug,
                "type": kwargs["type"],
            },
        )
        return context
