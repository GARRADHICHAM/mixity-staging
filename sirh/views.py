import logging
import json
from datetime import datetime, timedelta

from django.utils import timezone

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from rest_framework import viewsets

from mixity.dashboard.views import DashboardStructureViewMixin
from mixity.utils import segment_tracking
from sirh.indicators import ADPIndicatorAdapter
from sirh.models import ADPStatus, ADPSoftware, ADPIndicatorType, ADPCredentials
from sirh.serializers import ADPStatusSerializer
from scoring.mails import send_adp_connection_request
from sirh.services import APIConnection, ADPAdapter

# TODO : facto all views with common instructions


# Create your views here.
class ADPStatusView(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "../../sirh/templates/adp_status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        context["has_evaluation"] = (
            "true" if self.entity.last_global_evaluation else "false"
        )
        context["entity"] = self.entity
        segment_tracking(
            self.request.user,
            "ADP status page",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


# Create your views here.
class ADPRequestView(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "../../sirh/templates/adp_request.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        context["has_evaluation"] = (
            "true" if self.entity.last_global_evaluation else "false"
        )
        context["entity"] = self.entity
        segment_tracking(
            self.request.user,
            "ADP request page",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return (
            self.request.user in self.entity.entity_level.structure.members.all()
            and not ADPStatus.objects.filter(
                Q(entity=self.entity) | Q(structure=self.entity.entity_level.structure)
            ).exists()
        )


class ADPIndicatorsView(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, TemplateView
):
    template_name = "../../sirh/templates/adp_indicators.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["structure"] = self.entity.entity_level.structure
        context["has_evaluation"] = (
            "true" if self.entity.last_global_evaluation else "false"
        )
        context["entity"] = self.entity
        segment_tracking(
            self.request.user,
            "ADP indicators page",
            {"structure": self.entity.entity_level.structure.slug},
        )
        return context

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ADPIndicatorRetrieveAPI(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, View
):
    def get(self, *args, **kwargs):
        return JsonResponse(
            ADPIndicatorAdapter.get_indicator(kwargs["name"], self.entity)
        )

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ADPIndicatorsListAPI(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, View
):
    def get(self, *args, **kwargs):
        return JsonResponse(
            list(
                ADPIndicatorType.objects.filter(
                    adpindicator__entity=self.entity,
                )
                .distinct()
                .order_by("order_num")
                .values("name", "label", "category")
            ),
            safe=False,
        )

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ADPRequestAPI(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, View
):
    template_name = "../../sirh/templates/adp_request.html"

    def get(self, **kwargs):
        return HttpResponse("Nothing to see here...", status=404)

    def post(self, request, **kwargs):
        data = json.loads(request.body.decode("utf-8"))
        ADPStatus.objects.create(
            requested_software=ADPSoftware.objects.get(name=data["software"]),
            request_text=data["text"],
            entity=self.entity,
        )
        send_adp_connection_request(self.request.user, self.entity, self.request)
        return HttpResponse("{}", status=200)

    def test_func(self):
        return (
            self.request.user in self.entity.entity_level.structure.members.all()
            and not ADPStatus.objects.filter(
                Q(entity=self.entity) | Q(structure=self.entity.entity_level.structure)
            ).exists()
        )


class ADPStatusAPI(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = ADPStatusSerializer

    def get_queryset(self):
        return ADPStatus.objects.filter(
            Q(entity=self.entity) | Q(structure=self.entity.entity_level.structure)
        )

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ADPIndicatorsUpdateAPI(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, View
):
    def get(self, *args, **kwargs):
        adp_status = self.entity.adp_status.first()
        try:
            if adp_status.last_updated < (
                timezone.now() - timedelta(days=30 * adp_status.update_frequency)
            ):
                client_id, client_secret = ADPCredentials.objects.get(
                    entity=self.entity
                ).get_credentials()
                client = APIConnection(client_id, client_secret)
                adapter = ADPAdapter(
                    client, structure=self.entity.entity_level.structure
                )
                # @job("default", timeout=3600)
                adapter.gather_data()
        except Exception as e:
            print(f"{e}")
            logging.exception(f"{e}")
        return JsonResponse({})

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()
