from django.contrib.auth.mixins import LoginRequiredMixin
from django.test import TestCase
from django.urls import get_resolver
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

# Seuls points d'accès de l'API réellement publics (appelés avant connexion).
# Toute nouvelle vue doit exiger une connexion, sauf ajout volontaire à cette liste.
PUBLIC_API_VIEWS = {
    "ApiLogin",
    "ApiDashboardRegister",
    "ApiCountriesList",
    "ApiForgottenPasswordMail",
    "ApiForgottenPasswordChange",
    "ApiCollaboratorLogin",
    "ApiCreateCollaboratorPassword",
    "ApiGetEmail",
}


def routed_api_views():
    views = {}

    def walk(patterns):
        for pattern in patterns:
            if hasattr(pattern, "url_patterns"):
                walk(pattern.url_patterns)
                continue
            callback = pattern.callback
            cls = getattr(callback, "cls", None) or getattr(callback, "view_class", None)
            if isinstance(cls, type) and issubclass(cls, APIView):
                views[cls] = pattern

    walk(get_resolver().url_patterns)
    return views


def is_open_to_anonymous(cls):
    mro = cls.__mro__
    login_required_first = (
        LoginRequiredMixin in mro and mro.index(LoginRequiredMixin) < mro.index(APIView)
    )
    if login_required_first:
        return False
    # liste vide = tout le monde est autorisé
    return not cls.permission_classes or any(
        issubclass(permission, AllowAny) for permission in cls.permission_classes
    )


class ApiPermissionsTest(TestCase):
    def test_only_declared_public_views_are_open(self):
        open_views = {cls.__name__ for cls in routed_api_views() if is_open_to_anonymous(cls)}
        self.assertEqual(open_views, PUBLIC_API_VIEWS)

    def test_anonymous_cannot_call_protected_endpoints(self):
        for url in (
            "/api/update_structure/",
            "/api/get_collaborators/",
            "/api/delete_collaborator/",
            "/api/invite_collaborators/",
            "/api/update_structure_description/",
            "/api/upload_collaborators_csv/",
            "/api/upload_entities_csv/",
            "/api/update_user/",
            "/api/get_user_name/",
        ):
            with self.subTest(url=url):
                response = self.client.post(url, data="{}", content_type="application/json")
                self.assertIn(response.status_code, (302, 401, 403))

    def test_login_endpoint_stays_public(self):
        response = self.client.post(
            "/api/login/",
            data='{"email": "nobody@example.com", "password": "wrong"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_countries_endpoint_stays_public(self):
        self.assertEqual(self.client.get("/api/countries/").status_code, 200)
