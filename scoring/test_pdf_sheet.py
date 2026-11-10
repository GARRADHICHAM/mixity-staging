from unittest import mock

from django.urls import resolve, reverse

from mixity.testing import TestCase
from scoring.models import Evaluation, QuestionSheet, QuestionSheetType


class EvaluationPdfSheetTest(TestCase):
    """Bouton PDF des résultats : fichier stocké s'il existe, sinon régénération au lieu d'un lien cassé."""

    @classmethod
    def setUpTestData(cls):
        business_line = cls.make_business_line("bl", "Secteur", "Sector")
        sheet_type = QuestionSheetType.objects.create(slug="sheet_type", name="Sheet Type")
        sheet = QuestionSheet.objects.create(type=sheet_type, slug="my_sheet", version=0.1)
        cls.structure = cls.make_structure("Ma société", "ma-societe", 100, "Diversity", business_line)
        level = cls.make_entity_level(cls.structure, "Groupe", 0)
        cls.entity = cls.make_entity(cls.structure.juridic_name, level, 100)
        cls.evaluation = Evaluation.objects.create(
            sheet=sheet, entity=cls.entity, display_version="2021-mai", pdf_sheet_fr="media/pdf_sheets/old.pdf"
        )
        cls.owner = cls.make_user("owner@example.com", "pw", username="owner@example.com")
        cls.make_membership(cls.owner, cls.structure)

        other = cls.make_structure("Autre", "autre", 50, "Diversity", business_line)
        cls.make_entity(other.juridic_name, cls.make_entity_level(other, "Groupe", 0), 50)
        cls.outsider = cls.make_user("outsider@example.com", "pw", username="outsider@example.com")
        cls.make_membership(cls.outsider, other)

        cls.url = reverse("pdf_sheet_download", args=[cls.evaluation.pk, "fr"])

    def test_stored_pdf_is_served(self):
        self.client.force_login(self.owner)
        with mock.patch("scoring.views.pdf_sheet_available", return_value=True), mock.patch(
            "scoring.views.regenerate_pdf_sheet_with_job"
        ) as job:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("old", response["Location"])
        job.delay.assert_not_called()

    def test_missing_pdf_is_regenerated(self):
        self.client.force_login(self.owner)
        with mock.patch("scoring.views.pdf_sheet_available", return_value=False), mock.patch(
            "scoring.views.regenerate_pdf_sheet_with_job"
        ) as job:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/assess/ma-societe/diag/"))
        args = job.delay.call_args[0]
        self.assertEqual((args[0], args[1], args[4]), (self.evaluation.pk, "fr", "owner@example.com"))

    def test_outsider_refused(self):
        self.client.force_login(self.outsider)
        with mock.patch("scoring.views.regenerate_pdf_sheet_with_job") as job:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        job.delay.assert_not_called()

    def test_pdf_page_route_not_taken_for_a_version(self):
        self.assertEqual(resolve("/ma-societe/diag/assess/pdf/").url_name, "dashboard_assess_pdf")
