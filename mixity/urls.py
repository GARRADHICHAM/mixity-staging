from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from django.views.i18n import JavaScriptCatalog
from rest_framework import routers

from accounts.api_views import DiversityLabelViewSet
from mixity.dashboard.views import DashboardHome
from scoring.dashboard.views import DashboardCreateIndicatorView
from mixity.logentries_webhook import logentries_webhook
from mixity.sentry_webhook import sentry_webhook
from mixity.views import (
    FAQPageView,
    GoogleSheetsDataCheckView,
    QuestionTypeGeneratorView,
    NamsorApiUsageView,
    OpenAIApiView,
)

js_info_dict = {
    "domain": "djangojs",
}

router = routers.DefaultRouter()
router.register(r"labels", DiversityLabelViewSet)
urlpatterns = [
    # For translations in javascript pages
    path(
        "jsi18n/", JavaScriptCatalog.as_view(**js_info_dict), name="javascript-catalog"
    ),
    # Payments pages
    path("payments/", include("payments.urls", namespace="payments")),
    path("invoices/", include("invoices.urls", namespace="invoices")),
    # Admin pages
    path(settings.ADMIN_DIRECTORY + r"/rq/", include("django_rq.urls")),
    path(settings.ADMIN_DIRECTORY + r"/", admin.site.urls),
    path("api/", include(router.urls)),
    # Private/Login pages
    path("structure/", include("accounts.structure_urls", namespace="structure")),
    path("user/", include("accounts.user_urls", namespace="user")),
    # Public pages
    path("", DashboardHome.as_view(), name="home"),
    path("faq/", FAQPageView.as_view(), name="faq"),
    path("scoring/", include("scoring.urls")),
    path("accounts/", include("allauth.urls")),
    path("subscriptions/", include("subscriptions.urls", namespace="subscription")),
    path(
        "collaborator/",
        include("collaborator_evaluation.urls", namespace="collaborator"),
    ),
    path("", include("mixity.dashboard.urls", namespace="dashboard")),
    path("", include("landing.dashboard.urls", namespace="landing")),
    path(
        "create-indicator/",
        DashboardCreateIndicatorView.as_view(),
        name="create_indicator",
    ),
    path("api/", include("accounts.dashboard.urls_api")),
    path("api/", include("mixity.dashboard.urls_api")),
    path("<slug:slug>/api/", include("mixity.dashboard.urls_api")),
    path(
        "<slug:slug>/<slug:product>/api/",
        include("mixity.dashboard.urls_api"),
    ),
    path("open-ai-api/", OpenAIApiView.as_view(), name="open_ai_api"),
    path(
        "namsor-api-usage/",
        csrf_exempt(NamsorApiUsageView.as_view()),
        name="namsor_api_usage",
    ),
    path("<slug:slug>/", DashboardHome.as_view(), name="home"),
    path(
        "google-sheets-data-check/",
        csrf_exempt(GoogleSheetsDataCheckView.as_view()),
        name="google_sheets_data_check",
    ),
    path(
        "question-type-generator/",
        csrf_exempt(QuestionTypeGeneratorView.as_view()),
        name="question_type_generator",
    ),
    path("sentry-webhook/", sentry_webhook, name="sentry_webhook"),
    path("logentries-webhook/", logentries_webhook, name="logentries-webhook"),
]


if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("theme/", include("theme.urls", namespace="theme")),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "mixity"
