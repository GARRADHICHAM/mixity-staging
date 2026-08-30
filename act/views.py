from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http.request import HttpRequest as HttpRequest
from django.http.response import HttpResponse
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView,
    TemplateView,
)

from django.utils.timezone import now
from accounts.models import Structure
from act.models import Solver
from django.utils.translation import ugettext_lazy as _
from mixity.dashboard.views import DashboardStructureViewMixin


# Structure Solver Views
class SolverCreationView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Solver
    template_name = "structure_customer/solver_landing_page.html"
    fields = []

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            "dashboard:act:solver_solutions",
            kwargs={
                "slug": self.get_object().entity_level.first().entities.first().slug
            },
        )

    # Checking if the upcoming solver in an owner of the structure
    def get_object(self, **kwargs):
        return get_object_or_404(Structure, slug=self.kwargs.get("slug"))

    def test_func(self):
        return (
            self.request.user in self.get_object().owners
            and not self.get_object().get_solver
        )

    def handle_no_permission(self):
        structure = self.get_object()
        if self.request.user in structure.owners and structure.get_solver:
            return redirect(
                reverse(
                    "dashboard:act:solver_solutions",
                    kwargs={
                        "slug": structure.entity_level.first().entities.first().slug
                    },
                )
            )
        return super().handle_no_permission()

    # Creating a new solver
    def form_valid(self, form):
        form.instance.structure = self.get_object()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboard_header"] = True
        context["current_page"] = _("Devenir solutionneur")
        context["current_app"] = _("agir")

        return context


class ElearningsListView(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "act_elearnings_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = self.entity
        return context

    def test_func(self):
        return self.entity is None or self.request.user.test_func_rights(self.entity)


class ElearningDetailsView(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "act_elearning_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = self.entity
        return context

    def test_func(self):
        return self.entity is None or self.request.user.test_func_rights(self.entity)
