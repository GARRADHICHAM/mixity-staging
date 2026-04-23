from django.contrib.auth import views as auth_views
from django.urls import path
from accounts.views import (
    ResetPasswordViews,
    EmailConfirmationView,
    EmailConfirmationStartView,
    old_user_account_view,
    ResetPasswordConfirmView,
)

app_name = "user"

urlpatterns = [
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("account/", old_user_account_view, name="account"),
    path("email-confirm/", EmailConfirmationView.as_view(), name="email_confirm"),
    path(
        "email-confirm-start/",
        EmailConfirmationStartView.as_view(),
        name="email_confirm_start",
    ),
    path("password-reset/", ResetPasswordViews.as_view(), name="password_reset"),
    path(
        "password-reset/done",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<slug:uidb64>/<slug:token>/",
        ResetPasswordConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # path("user/account/", old_user_account_view, name="old_user_account"),
]
