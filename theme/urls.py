from django.conf import settings
from django.urls import path, include
from django.views.generic import TemplateView


class StyleguidePageView(TemplateView):
    template_name = "styleguide.html"


app_name = "Theme"

urlpatterns = [
    path("styleguide/", StyleguidePageView.as_view(), name="styleguide"),
]
