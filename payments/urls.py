# payments/urls.py

from django.urls import path

from . import views

app_name = "payments"
urlpatterns = [
    path("<int:pk>/pay/", views.StructurePaymentView.as_view(), name="pay"),
    path("config/", views.stripe_config),
    path(
        "<int:pk>/create-checkout-session/",
        views.StructureCreateCheckoutSession.as_view(),
    ),
    path("<int:pk>/cancelled/", views.CancelledView.as_view()),
    path("webhook/", views.stripe_webhook),
]
