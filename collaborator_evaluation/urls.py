from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from collaborator_evaluation.views import (
    CollaboratorEvaluationLandingView,
    CollaboratorEvaluationFillView,
    CollaboratorEvaluationEndView,
    HumanSheetApiView,
)

app_name = "collaborator_evaluation"

urlpatterns = [
    path(
        "evaluation/<str:signed_pk>/",
        CollaboratorEvaluationLandingView.as_view(),
        name="collaborator_evaluation_landing",
    ),
    path(
        "evaluation/<str:signed_pk>/fill/",
        CollaboratorEvaluationFillView.as_view(),
        name="collaborator_evaluation_fill",
    ),
    path(
        "evaluation/<str:signed_pk>/sheet/",
        csrf_exempt(HumanSheetApiView.as_view()),
        name="collaborator_evaluation_api",
    ),
    path(
        "evaluation/<str:signed_pk>/thanks/",
        CollaboratorEvaluationEndView.as_view(),
        name="collaborator_evaluation_end",
    ),
]
