from act import views, views_api
from rest_framework import routers
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path(
        "<slug:elearning>/elearning/",
        views_api.ApiElearningDetails.as_view(),
        name="api_elearning_details",
    ),
]

router = routers.DefaultRouter()


router.register(r"elearning", views_api.ApiElearning, basename="api_elearning"),


urlpatterns += router.urls
