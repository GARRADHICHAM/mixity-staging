from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import TemplateView
from django.urls import reverse
from mixity.dashboard.views import DashboardStructureViewMixin
from mixity.utils import segment_tracking


class SolutionsList(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "act_solutions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        segment_tracking(
            self.request.user,
            "Agir Chercher une solution",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class FavoritesList(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "act_favorites.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        segment_tracking(
            self.request.user,
            "Agir Mes solutions",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class SolverSolutionsList(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "act_solver_solutions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class BestPracticesManagement(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "act_best_practices_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        segment_tracking(
            self.request.user,
            "Agir Gérer mes bonnes pratiques",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class BestPracticesList(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "act_best_practices.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        segment_tracking(
            self.request.user,
            "Agir Chercher une bonne pratique",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class FavoriteBestPracticesList(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "act_favorite_best_practices.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        segment_tracking(
            self.request.user,
            "Agir Mes bonnes pratiques",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()
