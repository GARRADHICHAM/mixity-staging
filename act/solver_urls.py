from django.urls import path

from act.views import SolverCreationView

"""
    NOTE
    URLS of act application are divided into :
        - solver_urls : with urls of structures solver
        - customer_urls : with urls of structures customer
"""

app_name = "solver"
urlpatterns = [
    path("create/", SolverCreationView.as_view(), name="create"),  # Sign up as a solver
]
