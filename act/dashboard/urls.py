from django.urls import path
from act.dashboard import views
from mixity.dashboard.views_api import ApiUrl

app_name = "act"

urlpatterns = [
    path("search-solutions/", views.SolutionsList.as_view(), name="search_solutions"),
    path("favorites/", views.FavoritesList.as_view(), name="favorites_solutions"),
    path("my-solutions/", views.SolverSolutionsList.as_view(), name="solver_solutions"),
    path(
        "my-best-practices/",
        views.BestPracticesManagement.as_view(),
        name="best_practices_management",
    ),
    path(
        "search-best-practices/",
        views.BestPracticesList.as_view(),
        name="search_best_practices",
    ),
    path(
        "favorites-best-practices/",
        views.FavoriteBestPracticesList.as_view(),
        name="favorites_best_practices",
    ),
    path("search-solutions/api/url/", ApiUrl.as_view(), name="api_url"),
    path("favorites/api/url/", ApiUrl.as_view(), name="api_url_fav"),
    path("my-solutions/api/url/", ApiUrl.as_view(), name="api_url_solver"),
    path(
        "my-best-practices/api/url/",
        ApiUrl.as_view(),
        name="api_url_best_practices_management",
    ),
    path(
        "search-best-practices/api/url/",
        ApiUrl.as_view(),
        name="api_url_best_practices",
    ),
    path(
        "favorites-best-practices/api/url/",
        ApiUrl.as_view(),
        name="api_url_fav_best_practices",
    ),
]
