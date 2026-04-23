import json

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, FormView, TemplateView

from accounts.forms import CollaboratorCriteriaChoiceForm
from accounts.models import Entity
from scoring.views import StructureDataViewMixin
from accounts.vocabularies import CIVILITY_CHOICES, AGE_CHOICES, CAMPUS_CHOICE
from mixity.dashboard.views import DashboardStructureViewMixin, DashboardAccessMixin
from django.utils.translation import ugettext_lazy as _

from mixity.utils import segment_tracking


class DashboardLandingDiagView(
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "dashboard/landing_diag.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class DashboardLandingHumanView(
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "dashboard/landing_human.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class DashboardLandingMeasureView(
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "dashboard/landing_measure.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class DashboardLandingPilotView(
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "dashboard/landing_pilot.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class DashboardLandingSolverView(
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "dashboard/landing_solver.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class LandingElearningsView(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "act_landing_elearnings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        return self.entity is None or self.request.user.test_func_rights(self.entity)
