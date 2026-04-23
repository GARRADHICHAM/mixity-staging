from django.urls import path
from lead.dashboard import views
from mixity.dashboard.views_api import ApiUrl

app_name = "lead"

urlpatterns = [
    path("overview/", views.Overview.as_view(), name="overview"),
    path("", views.Lead.as_view(), name="home"),
    path("api/url/", ApiUrl.as_view(), name="api_url"),
    path("overview/api/url/", ApiUrl.as_view(), name="api_overview_url"),
]
