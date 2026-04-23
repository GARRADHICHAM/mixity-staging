import logging
import os
import datetime
from urllib.parse import urlencode, quote_plus

from django.apps import apps
from django.test import TestCase
from django.test import RequestFactory
from django.conf import settings
from django.utils import timezone

from accounts.models import (
    MixityUser,
    BusinessLine,
    Structure,
    Membership,
    HumanCriteria,
    HumanCriteriaChoice,
)
from collaborator_evaluation.views import CollaboratorEvaluationFillView
from mixity.utils import HiddenPrints
from collaborator_evaluation.test_files import import_20240304_1458_for_testing
from scoring.models import (
    QuestionSheetType,
    Evaluation,
    QuestionSheet,
    Question,
    Collaborator,
    Answer,
    SubAnswer,
)
from subscriptions.models import SubscriptionType, Subscription
from mixity.testing import TestCase


class CollaboratorEvaluationTest(TestCase):
    views = [
        {"view": CollaboratorEvaluationFillView.as_view(), "queries": 11},
    ]

    @classmethod
    def setUpTestData(cls):
        super(CollaboratorEvaluationTest, cls).setUpTestData()

        # Categories
        cls.make_categories()

        # Sheet
        name = "Sheet Type"
        sheet_path = (
            "csv/collaborateurs360/questionnaire_collaborateurs360_20240527_1005.csv"
        )
        sheet, sheet_type = cls.make_sheet_human(name, sheet_path)

        # BusinessLine
        slug = "others"
        name_fr = "Autre - précisez"
        name_en = "Others"
        business_line = cls.make_business_line(slug, name_fr, name_en)

        # User
        username = "toto"
        email = "tt@gg.com"
        password = "12345"
        cls.user = cls.make_user(email, password, username=username)
        username = "wrong_user"
        email = "wrong_user@wrong_user.com"
        wrong_user = cls.make_user(email, password, username=username)

        # Structure
        juridic_name = "My Structure"
        slug = "my_structure"
        workforce = 300
        category = "school"
        cls.s = cls.make_structure(
            juridic_name, slug, workforce, category, business_line
        )
        e_lvl_0 = cls.make_entity_level(cls.s, "Groupe", 0)
        cls.entity = cls.make_entity(cls.s.juridic_name, e_lvl_0, cls.s.workforce)

        # Membership
        cls.make_membership(cls.user, cls.s)
        cls.make_entity_membership(cls.user, cls.entity)

        # Subscription Type
        label = "Mixity Human"
        pme_label = "Mixity Human"
        slug = "human"
        order = 3
        desc = "L’évaluation du sentiment de diversité et d’inclusion de vos collaborateurs (f/h/nb)."
        sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)

        cls.sub = cls.make_subscription(sheet_type, sub_type, cls.s, True)
        sub_pack = cls.make_subscription_pack(datetime.date.today(), cls.s)
        product = cls.make_product(label, "human", sheet_type)
        sub_opt = cls.make_subscription_option(sub_pack, product.slug)

        cls.e = Evaluation.objects.create(
            sheet=sheet, entity=cls.entity, subscription=cls.sub
        )

    def test_logged(self):
        factory = RequestFactory()
        request = factory.get(
            f"",
        )
        request.META["HTTP_HOST"] = "0.0.0.0:8000"
        request.CURRENCY_SYMBOL = "€"
        request.user = self.user
        for view in self.views:
            with self.assertNumQueries(view["queries"]):
                view["view"](request, signed_pk=self.e.signer.sign(self.e.pk)).render()

    def test_send_form(self, num_queries=38):
        factory = RequestFactory()
        request = factory.post(
            f"",
        )
        request.META["HTTP_HOST"] = "0.0.0.0:8000"
        request.CURRENCY_SYMBOL = "€"
        request.user = self.user
        criteria: HumanCriteria = HumanCriteria.objects.create(
            label="test", evaluation=self.e
        )
        criteria1 = HumanCriteriaChoice.objects.create(label="test1", criteria=criteria)
        criteria2 = HumanCriteriaChoice.objects.create(label="test2", criteria=criteria)
        criteria_2: HumanCriteria = HumanCriteria.objects.create(
            label="test_2", evaluation=self.e
        )
        criteria_21 = HumanCriteriaChoice.objects.create(
            label="test_21", criteria=criteria_2
        )
        criteria_22 = HumanCriteriaChoice.objects.create(
            label="test_22", criteria=criteria_2
        )
        q1_choice = Question.objects.get(google_sheets_id=2021001)
        q2_text = Question.objects.get(google_sheets_id=2021048)
        q3_sub_choice = Question.objects.get(google_sheets_id=20210051)
        q3_sub_choice_subquestions = q3_sub_choice.subquestions.all()
        request_data = {
            "uuid": "d0de5cba-c2b7-46b7-8a5a-0c7d8084f477",
            "civility": "man",
            "age": "25_39",
            f"criteria_{criteria.id}": f"{criteria1.id}",
            f"criteria_{criteria_2.id}": f"{criteria_22.id},{criteria_21.id}",
            f"answer_{q2_text.id}": "test text",
            f"answer_{q2_text.id}_consent": "true",
            f"answer_{q1_choice.id}": q1_choice.choices.all()[1].label,
            f"answer_{q3_sub_choice.id}_{q3_sub_choice_subquestions[0].id}_id": q3_sub_choice_subquestions[
                0
            ]
            .choices.all()[0]
            .id,
            f"answer_{q3_sub_choice.id}_{q3_sub_choice_subquestions[1].id}_id": q3_sub_choice_subquestions[
                1
            ]
            .choices.all()[1]
            .id,
            f"answer_{q3_sub_choice.id}_{q3_sub_choice_subquestions[2].id}_id": q3_sub_choice_subquestions[
                2
            ]
            .choices.all()[0]
            .id,
            f"answer_{q3_sub_choice.id}_{q3_sub_choice_subquestions[3].id}_id": q3_sub_choice_subquestions[
                3
            ]
            .choices.all()[1]
            .id,
            f"answer_{q3_sub_choice.id}_{q3_sub_choice_subquestions[4].id}_id": q3_sub_choice_subquestions[
                4
            ]
            .choices.all()[0]
            .id,
            f"answer_{q3_sub_choice.id}_{q3_sub_choice_subquestions[5].id}_id": q3_sub_choice_subquestions[
                5
            ]
            .choices.all()[1]
            .id,
        }
        request.POST = request_data
        with self.assertNumQueries(num_queries):
            CollaboratorEvaluationFillView.as_view()(
                request, signed_pk=self.e.signer.sign(self.e.pk)
            )
        collaborator = Collaborator.objects.get()
        self.assertEqual(collaborator.civility, "man")
        self.assertEqual(collaborator.age, "25_39")
        self.assertTrue(
            collaborator.human_criteria_choices.filter(id=criteria1.id).exists()
        )
        self.assertTrue(
            collaborator.human_criteria_choices.filter(id=criteria_22.id).exists()
        )
        self.assertTrue(
            collaborator.human_criteria_choices.filter(id=criteria_21.id).exists()
        )
        self.assertEqual(
            Answer.objects.get(question=q1_choice).choice.label,
            q1_choice.choices.all()[1].label,
        )
        self.assertEqual(
            Answer.objects.get(question=q1_choice).allow_raw_usage,
            False,
        )
        a2 = Answer.objects.get(question=q2_text)
        self.assertEqual(a2.collaborator_comment, "test text")
        self.assertEqual(a2.allow_raw_usage, True)
        subanswers = Answer.objects.get(question=q3_sub_choice).subanswers.all()
        self.assertEqual(
            subanswers[0].choice_id, q3_sub_choice_subquestions[0].choices.all()[0].id
        )
        self.assertEqual(
            subanswers[1].choice_id, q3_sub_choice_subquestions[1].choices.all()[1].id
        )
        self.assertEqual(
            subanswers[2].choice_id, q3_sub_choice_subquestions[2].choices.all()[0].id
        )
        self.assertEqual(
            subanswers[3].choice_id, q3_sub_choice_subquestions[3].choices.all()[1].id
        )
        self.assertEqual(
            subanswers[4].choice_id, q3_sub_choice_subquestions[4].choices.all()[0].id
        )
        self.assertEqual(
            subanswers[5].choice_id, q3_sub_choice_subquestions[5].choices.all()[1].id
        )

    def test_send_form_twice(self):
        self.test_send_form(38)
        answers_count = Answer.objects.count()
        subanswers_count = SubAnswer.objects.count()
        self.test_send_form(35)
        self.assertEqual(answers_count, Answer.objects.count())
        self.assertEqual(subanswers_count, SubAnswer.objects.count())
        self.assertEqual(Collaborator.objects.count(), 1)

    def test_send_form_without_uuid(self):
        factory = RequestFactory()
        request = factory.post(
            f"",
        )
        request.META["HTTP_HOST"] = "0.0.0.0:8000"
        request.CURRENCY_SYMBOL = "€"
        request.user = self.user
        q2_text = Question.objects.get(google_sheets_id=2021048)
        request_data = {
            "civility": "man",
            "age": "25_39",
            f"answer_{q2_text.id}": "test text",
        }
        request.POST = request_data
        with self.assertNumQueries(11):
            CollaboratorEvaluationFillView.as_view()(
                request, signed_pk=self.e.signer.sign(self.e.pk)
            )
        self.assertEqual(Collaborator.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

    def test_send_form_with_invalid_uuid(self):
        factory = RequestFactory()
        request = factory.post(
            f"",
        )
        request.META["HTTP_HOST"] = "0.0.0.0:8000"
        request.CURRENCY_SYMBOL = "€"
        request.user = self.user
        q2_text = Question.objects.get(google_sheets_id=2021048)
        request_data = {
            "uuid": "wrong-uuid",
            "civility": "man",
            "age": "25_39",
            f"answer_{q2_text.id}": "test text",
        }
        request.POST = request_data
        with self.assertNumQueries(11):
            CollaboratorEvaluationFillView.as_view()(
                request, signed_pk=self.e.signer.sign(self.e.pk)
            )
        self.assertEqual(Collaborator.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

    def test_mandatory_forbidden_tags_and_questions(self):
        with self.assertNumQueries(90):
            self.assertFalse(
                any(
                    q.google_sheets_id == 2021076 for q in self.e.get_questions_human()
                ),
                "Une question avec mandatory tag a été trouvée alors que le tag n'est pas renseigné",
            )
            self.assertTrue(
                any(
                    q.google_sheets_id == 2021001 for q in self.e.get_questions_human()
                ),
                "Une question basique n'a pas été trouvée",
            )
            self.assertTrue(
                any(
                    q.google_sheets_id == 2021076
                    for q in self.e.get_questions_human(criteria_tags=["gender_only"])
                ),
                "Une question avec mandatory tag n'a pas été trouvée alors que le tag est pas renseigné",
            )
            self.assertFalse(
                any(
                    q.google_sheets_id == 2021076
                    for q in self.e.get_questions_human(
                        criteria_tags=["gender_only", "no_gender"]
                    )
                ),
                "Une question avec mandatory tag a été trouvée alors qu'un forbidden tag contradictoire existe",
            )
            self.assertTrue(
                any(
                    q.google_sheets_id == 2021076
                    for q in self.e.get_questions_human(
                        criteria_tags=[], mandatory_question_ids=[2021076]
                    )
                ),
                "Une question avec mandatory question n'a pas été trouvée alors que renseigné",
            )
            self.assertTrue(
                any(
                    q.google_sheets_id == 2021076
                    for q in self.e.get_questions_human(
                        criteria_tags=["no_gender"], mandatory_question_ids=[2021076]
                    )
                ),
                "Une question avec mandatory question n'a pas été trouvée alors que renseigné (tag passé en priorité par erreur ?)",
            )
            self.assertFalse(
                any(
                    q.google_sheets_id == 2021076
                    for q in self.e.get_questions_human(
                        criteria_tags=["gender_only"], forbidden_question_ids=[2021076]
                    )
                ),
                "Une question avec forbidden question a été trouvée",
            )

            self.assertFalse(
                any(
                    q.google_sheets_id == 2021001
                    for q in self.e.get_questions_human(
                        forbidden_question_ids=[2021001]
                    )
                ),
                "Une question avec forbidden question a été trouvée",
            )
            self.assertFalse(
                any(
                    q.google_sheets_id == 2021001
                    for q in self.e.get_questions_human(
                        mandatory_question_ids=[2021001],
                        forbidden_question_ids=[2021001],
                    )
                ),
                "Une question avec forbidden question a été trouvée",
            )
