from django.urls import path
from sirh.views import (
    ADPStatusView,
    ADPStatusAPI,
    ADPRequestView,
    ADPRequestAPI,
    ADPIndicatorsView,
    ADPIndicatorRetrieveAPI,
    ADPIndicatorsListAPI,
    ADPIndicatorsUpdateAPI,
)
from rest_framework import routers


app_name = "sirh"
urlpatterns = [
    path(
        "status/",
        ADPStatusView.as_view(),
        name="adp_status",
    ),
    path(
        "request/",
        ADPRequestView.as_view(),
        name="adp_request",
    ),
    path(
        "indicators/",
        ADPIndicatorsView.as_view(),
        name="adp_indicators",
    ),
    path(
        "api/indicator-retrieve/<str:name>/",
        ADPIndicatorRetrieveAPI.as_view(),
        name="adp_indicator_retrieve_api",
    ),
    path(
        "api/indicators-list/",
        ADPIndicatorsListAPI.as_view(),
        name="adp_indicator_list",
    ),
    path(
        "api/request/",
        ADPRequestAPI.as_view(),
        name="adp_request_api",
    ),
    path(
        "api/indicators-update/",
        ADPIndicatorsUpdateAPI.as_view(),
        name="adp_indicators_update_api",
    ),
]
router = routers.DefaultRouter()
router.register("api/status", ADPStatusAPI, "adp_status_api")
urlpatterns += router.urls
