from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from mixity.dashboard.views import NameAnalyzerView, NameAnalyzerUploadView
from scoring.dashboard.views import (
    DashboardAssessView,
    DashboardAssessTestView,
    DashboardCreateIndicatorView,
    DashboardFiltersView,
    EvaluationSurveyView,
    CollaboratorScoreCardView,
)
from mixity.dashboard.views import DashboardHome
from mixity.dashboard.views_api import ApiUrl
from scoring.pdf_generator.views import DashboardAssessView_PDF

app_name = "dashboard"

urlpatterns = [
    # path("", DashboardHome.as_view(), name="home"),
    # path("<slug:slug>/", DashboardHome.as_view(), name="home"),
    path("<slug:slug>/lead/", include("lead.dashboard.urls")),
    path("<slug:slug>/sirh/", include("sirh.urls")),
    path("<slug:slug>/take-action/", include("act.dashboard.urls")),
    path("<slug:slug>/solver/", include("act.solver_urls", namespace="solver")),
    path("elearning/", include("act.urls", namespace="elearning")),
    path("api/", include("act.urls_api")),
    path("account/", include("accounts.dashboard.urls", namespace="account")),
    path(
        "assess/<slug:slug>/<slug:product>/<str:version>/",
        DashboardAssessView.as_view(),
        name="dashboard_assess",
    ),
    path(
        "<slug:slug>/scan/score-card/",
        CollaboratorScoreCardView.as_view(),
        name="dashboard_assess",
    ),
    path(
        "<slug:slug>/<slug:product>/filters/<str:version>/",
        DashboardFiltersView.as_view(),
        name="evaluation_filters",
    ),
    path(
        "<slug:slug>/create-indicator/",
        DashboardCreateIndicatorView.as_view(),
        name="dashboard_create_indicator",
    ),
    path(
        "<slug:slug>/<slug:product>/assess/<str:version>/",
        DashboardAssessTestView.as_view(),
        name="dashboard_assess_test",
    ),
    path(
        "<slug:slug>/<slug:product>/survey/",
        EvaluationSurveyView.as_view(),
        name="evaluation_survey",
    ),
    path(
        "<slug:slug>/<slug:product>/assess/pdf/",
        DashboardAssessView_PDF.as_view(),
        name="dashboard_assess_pdf",
    ),
    path(
        "<slug:slug>/<slug:product>/assess/<str:version>/api/url/",
        ApiUrl.as_view(),
        name="assess_api_url",
    ),
    path(
        "<slug:slug>/<slug:product>/survey/api/url/",
        ApiUrl.as_view(),
        name="survey_api_url",
    ),
    path(
        "<slug:slug>/scan/score-card/api/url/",
        ApiUrl.as_view(),
        name="survey_api_url",
    ),
    path(
        "<slug:slug>/<slug:product>/filters/<str:version>/api/url/",
        ApiUrl.as_view(),
        name="filters_api_url",
    ),
    path("api/url/", ApiUrl.as_view(), name="api_url"),
    path("<slug:slug>/api/url/", ApiUrl.as_view(), name="api_url"),
    path(
        "<slug:slug>/name-analyzer/",
        NameAnalyzerView.as_view(),
        name="name_analyzer",
    ),
    path(
        "<slug:slug>/name-analyzer/<str:type>/<str:version>",
        NameAnalyzerUploadView.as_view(),
        name="name_analyzer_upload",
    ),
]
