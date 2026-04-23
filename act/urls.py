from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers

from act.views import (
    ElearningDetailsView,
    ElearningsListView,
)

app_name = "elearning"

urlpatterns = [
    path("<slug:elearning>/details/", ElearningDetailsView.as_view(), name="details"),
    path("list/", ElearningsListView.as_view(), name="list"),
]
