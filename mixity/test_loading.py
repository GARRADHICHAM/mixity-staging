import os

from django.conf import settings
from django.test import SimpleTestCase

BUNDLES = os.path.join(settings.BASE_DIR, "static", "dist", "js")

# Pages dont le texte « Chargement » a été remplacé par l'indicateur animé (mixity/dashboard/js/includes/Loading.js)
PAGES_WITH_LOADER = (
    "dashboardhomecomponents",
    "leadcomponents",
    "overviewleadcomponents",
    "assessdashboardhomecomponents",
    "evaluationcriteriascomponents",
    "evaluationsurveycomponents",
    "actsolutionscomponents",
    "dashboardlandingdiagcomponents",
    "dashboardlogincomponents",
    "dashboardregistercomponents",
)


def read_bundle(name):
    with open(os.path.join(BUNDLES, f"{name}-1.0.0.js"), encoding="utf-8") as bundle:
        return bundle.read()


class LoadingIndicatorTest(SimpleTestCase):
    def test_compiled_pages_contain_the_animated_loader(self):
        for name in PAGES_WITH_LOADER:
            with self.subTest(bundle=name):
                code = read_bundle(name)
                self.assertIn("mx-loading__ring", code)
                self.assertIn("mx-loading-spin", code)

    def test_home_page_no_longer_asks_the_server_for_its_own_address(self):
        """La page d'accueil prend l'adresse de la page (même protocole) : un aller-retour en moins, sans https en dur."""
        code = read_bundle("dashboardhomecomponents")
        self.assertNotIn("api/url/", code)
        self.assertIn("location.protocol", code)
