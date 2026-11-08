from unittest import mock

from django.urls import reverse

from accounts.models import Membership
from mixity.testing import TestCase
from scoring.models import Evaluation, QuestionSheet, QuestionSheetType


class EvaluationAccessTest(TestCase):
    """validate, open et les téléversements de visuels : réservés aux membres non lecteurs."""

    @classmethod
    def setUpTestData(cls):
        business_line = cls.make_business_line("bl", "Secteur", "Sector")
        sheet_type = QuestionSheetType.objects.create(slug="sheet_type", name="Sheet Type")
        sheet = QuestionSheet.objects.create(type=sheet_type, slug="my_sheet", version=0.1)

        cls.structure = cls.make_structure("Ma société", "ma-societe", 100, "Diversity", business_line)
        level = cls.make_entity_level(cls.structure, "Groupe", 0)
        cls.entity = cls.make_entity(cls.structure.juridic_name, level, 100)
        cls.evaluation = Evaluation.objects.create(
            sheet=sheet, entity=cls.entity, display_version="en-cours"
        )

        other_structure = cls.make_structure("Autre société", "autre", 50, "Diversity", business_line)
        other_level = cls.make_entity_level(other_structure, "Groupe", 0)
        cls.make_entity(other_structure.juridic_name, other_level, 50)

        cls.owner = cls.make_user("owner@example.com", "pw", username="owner@example.com")
        cls.make_membership(cls.owner, cls.structure)
        cls.reader = cls.make_user("reader@example.com", "pw", username="reader@example.com")
        Membership.objects.create(user=cls.reader, structure=cls.structure, is_reader=True)
        cls.outsider = cls.make_user("outsider@example.com", "pw", username="outsider@example.com")
        cls.make_membership(cls.outsider, other_structure)
        cls.staff = cls.make_user("staff@example.com", "pw", username="staff@example.com")
        cls.staff.is_staff = True
        cls.staff.save()

        pk = cls.evaluation.pk
        cls.urls = {
            "validate": reverse("evaluation_validate", args=[pk]),
            "open": reverse("evaluation_open", args=[pk]),
            "footprint": reverse("structure_footprint_upload", args=[pk]),
            "share": reverse("structure_share_upload", args=[pk]),
            "pdf": reverse("structure_pdf_upload", args=[pk]),
            "thumbnail": reverse("social_network_thumbnail_url", args=[pk]),
        }

    def call(self, name):
        url = self.urls[name]
        if name in ("validate", "open"):
            return self.client.get(url)
        return self.client.post(url, {"footprint": "image/png;base64,AAAA"})

    def test_anonymous_is_redirected_to_login(self):
        for name in self.urls:
            with self.subTest(name=name):
                response = self.call(name)
                self.assertEqual(response.status_code, 302)
                self.assertIn("login", response["Location"])

    def test_member_of_another_company_is_refused(self):
        self.client.force_login(self.outsider)
        for name in self.urls:
            with self.subTest(name=name):
                self.assertEqual(self.call(name).status_code, 403)

    def test_reader_is_refused(self):
        self.client.force_login(self.reader)
        for name in self.urls:
            with self.subTest(name=name):
                self.assertEqual(self.call(name).status_code, 403)

    def test_refused_user_cannot_change_the_evaluation(self):
        self.client.force_login(self.outsider)
        with mock.patch.object(Evaluation, "do_user_validation") as validation:
            self.call("validate")
        validation.assert_not_called()

    def test_owner_can_validate_and_open(self):
        self.client.force_login(self.owner)
        with mock.patch.object(Evaluation, "do_user_validation") as validation:
            response = self.call("validate")
        validation.assert_called_once()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.call("open").status_code, 302)

    def test_staff_can_validate(self):
        self.client.force_login(self.staff)
        with mock.patch.object(Evaluation, "do_user_validation"):
            self.assertEqual(self.call("validate").status_code, 302)
