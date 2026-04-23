import json

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.views.generic import TemplateView

from mixity.dashboard.views import DashboardStructureViewMixin, DashboardAccessMixin
from django.utils.translation import ugettext_lazy as _


class DashboardAssessView_PDF(
    LoginRequiredMixin,
    DashboardAccessMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "dashboard/assess_page_PDF.html"

    def post(self, request, *args, **kwargs):
        params = json.loads(request.body.decode("utf-8"))
        print(params)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)
