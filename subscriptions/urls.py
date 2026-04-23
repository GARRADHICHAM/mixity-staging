from django.urls import path

from subscriptions.views import ProductListView, AccountSubsriptionReNew


app_name = "Subscriptions"


urlpatterns = [
    path("offers", ProductListView.as_view(), name="offers"),
    path(
        "offer/<int:offer_pk>/renew",
        AccountSubsriptionReNew.as_view(),
        name="offer_renew",
    ),
]
