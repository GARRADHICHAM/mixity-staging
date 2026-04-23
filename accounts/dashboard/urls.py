from django.urls import path
from django.contrib.auth import views as auth_views

from accounts.dashboard.views import (
    StructureUpdateView,
    ProfileUpdateView,
    PasswordChangeView,
    CollaboratorRedirectEvaluationView,
    InvitationCreatePasswordView,
    InvitationConfirmedView,
    DashboardRegisterView,
    DashboardMailValidationView,
    DashboardRegisterConfirmedView,
    DashboardRegisterConfirmedRedirectView,
    DashboardRegisterStartView,
    DashboardRegisterStartConfirmedView,
    DashboardLoginView,
)

app_name = "account"

urlpatterns = [
    path(
        "invitation/redirect/<slug:slug>/<str:encrypted_email>/",
        CollaboratorRedirectEvaluationView.as_view(),
        name="collaborator_evaluation_redirect",
    ),
    path(
        "invitation/confirmed/<slug:slug>/<str:encrypted_email>/",
        InvitationConfirmedView.as_view(),
        name="invitation_confirmed",
    ),
    path(
        "invitation/create_password/<slug:slug>/<str:encrypted_email>/",
        InvitationCreatePasswordView.as_view(),
        name="invitation_create_password",
    ),
    path(
        "login",
        DashboardLoginView.as_view(),
        name="dashboard_login",
    ),
    path(
        "register/",
        DashboardRegisterView.as_view(),
        name="dashboard_register",
    ),
    path(
        "register/start/",
        DashboardRegisterView.as_view(),
        name="dashboard_register_start",
        kwargs={"subscription": "start"},
    ),
    path(
        "register_confirmed_redirect/",
        DashboardRegisterConfirmedRedirectView.as_view(),
        name="dashboard_register_confirmed_redirect",
    ),
    path(
        "register/step2/",
        DashboardRegisterConfirmedView.as_view(),
        name="dashboard_register_confirmed",
    ),
    path(
        "register/start/step2/",
        DashboardRegisterStartConfirmedView.as_view(),
        name="dashboard_register_start_confirmed",
    ),
    path(
        "register/start/step3/",
        DashboardRegisterStartView.as_view(),
        name="dashboard_register_start",
    ),
    path(
        "register/mail_validation/",
        DashboardMailValidationView.as_view(),
        name="dashboard_mail_validation",
    ),
    path(
        "<slug:slug>/update/<str:category>/",
        StructureUpdateView.as_view(),
        name="update",
    ),
    path("update_profile/", ProfileUpdateView.as_view(), name="update_profile"),
    path("password-change/", PasswordChangeView.as_view(), name="password_change"),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
