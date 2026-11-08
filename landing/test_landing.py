import os

from django.conf import settings
from django.test import TestCase
from django.utils.html import escapejs

from accounts.models import MixityUser

PAGES = ("diag", "human", "measure", "pilot", "solver")
BUNDLE_DIR = os.path.join(settings.BASE_DIR, "static", "dist", "js")


class LandingPagesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MixityUser.objects.create_user(
            username="visitor@example.com", email="visitor@example.com", password="pw"
        )

    def test_pages_give_the_front_the_marketing_site_address(self):
        self.client.force_login(self.user)
        for name in PAGES:
            with self.subTest(page=name):
                response = self.client.get(f"/{name}/landing/")
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f"var marketing_site_url = '{settings.MARKETING_SITE_URL}'")

    def test_marketing_site_address_is_the_real_website(self):
        self.assertEqual(settings.MARKETING_SITE_URL, "https://www.mixity.io")

    def test_compiled_bundles_no_longer_contain_the_dead_relative_links(self):
        """Les boutons menaient à /evaluation/diag/, /contact/, /pricing/... qui n'existent pas dans l'application."""
        for name in PAGES:
            with self.subTest(page=name):
                path = os.path.join(BUNDLE_DIR, f"dashboardlanding{name}components-1.0.0.js")
                with open(path, encoding="utf-8") as bundle:
                    code = bundle.read()
                for dead in ("/evaluation/diag/", "/evaluation/human/", "'/contact/'", "'/pricing/'", "'/360/'"):
                    self.assertNotIn(dead, code)
                self.assertIn("/empreintes", code)


class SolverLandingSignUpTest(TestCase):
    """« S'inscrire » ouvre le formulaire Devenir solutionneur de la structure, pas le site web."""

    def test_sign_up_button_targets_the_solver_form_of_the_structure(self):
        from mixity.testing import TestCase as MixityTestCase
        from accounts.models import Membership

        business_line = MixityTestCase.make_business_line("bl", "Secteur", "Sector")
        structure = MixityTestCase.make_structure("Société S", "societe-s", 10, "Diversity", business_line)
        entity = MixityTestCase.make_entity("Société S-main", MixityTestCase.make_entity_level(structure, "Groupe", 0), 10)
        user = MixityUser.objects.create_user(username="owner@example.com", email="owner@example.com", password="pw")
        Membership.objects.create(user=user, structure=structure, entity=entity, is_owner=True)

        self.client.force_login(user)
        response = self.client.get("/solver/landing/")
        url = escapejs(f"/{structure.slug}/solver/create/")
        self.assertContains(response, f"var solver_create_url = '{url}'")
