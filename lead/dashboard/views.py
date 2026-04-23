from django.utils.translation import ugettext_lazy as _
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import TemplateView
from django.urls import reverse
from mixity.dashboard.views import DashboardStructureViewMixin
from mixity.utils import segment_tracking


class Lead(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "lead.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        segment_tracking(
            self.request.user,
            "Piloter Plan Action",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class Overview(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        segment_tracking(
            self.request.user,
            "Piloter Homepage",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)
