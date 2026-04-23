from django.urls import path

from landing.dashboard.views import (
    DashboardLandingDiagView,
    DashboardLandingHumanView,
    DashboardLandingMeasureView,
    DashboardLandingPilotView,
    DashboardLandingSolverView,
    LandingElearningsView,
)

app_name = "landing"

urlpatterns = [
    # views
    path(
        "diag/landing/",
        DashboardLandingDiagView.as_view(),
        name="landing_diag",
    ),
    path(
        "human/landing/",
        DashboardLandingHumanView.as_view(),
        name="landing_human",
    ),
    path(
        "measure/landing/",
        DashboardLandingMeasureView.as_view(),
        name="landing_measure",
    ),
    path(
        "pilot/landing/",
        DashboardLandingPilotView.as_view(),
        name="landing_pilot",
    ),
    path(
        "solver/landing/",
        DashboardLandingSolverView.as_view(),
        name="landing_solver",
    ),
    path(
        "elearning/landing/", LandingElearningsView.as_view(), name="landing_elearning"
    ),
]
