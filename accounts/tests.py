import datetime
import json
from django.urls import reverse
from django.test import Client
from smart_testing.testcase import TestCaseMixin

from scoring.models import QuestionSheetType, Evaluation, QuestionSheet
from mixity.testing import TestCase


class ManageHumanCriteriaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(ManageHumanCriteriaTest, cls).setUpTestData()
        # Categories
        cls.make_categories()

        # Sheet
        sheet_type = QuestionSheetType.objects.create(
            slug="evaluation_collaborateurs_360",
            name="Sheet Type",
            is_collaborator=True,
        )
        QuestionSheet.objects.create(
            type=sheet_type,
            slug="my_sheet",
            version=0.1,
        )

        # BusinessLine
        slug = "others"
        name_fr = "Autre - précisez"
        name_en = "Others"
        business_line = cls.make_business_line(slug, name_fr, name_en)

        # User
        username = "user"
        email = "user@user.com"
        password = "12345"
        user = cls.make_user(email, password, username=username)
        username = "wrong_user"
        email = "wrong_user@wrong_user.com"
        wrong_user = cls.make_user(email, password, username=username)

        # Structure
        juridic_name = "My Structure"
        slug = "my_structure"
        workforce = 100
        category = "Diversity"
        s = cls.make_structure(juridic_name, slug, workforce, category, business_line)
        e_lvl_0 = cls.make_entity_level(s, "Groupe", 0)
        e = cls.make_entity(s.juridic_name, e_lvl_0, s.workforce)

        # Membership
        cls.make_membership(user, s)
        cls.make_entity_membership(user, e)

        # Subscription Type
        label = "Mixity Human"
        pme_label = "Mixity Human"
        slug = "human"
        order = 3
        desc = "L’évaluation du sentiment de diversité et d’inclusion de vos collaborateurs (f/h/nb)."
        sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)

        cls.sub = cls.make_subscription(sheet_type, sub_type, s, False)
        sub_pack = cls.make_subscription_pack(datetime.date.today(), s)
        product = cls.make_product(label, "human", sheet_type)
        sub_opt = cls.make_subscription_option(sub_pack, product.slug)

        # Attributes
        cls.structure_client = Client()
        cls.structure_client.force_login(user)
        cls.wrong_client = Client()
        cls.wrong_client.force_login(wrong_user)
        cls.s = s
        cls.e = e
        cls.user = user

    def test_create_human_criteria(self):
        criteria = [
            {
                "label": "function",
                "choices": ["one", "two", "three"],
            },
            {
                "label": "color",
                "choices": ["blue", "red", "green", "yellow", "black", "white"],
            },
        ]
        response = self.structure_client.post(
            reverse("structure:manage_criteria", kwargs={"pk": self.s.pk}),
            json.dumps(criteria),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.e.evaluations.first(), None)
        self.sub.is_active = True
        self.sub.save()
        response = self.structure_client.post(
            reverse("structure:manage_criteria", kwargs={"pk": self.s.pk}),
            json.dumps(criteria),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.structure_client.get(
            reverse("home", kwargs={"slug": self.e.slug})
        )
        self.assertContains(response, reverse("home", kwargs={"slug": self.e.slug}))
        self.assertNotEqual(self.e.evaluations.first(), None)
        eval = self.e.last_human_evaluation
        self.assertEqual(eval.human_criteria.count(), 2)
        self.assertEqual(eval.human_criteria.get(label="function").choices.count(), 3)
        self.assertEqual(eval.human_criteria.get(label="color").choices.count(), 6)
        response = self.structure_client.post(
            reverse("structure:manage_criteria", kwargs={"pk": self.s.pk}),
            json.dumps(criteria),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_human_criteria_wrong_user(self):
        criteria = [
            {
                "label": "function",
                "choices": ["one", "two", "three"],
            },
            {
                "label": "color",
                "choices": ["blue", "red", "green", "yellow", "black", "white"],
            },
        ]
        self.sub.is_active = True
        self.sub.save()

        self.assertEqual(self.e.evaluations.first(), None)
        response = self.wrong_client.post(
            reverse("structure:manage_criteria", kwargs={"pk": self.s.pk}),
            json.dumps(criteria),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.e.evaluations.first(), None)


class StructureEvaluationStatusTest(TestCaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(StructureEvaluationStatusTest, cls).setUpClass()
        # Categories
        cls.make_categories()

        # Sheet
        name = "Sheet Type"
        sheet_path = (
            "csv/collaborateurs360/questionnaire_collaborateurs360_20240527_1005.csv"
        )
        cls.sheet, cls.sheet_type = cls.make_sheet_human(name, sheet_path)

        # BusinessLine
        slug = "others"
        name_fr = "Autre - précisez"
        name_en = "Others"
        cls.business_line = cls.make_business_line(slug, name_fr, name_en)

        # Subscription Type
        label = "Mixity Human"
        pme_label = "Mixity Human"
        slug = "human"
        order = 3
        desc = ""
        cls.sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)

    def test_eval_status_none(self):
        juridic_name = "human none"
        slug = "human_none"
        workforce = 100
        category = "Diversity"
        s = self.make_structure(
            juridic_name, slug, workforce, category, self.business_line
        )
        e_lvl_0 = self.make_entity_level(s, "Groupe", 0)
        e = self.make_entity(s.juridic_name, e_lvl_0, s.workforce)
        self.assertEqual(e.get_human_status, "not_started")

    def test_eval_status_not_started(self):
        juridic_name = "human not_started"
        slug = "human_not_started"
        workforce = 100
        category = "Diversity"
        s = self.make_structure(
            juridic_name, slug, workforce, category, self.business_line
        )
        e_lvl_0 = self.make_entity_level(s, "Groupe", 0)
        e = self.make_entity(s.juridic_name, e_lvl_0, s.workforce)
        self.make_subscription(self.sheet_type, self.sub_type, s)
        self.assertEqual(e.get_human_status, "not_started")

    def test_eval_status_in_progress(self):
        juridic_name = "human in_progress"
        slug = "human_in_progress"
        workforce = 100
        category = "Diversity"
        s = self.make_structure(
            juridic_name, slug, workforce, category, self.business_line
        )
        e_lvl_0 = self.make_entity_level(s, "Groupe", 0)
        e = self.make_entity(s.juridic_name, e_lvl_0, s.workforce)
        subscription = self.make_subscription(self.sheet_type, self.sub_type, s)
        self.e = Evaluation.objects.create(
            sheet=self.sheet, entity=e, subscription=subscription
        )
        self.e.is_started = True
        self.e.save()
        self.assertEqual(e.get_human_status, "in_progress")

    def test_eval_status_validate_by_user(self):
        juridic_name = "human validate_by_user"
        slug = "human_validate_by_user"
        workforce = 100
        category = "Diversity"
        s = self.make_structure(
            juridic_name, slug, workforce, category, self.business_line
        )
        e_lvl_0 = self.make_entity_level(s, "Groupe", 0)
        e = self.make_entity(s.juridic_name, e_lvl_0, s.workforce)
        subscription = self.make_subscription(self.sheet_type, self.sub_type, s)
        self.e = Evaluation.objects.create(
            sheet=self.sheet, entity=e, subscription=subscription
        )
        self.e.is_started = True
        self.e.save()
        self.e.is_validated_by_user = True
        self.e.save()
        self.assertEqual(e.get_human_status, "validate_by_user")

    def test_eval_status_validate_by_admin(self):
        juridic_name = "human validate_by_admin"
        slug = "human_validate_by_admin"
        workforce = 100
        category = "Diversity"
        s = self.make_structure(
            juridic_name, slug, workforce, category, self.business_line
        )
        e_lvl_0 = self.make_entity_level(s, "Groupe", 0)
        e = self.make_entity(s.juridic_name, e_lvl_0, s.workforce)
        subscription = self.make_subscription(self.sheet_type, self.sub_type, s)
        self.e = Evaluation.objects.create(
            sheet=self.sheet, entity=e, subscription=subscription
        )
        self.e.is_started = True
        self.e.save()
        self.e.is_validated_by_user = True
        self.e.save()
        self.e.is_validated_by_admin = True
        self.e.save()
        self.assertEqual(e.get_human_status, "validate_by_admin")
