from unittest import mock

from django.urls import reverse

from mixity.testing import TestCase
from scoring.models import Evaluation, QuestionSheet, QuestionSheetType
from scoring.views import EvaluationConfirm, EvaluationFill


# La vérification d'abonnement (CanEvaluateMixin) est et l'option d'essai sont neutralisées : seul le contenu de la page est testé ici.
@mock.patch.object(EvaluationFill, "set_trial_cat", staticmethod(lambda evaluation, data: data))
@mock.patch.object(EvaluationConfirm, "test_func", lambda self: True)
class EvaluationConfirmFreshTest(TestCase):
    """Page "Reprendre le questionnaire" d'une entreprise toute neuve (évaluation sans réponse)."""

    @classmethod
    def setUpTestData(cls):
        business_line = cls.make_business_line("bl", "Secteur", "Sector")
        sheet_type = QuestionSheetType.objects.create(slug="mixity_evaluation_diag", name="Diag")
        sheet = QuestionSheet.objects.create(type=sheet_type, slug="diag_sheet", version=0.1)
        structure = cls.make_structure("Entreprise", "entreprise", 100, "Diversity", business_line)
        level = cls.make_entity_level(structure, "Groupe", 0)
        cls.entity = cls.make_entity(structure.juridic_name, level, 100)
        cls.evaluation = Evaluation.objects.create(sheet=sheet, entity=cls.entity, display_version="en-cours")
        cls.owner = cls.make_user("owner@example.com", "pw", username="owner@example.com")
        cls.make_membership(cls.owner, structure)
        cls.outsider = cls.make_user("out@example.com", "pw", username="out@example.com")
        cls.url = reverse("evaluation_confirm", args=[cls.evaluation.pk])

    def test_owner_gets_the_page_even_without_answers(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(str(self.evaluation.pk), response.context["json_formatted"])

    def test_outsider_is_refused_instead_of_crashing(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 403)
