import datetime
import importlib
import logging
import os
import openpyxl as opx
from django.apps import apps
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

from mixity.testing import TestCase
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from accounts.models import (
    Structure,
    MixityUser,
    Membership,
    BusinessLine,
    HumanCriteria,
    HumanCriteriaChoice,
)

from scoring.models import do_update_scoring, QuestionTag
from scoring.views import StructureDetailPublicView
from mixity.utils import HiddenPrints, evaluation_random_generator
from scoring.importsheets import import_20240527_1005
from scoring.models import (
    Question,
    Evaluation,
    SubCategory,
    Category,
    QuestionSheet,
    QuestionSheetType,
    SubQuestion,
    SubAnswer,
    Answer,
    Collaborator,
    Aim,
    ScoreCategory,
    Comment,
    Choice,
)
from django.conf import settings
from django.test import RequestFactory
from smart_testing.testcase import TestCaseMixin

from scoring.views import EvaluationFill, EvaluationCategoryConfirm
from subscriptions.models import SubscriptionType, Subscription
from django.test import Client
from django.core import management


logger = logging.getLogger(__name__)


def compare_excel_files(file1, file2):
    """
    NOTE : Function that compares 2 excel files using openpyxl library
    """

    # Workbooks
    wk1 = opx.load_workbook(file1)
    wk2 = opx.load_workbook(file2)

    # Worksheets
    sh1 = wk1.active
    sh2 = wk2.active

    # Rows and columns
    r1, c1 = sh1.max_row, sh1.max_column
    r2, c2 = sh2.max_row, sh2.max_column

    # Rows and columns conditions
    rows_condition = r1 != r2
    columns_condition = c1 != c2

    # Comparing rows and columns length
    if rows_condition and columns_condition:
        raise AssertionError(
            f"Numbers of rows and columns are not equal :\n - Rows : {r1}, {r2}\n - Columns : {c1}, {c2}"
        )
    elif columns_condition:
        raise AssertionError(f"Numbers of columns are not equal: {c1}, {c2}")
    elif rows_condition:
        raise AssertionError(f"Numbers of rows are not equal: {r1}, {r2}")

    # Comparing values
    are_equal = True
    if c1 == 5:
        # NB : in openpyxl indexes start from 1 not 0
        for i in range(1, r1 + 1):  # Iterating on rows
            for j in range(1, c1 + 1):  # Iterating on columns
                v1 = sh1.cell(i, j).value
                v2 = sh2.cell(i, j).value
                if v1 != v2:
                    are_equal = False
                    logger.error(
                        f"### col {j} row {i}\n >>> expected: {v2!r}\n >>> results : {v1!r}"
                    )
    else:
        raise AssertionError(f"Number of columns is more than 4: {c1}")
    return are_equal


class RatioSubAnswerTest(TestCase):
    def setUp(self):
        pass

    def test_mean_score(self):
        c = Category.objects.create(
            name="My category", slug="my_category", weight_index=1
        )
        sb = SubCategory.objects.create(
            name="My subcategory", short_name="My Sub", slug="my_sub"
        )
        sb.categories.add(c)
        sheet_type = QuestionSheetType.objects.create(
            slug="sheet_type", name="Sheet Type"
        )
        sheet = QuestionSheet.objects.create(
            type=sheet_type,
            slug="my_sheet",
            version=0.1,
        )
        businessLine = BusinessLine.objects.create(
            slug="others",
            name_fr="Autre - précisez",
            name_en="Others",
        )
        s = Structure.objects.create(
            juridic_name="My Structure",
            slug="my_structure",
            workforce=100,
            category="Diversity",
            business_line=businessLine,
        )
        e_lvl_0 = self.make_entity_level(s, "Groupe", 0)
        entity = self.make_entity(s.juridic_name, e_lvl_0, s.workforce)
        e = Evaluation.objects.create(sheet=sheet, entity=entity)
        e2 = Evaluation.objects.create(sheet=sheet, entity=entity)
        questions = list()
        questions.append(
            Question.objects.create(
                google_sheets_id=1,
                label="My Question",
                subcategory=sb,
                category=c,
                type="valeur",
            )
        )
        questions.append(
            Question.objects.create(
                google_sheets_id=2,
                label="My Question",
                subcategory=sb,
                category=c,
                type="subquestions",
            )
        )
        questions.append(
            Question.objects.create(
                google_sheets_id=3,
                label="My Question",
                subcategory=sb,
                category=c,
                type='subquestions_json_{"mode": "ratio-questions","questions": ["1","2_0","2_1"]}',
            )
        )
        SubQuestion.objects.create(question=questions[1], label="Oui", order=0)
        SubQuestion.objects.create(question=questions[1], label="Non", order=1)

        SubQuestion.objects.create(question=questions[2], label="Oui", order=0)
        SubQuestion.objects.create(question=questions[2], label="Non", order=1)
        for q in questions:
            q.sheets.add(sheet)
        e.generate_answers()
        e2.generate_answers()
        e.answers.filter(question__google_sheets_id=1).update(value=20)
        answer = e.answers.get(question__google_sheets_id=2)
        SubAnswer.objects.create(
            subquestion=questions[1].subquestions.all()[0], answer=answer, value=22
        )
        SubAnswer.objects.create(
            subquestion=questions[1].subquestions.all()[1], answer=answer, value=31
        )

        answer = e.answers.get(question__google_sheets_id=3)
        SubAnswer.objects.create(
            subquestion=questions[2].subquestions.all()[0], answer=answer, value=30
        )
        SubAnswer.objects.create(
            subquestion=questions[2].subquestions.all()[1], answer=answer, value=51
        )
        subanswers2 = answer.subanswers.order_by("subquestion__order")

        e2.answers.filter(question__google_sheets_id=1).update(value=90)

        answer = e2.answers.get(question__google_sheets_id=2)
        SubAnswer.objects.create(
            subquestion=questions[1].subquestions.all()[0], answer=answer, value=24
        )
        SubAnswer.objects.create(
            subquestion=questions[1].subquestions.all()[1], answer=answer, value=33
        )

        answer = e2.answers.get(question__google_sheets_id=3)
        SubAnswer.objects.create(
            subquestion=questions[2].subquestions.all()[0], answer=answer, value=60
        )
        SubAnswer.objects.create(
            subquestion=questions[2].subquestions.all()[1], answer=answer, value=40
        )
        do_update_scoring(
            e.pk, update_choices=True, update_comments=False, update_categories=True
        )
        self.assertEqual(round(subanswers2[0].get_value_from_json_params, 0), 41)
        self.assertEqual(round(subanswers2[1].get_value_from_json_params, 0), 70)
        self.assertEqual(round(subanswers2[0].get_mean_score, 0), 41)


class HumanComputeTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(HumanComputeTest, cls).setUpClass()
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

        # Structure
        juridic_name = "My Structure"
        slug = "my_structure"
        workforce = 100
        category = "Diversity"
        s = cls.make_structure(juridic_name, slug, workforce, category, business_line)
        e_lvl_0 = cls.make_entity_level(s, "Groupe", 0)
        entity = cls.make_entity(s.juridic_name, e_lvl_0, s.workforce)

        # Attributes
        e = cls.e = Evaluation.objects.create(sheet=sheet, entity=entity)
        e2 = cls.e2 = Evaluation.objects.create(sheet=sheet, entity=entity)
        cls.c1 = Collaborator.objects.create(evaluation=e)
        cls.c2 = Collaborator.objects.create(evaluation=e)
        cls.c3 = Collaborator.objects.create(evaluation=e2)

    def test_simple_question(self):
        simple_question = Question.objects.get(google_sheets_id=2021001)

        a = Answer.objects.create(
            question=simple_question,
            choice=simple_question.choices.first(),
            evaluation=self.e,
            collaborator=self.c1,
        )
        Answer.objects.create(
            question=simple_question,
            choice=simple_question.choices.all()[1],
            evaluation=self.e,
            collaborator=self.c2,
        )
        Answer.objects.create(
            question=simple_question,
            choice=simple_question.choices.first(),
            evaluation=self.e2,
            collaborator=self.c3,
        )
        queryset = Collaborator.objects.filter(evaluation_id=self.e.id)
        computed_value = a.get_computed_value(
            self.e, param='{"type":"rate_choice_total"}', queryset=queryset
        )
        self.assertEqual(round(computed_value[0][0]["value"], 0), 50)
        self.assertEqual(round(computed_value[1][0]["value"], 0), 50)
        self.assertEqual(round(computed_value[2][0]["value"], 0), 50)

        computed_value = a.get_computed_value(
            self.e, param='{"type":"count_choice"}', queryset=queryset
        )
        self.assertEqual(round(computed_value[0][0]["value"], 0), 1)
        self.assertEqual(round(computed_value[1][0]["value"], 0), 1)
        self.assertEqual(round(computed_value[2][0]["value"], 0), 1)

    def test_subanswer_question(self):
        question = Question.objects.get(google_sheets_id=2021002)

        test_dict = [[1, 1, 1], [0, 1, 0], [1, 0, 1]]

        a1 = Answer.objects.create(
            question=question,
            evaluation=self.e,
            collaborator=self.c1,
        )
        a2 = Answer.objects.create(
            question=question,
            evaluation=self.e,
            collaborator=self.c2,
        )
        a3 = Answer.objects.create(
            question=question,
            evaluation=self.e2,
            collaborator=self.c3,
        )
        for i in range(0, 3):
            sq = SubQuestion.objects.filter(question=question)[i]
            SubAnswer.objects.create(answer=a1, subquestion=sq, value=test_dict[0][i])
            SubAnswer.objects.create(answer=a2, subquestion=sq, value=test_dict[1][i])
            SubAnswer.objects.create(answer=a3, subquestion=sq, value=test_dict[2][i])

        queryset = Collaborator.objects.filter(evaluation_id=self.e.id)

        computed_value = a1.get_computed_value(
            self.e, param='{"type":"rate_subanswers"}', queryset=queryset
        )
        self.assertEqual(round(computed_value[0][0]["value"], 0), 50)
        self.assertEqual(round(computed_value[1][0]["value"], 0), 50)
        self.assertEqual(round(computed_value[2][0]["value"], 0), 50)

        self.assertEqual(round(computed_value[0][0]["value"], 0), 50)
        self.assertEqual(round(computed_value[0][1]["value"], 0), 100)
        self.assertEqual(round(computed_value[0][2]["value"], 0), 50)

    def test_subanswer_choice_question(self):
        question = Question.objects.get(google_sheets_id=2021009)

        test_dict = [[1, 2, 1], [0, 1, 0], [1, 2, 1]]

        a1 = Answer.objects.create(
            question=question,
            evaluation=self.e,
            collaborator=self.c1,
        )
        a2 = Answer.objects.create(
            question=question,
            evaluation=self.e,
            collaborator=self.c2,
        )
        a3 = Answer.objects.create(
            question=question,
            evaluation=self.e2,
            collaborator=self.c3,
        )
        for i in range(0, 3):
            sq = SubQuestion.objects.filter(question=question)[i]
            SubAnswer.objects.create(
                answer=a1, subquestion=sq, choice=sq.choices.all()[test_dict[0][i]]
            )
            SubAnswer.objects.create(
                answer=a2, subquestion=sq, choice=sq.choices.all()[test_dict[1][i]]
            )
            SubAnswer.objects.create(
                answer=a3, subquestion=sq, choice=sq.choices.all()[test_dict[2][i]]
            )

        queryset = Collaborator.objects.filter(evaluation_id=self.e.id)

        computed_value = a1.get_computed_value(
            self.e, param='{"type":"rate_subanswers_choice_count"}', queryset=queryset
        )
        self.assertEqual(round(computed_value[0][0]["choices"][0]["value"], 0), 50)
        self.assertEqual(round(computed_value[0][0]["choices"][1]["value"], 0), 50)
        self.assertEqual(round(computed_value[0][0]["choices"][2]["value"], 0), 0)
        self.assertEqual(round(computed_value[0][1]["choices"][0]["value"], 0), 0)
        self.assertEqual(round(computed_value[0][1]["choices"][1]["value"], 0), 50)
        self.assertEqual(round(computed_value[0][1]["choices"][2]["value"], 0), 50)


# class GenerateAnswersTest(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super(GenerateAnswersTest, cls).setUpClass()
#         # Categories
#         cls.make_categories()

#         # Sheet
#         name = "Sheet Type"
#         sheet_path = "csv/startflash/questionnaire_startflash_20240527_1005.csv"
#         sheet, sheet_type = cls.make_sheet_start(name, sheet_path)

#         # BusinessLine
#         slug = "others"
#         name_fr = "Autre - précisez"
#         name_en = "Others"
#         business_line = cls.make_business_line(slug, name_fr, name_en)

#         # Structure
#         juridic_name = "My Structure"
#         slug = "my_structure"
#         workforce = 100
#         category = "Diversity"
#         s = cls.make_structure(juridic_name, slug, workforce, category, business_line)
#         e_lvl_0 = cls.make_entity_level(s, "Groupe", 0)
#         entity = cls.make_entity(s.juridic_name, e_lvl_0, s.workforce)

#         # User
#         u = cls.make_common_user()

#         # Subscription Type
#         label = "Mixity Start"
#         pme_label = "Mixity Start"
#         slug = "mixity_start"
#         order = 4
#         desc = "L'évaluation instantanée pour débuter votre politique de diversité et inclusion"
#         sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)
#         # Subscription
#         subscription = cls.make_subscription(sheet_type, sub_type, s)
#         sub_pack = cls.make_subscription_pack(datetime.date.today(), s)
#         product = cls.make_product(label, slug, sheet_type)
#         sub_opt = cls.make_subscription_option(sub_pack, product.slug)

#         # Membership
#         cls.make_membership(u, s)
#         cls.make_entity_membership(u, entity)

#         # Attributes
#         cls.e = Evaluation.objects.create(
#             sheet=sheet, entity=entity, subscription=subscription
#         )
#         cls.user = u

#     def test_generate_answer(self):
#         question = self.e.get_questions[0]
#         a = Answer(
#             question=question,
#             evaluation=self.e,
#         )
#         a.display = not question.public_display_default
#         a.save()
#         self.e.generate_answers()
#         a.refresh_from_db()
#         self.assertEqual(not question.public_display_default, a.display)
#         self.assertEqual(len(self.e.get_questions), self.e.answers.count())


# class EvaluationGetAimsTest(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super(EvaluationGetAimsTest, cls).setUpClass()
#         # Categories
#         cls.make_categories()

#         # Sheet
#         name = "Sheet Type"
#         sheet_path = "csv/startflash/questionnaire_startflash_20240527_1005.csv"
#         sheet, sheet_type = cls.make_sheet_start(name, sheet_path)

#         # BusinessLine
#         slug = "others"
#         name_fr = "Autre - précisez"
#         name_en = "Others"
#         business_line = cls.make_business_line(slug, name_fr, name_en)

#         # Structure
#         juridic_name = "My Structure"
#         slug = "my_structure"
#         workforce = 100
#         category = "Diversity"
#         s = cls.make_structure(juridic_name, slug, workforce, category, business_line)
#         e_lvl_0 = cls.make_entity_level(s, "Groupe", 0)
#         cls.entity = cls.make_entity(s.juridic_name, e_lvl_0, s.workforce)

#         # User
#         u = cls.make_common_user()

#         # Subscription Type
#         label = "Mixity Start"
#         pme_label = "Mixity Start"
#         slug = "mixity_start"
#         order = 4
#         desc = "L'évaluation instantanée pour débuter votre politique de diversité et inclusion"
#         sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)
#         # Subscription
#         cls.make_subscription(sheet_type, sub_type, s)
#         sub_pack = cls.make_subscription_pack(datetime.date.today(), s)
#         product = cls.make_product(label, slug, sheet_type)
#         sub_opt = cls.make_subscription_option(sub_pack, product.slug)

#         # Membership
#         cls.make_membership(u, s)

#         # Attributes
#         cls.e = Evaluation.objects.create(sheet=sheet, entity=cls.entity)
#         cls.e.generate_answers()
#         cls.user = u

#     def test_get_aims(self):
#         answers = self.e.answers.filter(question__category__slug="disability")
#         i = 7
#         aims_created = []
#         for answer in answers:
#             if (
#                 not "qcm" in answer.question.type
#                 and not "subquestion" in answer.question.type
#             ):
#                 answer.value = 15
#             elif "qcm" in answer.question.type:
#                 answer.choice = answer.question.choices.first()
#             answer.save()
#             priority_value = 0
#             if answer.evaluation.aims.count() >= 3:
#                 priority_value = 1
#             if answer.evaluation.aims.count() >= 5:
#                 priority_value = 2
#             aims_created.append(
#                 Aim.objects.create(
#                     answer=answer,
#                     subcategory=answer.question.subcategory,
#                     category=answer.question.category,
#                     description_fr="test recommendation",
#                     description_en="try recommendation",
#                     evaluation=answer.evaluation,
#                     order=i,
#                     priority_value=priority_value,
#                     is_auto_generate=False,
#                 )
#             )
#             i -= 1
#         self.assertEqual(
#             self.e.aims.filter(answer__question__category__slug="disability").count(),
#             9,
#         )
#         aims, aims_count = self.e.scores_categories.get(
#             category__slug="disability"
#         ).get_aims
#         self.assertEqual(aims_count, 6)
#         self.assertEqual(aims[0][0], "À mettre en place")
#         self.assertEqual(aims[0][1], aims_created[2])
#         self.assertEqual(aims[1][0], "")
#         self.assertEqual(aims[1][1], aims_created[1])
#         self.assertEqual(aims[3][0], "À formaliser")
#         self.assertEqual(aims[3][1], aims_created[4])
#         self.assertEqual(aims[5][0], "À renforcer")
#         self.assertEqual(aims[5][1], aims_created[8])


def generate_global_evaluation(cls):
    # Categories
    cls.make_categories()

    # Sheet
    name = "Sheet Type"
    sheet_path = "csv/society2021/questionnaire_society2021_20240527_1005.csv"
    sheet, sheet_type = cls.make_sheet_global(name, sheet_path)

    # BusinessLine
    slug = "others"
    name_fr = "Autre - précisez"
    name_en = "Others"
    business_line = cls.make_business_line(slug, name_fr, name_en)

    # Structure
    juridic_name = "My Structure"
    slug = "my_structure"
    workforce = 100
    category = "Diversity"
    s = cls.make_structure(juridic_name, slug, workforce, category, business_line)
    e_lvl_0 = cls.make_entity_level(s, "Groupe", 0)
    entity = cls.make_entity(s.juridic_name, e_lvl_0, s.workforce)

    # User
    u = cls.make_common_user()

    # Subscription Type
    label = "Mixity Diag"
    pme_label = "Mixity Global"
    slug = "global"
    order = 4
    desc = ""
    sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)
    # Subscription
    subscription = cls.make_subscription(sheet_type, sub_type, s)
    sub_pack = cls.make_subscription_pack(datetime.date.today(), s)
    product = cls.make_product(label, "diag", sheet_type)
    sub_opt = cls.make_subscription_option(sub_pack, product.slug)

    # Membership
    cls.make_membership(u, s)
    cls.make_entity_membership(u, entity)

    # Attributes
    cls.e = Evaluation.objects.create(
        sheet=sheet, entity=entity, subscription=subscription
    )
    cls.e.generate_answers()
    cls.user = u
    cls.entity = entity
    cls.scoring_client = Client()
    cls.scoring_client.force_login(cls.user)


class EvaluationFillTest(TestCaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(EvaluationFillTest, cls).setUpClass()
        cls.e = None
        cls.user = None
        cls.scoring_client = None
        generate_global_evaluation(cls=cls)

    @csrf_exempt
    def post_form(self, path, args, data):
        path = reverse(path, args=args)
        response = self.scoring_client.post(
            path,
            data=data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "None")  # None = same url

    @csrf_exempt
    def get_page(self, path, args):
        path = reverse(path, args=args)
        response = self.scoring_client.get(
            path,
        )
        self.assertEqual(response.status_code, 200)

    @csrf_exempt
    def test_post_subanswers(self):
        q = Question.objects.get(google_sheets_id=20214002)
        sq = q.subquestions.all()

        # post subanswers
        data_cases = [
            {
                f"question_{q.id}_sub_{sq[0].id}": "50",
                f"question_{q.id}_sub_{sq[1].id}": "20",
                f"question_{q.id}_sub_{sq[2].id}": "10",
            },
            {
                f"question_{q.id}_sub_{sq[0].id}": "0",
                f"question_{q.id}_sub_{sq[1].id}": "10",
                f"question_{q.id}_sub_{sq[2].id}": "2",
            },
            {
                f"question_{q.id}_sub_{sq[0].id}": "0",
                f"question_{q.id}_sub_{sq[1].id}": "0",
                f"question_{q.id}_sub_{sq[2].id}": "0",
            },
            {
                f"question_{q.id}_sub_{sq[0].id}": "12",
                f"question_{q.id}_sub_{sq[1].id}": "2",
                f"question_{q.id}_sub_{sq[2].id}": "1",
            },
            {
                f"question_{q.id}_sub_{sq[0].id}": "",
                f"question_{q.id}_sub_{sq[1].id}": "2",
                f"question_{q.id}_sub_{sq[2].id}": "1",
            },
            {
                f"question_{q.id}_sub_{sq[0].id}": "",
                f"question_{q.id}_sub_{sq[1].id}": "",
                f"question_{q.id}_sub_{sq[2].id}": "",
            },
        ]
        expected = [
            [50.0, 20.0, 10.0],
            [0.0, 10.0, 2.0],
            [0.0, 0.0, 0.0],
            [12.0, 2.0, 1.0],
            [None, 2.0, 1.0],
            [None, None, None],
        ]
        for key, data in enumerate(data_cases):
            self.post_form(
                "evaluation_fill",
                [self.e.id, "all", "chiffres", 0],
                data,
            )
            subanswers = Answer.objects.get(question_id=q.id).subanswers.all()
            self.assertEqual(subanswers[0].value, expected[key][0])
            self.assertEqual(subanswers[1].value, expected[key][1])
            self.assertEqual(subanswers[2].value, expected[key][2])

    @csrf_exempt
    def test_post_correct_subanswers_percentages(self):
        q = Question.objects.get(google_sheets_id=20214060)
        sq = q.subquestions.all()
        data_cases = [
            {
                f"question_{q.id}_sub_{sq[0].id}": "50",
                f"question_{q.id}_sub_{sq[1].id}": "40",
                f"question_{q.id}_sub_{sq[2].id}": "10",
            },
            {
                f"question_{q.id}_sub_{sq[0].id}": "0",
                f"question_{q.id}_sub_{sq[1].id}": "0",
                f"question_{q.id}_sub_{sq[2].id}": "100",
            },
            {
                f"question_{q.id}_sub_{sq[0].id}": "",
                f"question_{q.id}_sub_{sq[1].id}": "",
                f"question_{q.id}_sub_{sq[2].id}": "100",
            },
            {
                f"question_{q.id}_sub_{sq[0].id}": "10",
                f"question_{q.id}_sub_{sq[1].id}": "80",
                f"question_{q.id}_sub_{sq[2].id}": "10",
            },
            {
                f"question_{q.id}_sub_{sq[0].id}": "",
                f"question_{q.id}_sub_{sq[1].id}": "80",
                f"question_{q.id}_sub_{sq[2].id}": "20",
            },
        ]
        expected = [
            [50.0, 40.0, 10.0],
            [0.0, 0.0, 100.0],
            [None, None, 100.0],
            [10.0, 80.0, 10.0],
            [None, 80.0, 20.0],
        ]
        for key, data in enumerate(data_cases):
            self.post_form(
                "evaluation_fill",
                [self.e.id, "gender", "chiffres", 3],
                data,
            )
            subanswers = Answer.objects.get(question_id=q.id).subanswers.all()
            self.assertEqual(subanswers[0].value, expected[key][0])
            self.assertEqual(subanswers[1].value, expected[key][1])
            self.assertEqual(subanswers[2].value, expected[key][2])

    def test_choice_attribution_pourcentage_answer(self):
        q1 = Question.objects.get(google_sheets_id=20214049)  # pourcentage
        data_cases_q1 = [
            [-10.1, "Moins de -10%"],
            [-10, "Moins de -10%"],
            [-9, "Entre -10 et -5%"],
            [-5, "Entre -10 et -5%"],
            [-4.9, "Entre -5 et -3%"],
            [-4, "Entre -5 et -3%"],
            [-3, "Entre -5 et -3%"],
            [-2.9, "Entre -3 et -1%"],
            [-2, "Entre -3 et -1%"],
            [-1, "Entre -3 et -1%"],
            [-0.9, "Entre -1 et 0%"],
            [0, "Entre -1 et 0%"],
            [0.1, "Entre 0 et 1%"],
            [1, "Entre 0 et 1%"],
            [1.1, "Entre 1 et 3%"],
            [3, "Entre 1 et 3%"],
            [4.9, "Entre 3 et 5%"],
            [5, "Entre 3 et 5%"],
            [5.1, "Entre 5 et 10%"],
            [10, "Entre 5 et 10%"],
            [10.1, "Plus de 10%"],
        ]
        answer = Answer.objects.get(question_id=q1.id)
        for case in data_cases_q1:
            answer.value = case[0]
            answer.do_compute_scores(
                update_choices=True, update_comments=True, evaluation=self.e
            )
            self.assertEqual(answer.choice.label, case[1])

    def test_locked_unlocked(self):
        q1 = Question.objects.get(google_sheets_id=20214049)  # pourcentage
        data_cases_q1 = [
            [-10, "Moins de -10%"],
            [-9, "Entre -10 et -5%"],
        ]
        data_cases_q1_2 = [
            [-10, "Moins de -10%"],
            [-9, "Moins de -10%"],  # locked so doesn't update
        ]
        answer = Answer.objects.get(question_id=q1.id)
        for case in data_cases_q1:
            answer.value = case[0]
            answer.do_compute_scores(
                update_choices=True, update_comments=True, evaluation=self.e
            )
            self.assertEqual(answer.choice.label, case[1])
        for case in data_cases_q1_2:
            answer.value = case[0]
            answer.do_compute_scores(
                update_choices=True, update_comments=True, evaluation=self.e
            )
            answer.locked = True
            answer.save()
            self.assertEqual(answer.choice.label, case[1])

    @csrf_exempt
    def test_post_wrong_subanswers_percentages(self):
        q = Question.objects.get(google_sheets_id=20214060)
        sq = q.subquestions.all()
        data = {
            f"question_{q.id}_sub_{sq[0].id}": "50",
            f"question_{q.id}_sub_{sq[1].id}": "40",
            f"question_{q.id}_sub_{sq[2].id}": "9",
        }

        self.post_form(
            "evaluation_fill",
            [self.e.id, "gender", "chiffres", 3],
            data,
        )
        self.assertEqual(Answer.objects.get(question_id=q.id).subanswers.count(), 0)

    @csrf_exempt
    def test_post_wrong_subanswers_percentages_with_no_validators(self):
        q = Question.objects.get(google_sheets_id=20214060)
        sq = q.subquestions.all()
        sq.update(ui_type="pourcentage_novalidator")
        data = {
            f"question_{q.id}_sub_{sq[0].id}": "50",
            f"question_{q.id}_sub_{sq[1].id}": "40",
            f"question_{q.id}_sub_{sq[2].id}": "9",
        }

        self.post_form(
            "evaluation_fill",
            [self.e.id, "gender", "chiffres", 3],
            data,
        )
        subanswers = Answer.objects.get(question_id=q.id).subanswers.all()
        self.assertEqual(subanswers[0].value, 50)
        self.assertEqual(subanswers[1].value, 40)
        self.assertEqual(subanswers[2].value, 9)

    @csrf_exempt
    def test_date(self):
        q = Question.objects.get(google_sheets_id=20214060)
        q.type = "date"
        q.save()

        def do_value_test(date, date_expected, value_expected):
            data = {
                f"question_{q.id}": date,
            }

            self.post_form(
                "evaluation_fill",
                [self.e.id, "gender", "chiffres", 3],
                data,
            )
            self.assertEqual(Answer.objects.get(question_id=q.id).value, value_expected)
            view_template = EvaluationFill.as_view()(
                self.get_request(),
                pk=self.e.id,
                category="gender",
                subcategory="chiffres",
                page=3,
            )
            view = view_template.context_data["view"]
            self.assertEqual(view.get_initial()[f"question_{q.id}"], date_expected)

        do_value_test(
            "2023-12-05", "2023-12-05", 1701730800
        )  # 1701730800 = Unix timestamp for 2023-12-05 00:00
        # The value is stored as a timestamp in the
        # database instead of creating a new special datefield
        do_value_test("", None, None)

    @csrf_exempt
    def test_non_applicable(self):
        q = Question.objects.get(google_sheets_id=20214060)
        q.display_not_applicable = True
        q.save()
        data = {
            f"question_{q.id}_not_applicable": True,
        }

        self.post_form(
            "evaluation_fill",
            [self.e.id, "gender", "chiffres", 3],
            data,
        )
        self.assertEqual(Answer.objects.get(question_id=q.id).is_not_applicable, True)
        data = {
            f"question_{q.id}_not_applicable": False,
        }

        self.post_form(
            "evaluation_fill",
            [self.e.id, "gender", "chiffres", 3],
            data,
        )
        self.assertEqual(Answer.objects.get(question_id=q.id).is_not_applicable, False)

    @csrf_exempt
    def test_non_applicable_invalid(self):
        q = Question.objects.get(google_sheets_id=20214060)
        q.display_not_applicable = False
        q.save()
        data = {
            f"question_{q.id}_not_applicable": True,
        }

        self.post_form(
            "evaluation_fill",
            [self.e.id, "gender", "chiffres", 3],
            data,
        )
        self.assertEqual(Answer.objects.get(question_id=q.id).is_not_applicable, False)

    @csrf_exempt
    def test_not_followed(self):
        q = Question.objects.get(google_sheets_id=20214015)
        q.is_indicator = True
        q.save()
        sc = ScoreCategory.objects.get(category__slug="all")
        choice = q.choices.get(value=5).id
        data = {
            f"question_{q.id}_indicator_not_followed": True,
            f"question_{q.id}": choice,
        }

        self.post_form(
            "evaluation_fill",
            [self.e.id, "all", "awareness", 0],
            data,
        )
        self.assertEqual(Answer.objects.get(question_id=q.id).is_not_followed, True)
        self.assertEqual(
            round(sc.compute_score(), 2),
            54.17,
        )
        data = {
            f"question_{q.id}_not_followed": False,
            f"question_{q.id}": choice,
        }
        self.post_form(
            "evaluation_fill",
            [self.e.id, "all", "awareness", 0],
            data,
        )
        self.assertEqual(Answer.objects.get(question_id=q.id).is_not_followed, False)
        self.assertEqual(round(sc.compute_score(), 2), 55.83)

    @csrf_exempt
    def test_not_followed_invalid(self):
        q = Question.objects.get(google_sheets_id=20214015)
        q.is_indicator = False
        q.save()
        data = {
            f"question_{q.id}_indicator_not_followed": True,
        }

        self.post_form(
            "evaluation_fill",
            [self.e.id, "all", "awareness", 0],
            data,
        )
        self.assertEqual(Answer.objects.get(question_id=q.id).is_not_followed, False)

    @csrf_exempt
    def test_custom_question(self):
        q = Question.objects.get(google_sheets_id=20214015)
        q.display_custom_question_label = True
        q.save()
        data = {
            f"question_{q.id}_custom_question_label": "xdd",
        }

        self.post_form(
            "evaluation_fill",
            [self.e.id, "all", "awareness", 0],
            data,
        )
        self.assertEqual(
            Answer.objects.get(question_id=q.id).custom_question_label, "xdd"
        )
        data = {
            f"question_{q.id}_custom_question_label": "BWOAH",
        }
        self.post_form(
            "evaluation_fill",
            [self.e.id, "all", "awareness", 0],
            data,
        )
        self.assertEqual(
            Answer.objects.get(question_id=q.id).custom_question_label, "BWOAH"
        )

    @csrf_exempt
    def test_custom_question_invalid(self):
        q = Question.objects.get(google_sheets_id=20214015)
        q.display_custom_question_label = False
        q.save()
        data = {
            f"question_{q.id}_custom_question_label": "Madge",
        }

        self.post_form(
            "evaluation_fill",
            [self.e.id, "all", "awareness", 0],
            data,
        )
        self.assertEqual(
            Answer.objects.get(question_id=q.id).custom_question_label, None
        )

    def test_choice_attribution_valeur_answer(self):
        q1 = Question.objects.get(google_sheets_id=20214065)  # valeur

        data_cases_q1 = [
            [-1, "11 jours"],
            [0, "11 jours"],
            [10, "11 jours"],
            [11, "11 jours"],
            [12, "Entre 12 jours et 21 jours"],
            [20, "Entre 12 jours et 21 jours"],
            [21, "Entre 12 jours et 21 jours"],
            [22, "Entre 21 jours et 30 jours"],
            [29, "Entre 21 jours et 30 jours"],
            [30, "Entre 21 jours et 30 jours"],
            [31, "Plus de 30 jours"],
        ]
        answer = Answer.objects.get(question_id=q1.id)
        for case in data_cases_q1:
            answer.value = case[0]
            answer.do_compute_scores(
                update_choices=True, update_comments=True, evaluation=self.e
            )
            self.assertEqual(answer.choice.label, case[1])

    def test_choice_attribution_valeur_answer_with_json_rule(self):
        q1 = Question.objects.get(google_sheets_id=20214069)  # valeur
        q1.type = """valeur_json_{
	"mode": "ratio-questions",
	"questions": [
		"20214002_0", "20214002_1", "20214002_2"
	],
	"attributionmode": {
		"type": "tag-rule",
		"attributionmode": "range",
		"rules": [{
				"mandatory_tags": ["tag1", "tag2"],
				"forbidden_tags": ["tag3", "tag4"],
				"rule": [
					0.2,
					0.4,
					0.6,
					0.8
				]
			},
			{
				"mandatory_tags": ["tag3", "tag2"],
				"forbidden_tags": ["tag4"],
				"rule": [
					0.2,
					0.45,
					0.6,
					0.8
				]
			}
		]
	}
}"""
        q1.save()
        a, _ = Answer.objects.get_or_create(
            question=Question.objects.get(google_sheets_id=20214002), evaluation=self.e
        )

        for sq in a.question.subquestions.all():
            SubAnswer.objects.create(subquestion=sq, answer=a, value=12)
        test_cases = [
            [["tag1", "tag2"], "40 to 60%", False],
            [["tag3", "tag2"], "20 to 40%", False],
            [
                ["tag4"],
                "80 to 100%",
                True,
            ],  # By default, last choice is chosen. But in our case, the score is ignored anyway
        ]
        for case in test_cases:
            self.e.tags.clear()
            for tag in case[0]:
                tag, _ = QuestionTag.objects.get_or_create(name=tag)
                self.e.tags.add(tag)
            answer = Answer.objects.get(question_id=q1.id)
            answer.value = 15
            answer.do_compute_scores(
                update_choices=True, update_comments=True, evaluation=self.e
            )
            self.assertEqual(answer.choice.label, case[1])
            self.assertEqual(answer.is_not_applicable, case[2])

    def test_choice_attribution_subquestions_qcm_with_json(self):
        q1 = Question.objects.get(google_sheets_id=20214075)  # subquestions_qcm
        q1.type = """subquestions_qcm_json_{
    	"mode": "subquestions-qcm-count",
    	"range": [0, 4],
    	"attributionmode": "range"
    }"""
        q1.save()
        a, _ = Answer.objects.get_or_create(
            question=q1,
            evaluation=self.e,
        )
        for sq in q1.subquestions.all():
            SubAnswer.objects.create(subquestion=sq, answer=a, value=0.0)
        a.do_compute_scores(
            update_choices=True, update_comments=True, evaluation=self.e
        )
        self.assertEqual(a.choice.label, "Aucune case cochée")
        for sq in q1.subquestions.all():
            SubAnswer.objects.filter(subquestion=sq, answer=a).update(value=1.0)
        a.do_compute_scores(
            update_choices=True, update_comments=True, evaluation=self.e
        )
        self.assertEqual(a.choice.label, "Une case cochée ou plus")

    def test_choice_attribution_valeur_with_json_answer(self):
        q1 = Question.objects.get(google_sheets_id=20214002)  # subquestions
        answer = Answer.objects.get(question_id=q1.id)
        sq = q1.subquestions.all()
        sa1 = SubAnswer.objects.create(subquestion=sq[0], value=50, answer=answer)
        sa2 = SubAnswer.objects.create(subquestion=sq[1], value=25, answer=answer)
        sa3 = SubAnswer.objects.create(subquestion=sq[2], value=25, answer=answer)

        q2 = Question.objects.get(google_sheets_id=20214069)  # valeur_json
        # 0 to 20% ; 20 to 40% ; 40 to 60% ; 60 to 80% ; 80 to 100%
        data_cases_q2 = [
            [19.9, "0 to 20%"],
            [20, "0 to 20%"],
            [20.1, "20 to 40%"],
            [39.9, "20 to 40%"],
            [40, "20 to 40%"],
            [40.1, "40 to 60%"],
            [59.9, "40 to 60%"],
            [60, "40 to 60%"],
            [60.1, "60 to 80%"],
            [79.9, "60 to 80%"],
            [80, "60 to 80%"],
            [80.1, "80 to 100%"],
            [100.1, "80 to 100%"],  # expected because no more choice after 0.8
        ]
        answer = Answer.objects.get(question_id=q2.id)
        for case in data_cases_q2:
            answer.value = case[0]
            answer.do_compute_scores(
                update_choices=True, update_comments=True, evaluation=self.e
            )
            self.assertEqual(answer.choice.label, case[1])

    @csrf_exempt
    def test_post_wrong_subanswers_percentages(self):
        q = Question.objects.get(google_sheets_id=20214060)
        sq = q.subquestions.all()
        data = {
            f"question_{q.id}_sub_{sq[0].id}": "50",
            f"question_{q.id}_sub_{sq[1].id}": "40",
            f"question_{q.id}_sub_{sq[2].id}": "9",
        }
        with self.assertNumQueries(108):
            self.post_form(
                "evaluation_fill",
                [self.e.id, "gender", "chiffres", 3],
                data,
            )
        self.assertEqual(Answer.objects.get(question_id=q.id).subanswers.count(), 0)

    @csrf_exempt
    def test_post_answers(self, assert_disabled=False):
        q1 = Question.objects.get(google_sheets_id=20214007)
        q2 = Question.objects.get(google_sheets_id=20214008)
        data_cases = [
            {
                f"question_{q1.id}": "50",
                f"question_{q2.id}": "20",
            },
            {
                f"question_{q1.id}": "0",
                f"question_{q2.id}": "20",
            },
            {
                f"question_{q1.id}": "",
                f"question_{q2.id}": "",
            },
            {
                f"question_{q1.id}": "50",
                f"question_{q2.id}": "",
            },
            {
                f"question_{q1.id}": "-1",
                f"question_{q2.id}": "-12",
            },
        ]
        # test if answers are saved correctly according to user input.
        # [0] : q1, [1] : q2, [2] : Queries Expected
        expected = [
            [50.0, 20.0, 41],
            [0.0, 20.0, 41],
            [None, None, 39],
            [50.0, None, 40],
            [-1, -12, 41],
        ]
        for key, data in enumerate(data_cases):
            if assert_disabled:
                self.post_form(
                    "evaluation_fill",
                    [self.e.id, "all", "chiffres", 1],
                    data,
                )
            else:
                with self.assertNumQueries(expected[key][2]):
                    self.post_form(
                        "evaluation_fill",
                        [self.e.id, "all", "chiffres", 1],
                        data,
                    )
            self.assertEqual(
                Answer.objects.get(question_id=q1.id).value, expected[key][0]
            )
            self.assertEqual(
                Answer.objects.get(question_id=q2.id).value, expected[key][1]
            )

    @csrf_exempt
    def test_post_answer_with_precise(self):
        q = Question.objects.get(google_sheets_id=20214063)
        choice = q.choices.first()

        # post answer
        data_cases = [
            {
                f"question_{q.id}": str(choice.id),
                f"question_{q.id}_detail": "oui",
            },
            {
                f"question_{q.id}": str(choice.id),
                f"question_{q.id}_detail": "",
            },
            {
                f"question_{q.id}": "",
                f"question_{q.id}_detail": "oui",
            },
        ]

        # [0] : q, [1] : choice, [2] : Queries Expected
        expected = [[choice, "oui", 43], [choice, "", 43], [None, "oui", 42]]
        for key, data in enumerate(data_cases):
            with self.assertNumQueries(expected[key][2]):
                self.post_form(
                    "evaluation_fill",
                    [self.e.id, "gender", "career-development", 0],
                    data,
                )
            self.assertEqual(
                Answer.objects.get(question_id=q.id).choice, expected[key][0]
            )
            self.assertEqual(
                Answer.objects.get(question_id=q.id).text_value, expected[key][1]
            )

    def test_good_bad_comments(self):
        q = Question.objects.get(google_sheets_id=20214063)
        choice_good = q.choices.get(value=5)
        choice_bad_1 = q.choices.get(value=1)
        fake_choice = q.choices.get(value=1)
        fake_choice.pk = None
        fake_choice.value = 0
        fake_choice.save()
        choice_bad_0 = fake_choice
        choice_dont_care = q.choices.get(value=3)

        # post answer
        data_cases = [
            {
                f"question_{q.id}": str(choice_good.id),
            },
            {
                f"question_{q.id}": str(choice_bad_0.id),
            },
            {
                f"question_{q.id}": str(choice_dont_care.id),
            },
            {
                f"question_{q.id}": str(choice_bad_1.id),
            },
        ]

        # if there is a good (True), bad (False) or no (None) comment
        expected = [True, False, None, False]
        for key, data in enumerate(data_cases):
            self.post_form(
                "evaluation_fill",
                [self.e.id, "gender", "career-development", 0],
                data,
            )
            answer = Answer.objects.get(question_id=q.id)
            answer.do_compute_scores(
                update_choices=True, update_comments=True, evaluation=self.e
            )
            if expected[key] is None:
                self.assertIsNone(answer.comment)
            else:
                self.assertEqual(answer.comment.is_good, expected[key])
        a = Answer.objects.get(question_id=q.id)
        a.choice = choice_good
        a.do_compute_scores(
            update_choices=True, update_comments=True, evaluation=self.e
        )
        a.refresh_from_db()
        self.assertTrue(a.comment.is_good)  # check if save works
        a.comment = Comment.objects.filter(question_id=q.id, is_good=False).first()
        a.do_compute_scores(
            update_choices=True, update_comments=True, evaluation=self.e
        )
        a.refresh_from_db()
        self.assertTrue(
            a.comment.is_good
        )  # if evaluation not validated by user, custom comment attribution not possible

        self.e.do_user_validation()
        a.refresh_from_db()
        a.comment = Comment.objects.filter(question_id=q.id, is_good=False).first()
        a.do_compute_scores(
            update_choices=True, update_comments=False, evaluation=self.e
        )  # do_compute_scores must never be called with update_comments=True after do_user_validation
        a.refresh_from_db()
        self.assertFalse(
            a.comment.is_good
        )  # if evaluation is validated by user, custom comment attribution is possible

    def get_request(self):
        factory = RequestFactory()

        request = factory.get("")
        request.user = self.user
        # in your test method:
        """Annotate a request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        """Annotate a request object with a messages"""
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        return request

    def questions_test_cases(self, ids, category, subcategory, actions):
        for key, id_list in enumerate(ids):
            view_template = EvaluationFill.as_view()(
                self.get_request(),
                pk=self.e.id,
                category=category,
                subcategory=subcategory,
                page=key,
            )
            view = view_template.context_data["view"]
            self.assertEqual(len(view.get_questions()), len(id_list))
            for question in view.get_questions():
                self.assertTrue(question.google_sheets_id in id_list)
            self.assertEqual(
                view.get_next_action(view_template.context_data), actions[key]
            )

    # Affected test after change of categories and subcategories orders
    def test_get_questions_key_figures(self):
        ids = [
            [20214002, 20214003, 20214004, 20214005, 20214006],
            [20214007, 20214008, 202140081, 202140082, 20214009],
            [20214010, 20214011, 20214012, 20214013, 20214016],
            [20214017, 20214023, 20214027, 20214029, 20214030],
            [20214031, 20214038],
        ]
        actions = ["Continuer vers Chiffres-clés"] * 4 + [
            "Continuer vers Sensibilisation"
        ]
        with self.assertNumQueries(136):
            self.questions_test_cases(ids, "all", "chiffres", actions)

    def test_get_questions_normal_category(self):
        ids = [
            [20214098, 20214099, 20214101],
            [20214102, 20214103, 20214105],
        ]
        actions = [
            "Continuer vers Sensibilisation",
            "Continuer vers Qualité de vie au travail",
        ]
        # cats in prod are in the correct order, not in test env bcs they don't exist prior the import
        sensibilisation = SubCategory.objects.get(slug="awareness")
        qualite = SubCategory.objects.get(slug="work-life-balance")
        sensibilisation.order = qualite.order
        sensibilisation.save()
        qualite.order = sensibilisation.order + 1
        qualite.save()
        with self.assertNumQueries(64):
            self.questions_test_cases(ids, "disability", "awareness", actions)

    def test_get_questions_to_key_figures(self):
        ids = [
            [20214165],
        ]
        actions = [
            "Continuer vers LGBTQIA+ / Champ libre",
        ]
        # cats in prod are in the correct order, not in test env bcs they don't exist prior the import
        recrutement = SubCategory.objects.get(slug="recruitment")
        recrutement.order = 999
        recrutement.save()
        with self.assertNumQueries(30):
            self.questions_test_cases(ids, "lgbt", "recruitment", actions)

    def test_to_key_figures(
        self,
    ):
        view_template = EvaluationCategoryConfirm.as_view()(
            self.get_request(),
            pk=ScoreCategory.objects.get(category__slug="generational_diversity").pk,
            category="generational_diversity",
        )
        with self.assertNumQueries(11):
            view_template.render()
        view = view_template.context_data["view"]
        self.assertEqual(
            view.get_next_action(view_template.context_data),
            "Continuer vers LGBTQIA+ / Chiffres-clefs",
        )

    def test_to_validation(
        self,
    ):
        view_template = EvaluationCategoryConfirm.as_view()(
            self.get_request(),
            pk=ScoreCategory.objects.get(category__slug="lgbt").pk,
            category="lgbt",
        )
        view = view_template.context_data["view"]
        with self.assertNumQueries(11):
            view_template.render()
        self.assertEqual(
            view.get_next_action(view_template.context_data),
            "Passer à la validation",
        )

    def test_company_sheet_view(self):
        evaluation_random_generator(queryset=Evaluation.objects.all(), not_random=True)
        with self.assertNumQueries(969):
            self.e.do_user_validation()
        self.e.public_display = True
        self.e.private_display = True
        with self.assertNumQueries(7):
            self.e.do_admin_validation()
        # Non cached
        with self.assertNumQueries(450):  # TODO: outrageous number of queries...
            StructureDetailPublicView.as_view()(
                self.get_request(),
                slug=self.e.entity.slug,
                subscription_type=self.e.subscription.subscription_type.slug,
            ).render()
        # Cached
        with self.assertNumQueries(69):
            StructureDetailPublicView.as_view()(
                self.get_request(),
                slug=self.e.entity.slug,
                subscription_type=self.e.subscription.subscription_type.slug,
            ).render()

    def test_key_figures_and_category_answers_rate_reset(self):
        sc = ScoreCategory.objects.get(category__slug="all")
        self.assertIsNone(sc.key_figures_filled)
        self.assertIsNone(sc.category_answers_rate_cache)
        with self.assertNumQueries(123):  # no cache yet
            self.get_page("evaluation_confirm", [self.e.id])
        with self.assertNumQueries(119):  # cache available
            self.get_page("evaluation_confirm", [self.e.id])
        sc.refresh_from_db()
        #####   IMPORTANT : key_figures_filled not used anymore   #####
        ## (Since targets exists and need to be tracked differently) ##
        #####    cf get_categories_datas() in evaluation model    #####
        #        self.assertIsNotNone(sc.key_figures_filled)
        #        self.assertIsNotNone(sc.category_answers_rate_cache)
        self.test_post_answers(assert_disabled=True)
        sc.refresh_from_db()
        self.assertIsNone(sc.key_figures_filled)
        self.assertEqual(sc.category_answers_rate_cache, 0.0)


class EvaluationFillCampusTest(TestCaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(EvaluationFillCampusTest, cls).setUpClass()
        cls.make_categories()
        sheet_type = QuestionSheetType.objects.create(
            slug="mixity_evaluation_campus",
            name="Evaluation Mixity Campus",
        )
        file = os.path.join(
            settings.STATICFILES_DIRS[0],
            "csv/campus2022/questionnaire_campus2022_20240527_1005.csv",
        )
        with HiddenPrints():
            import_20240527_1005.import_questions(
                apps, file, "mixity_evaluation_campus"
            )

        sheet = QuestionSheet.objects.first()
        businessLine = BusinessLine.objects.create(
            slug="others",
            name_fr="Autre - précisez",
            name_en="Others",
        )
        s = Structure.objects.create(
            juridic_name="My Structure",
            slug="my_structure",
            workforce=300,
            category="school",
            business_line=businessLine,
        )
        e_lvl_0 = cls.make_entity_level(s, "Groupe", 0)
        entity = cls.make_entity(s.juridic_name, e_lvl_0, s.workforce)
        u, _ = MixityUser.objects.get_or_create(
            email="user@user.com",
            password="user",
            first_name="user1",
            phone=12345679,
            last_name="Yee",
        )
        sub = SubscriptionType.objects.create(
            label="Mixity Campus",
            pme_label="Mixity Campus",
            slug="campus",
            order=5,
            description="",
            is_active=True,
            allow_structure_evaluation=True,
            allow_public_display=True,
            allow_add_structure_members=True,
        )
        sub.question_sheet_types.add(sheet_type)
        subscription = Subscription.objects.create(
            is_active=True,
            start_date=timezone.now(),
            structure=s,
            subscription_type=sub,
            question_sheet_type=sheet_type,
        )
        sub_pack = cls.make_subscription_pack(datetime.date.today(), s)
        product = cls.make_product("Mixity Campus", "diag", sheet_type)
        sub_opt = cls.make_subscription_option(sub_pack, product.slug)
        Membership.objects.create(structure=s, user=u, is_owner=True)
        cls.e = Evaluation.objects.create(
            sheet=sheet, entity=entity, subscription=subscription
        )
        cls.make_entity_membership(u, entity)
        cls.e.generate_answers()
        cls.user = u
        cls.scoring_client = Client()
        cls.scoring_client.force_login(cls.user)

    @csrf_exempt
    def get_page(self, path, args):
        path = reverse(path, args=args)
        response = self.scoring_client.get(path)
        self.assertEqual(response.status_code, 200)

    def get_request(self):
        factory = RequestFactory()

        request = factory.get("")
        request.user = self.user
        # in your test method:
        """Annotate a request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        """Annotate a request object with a messages"""
        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        return request

    def test_targets(self):
        targets = self.e.targets
        expected = ["collaborator", "student"]
        self.assertListEqual(targets, expected)

    def test_to_validation(self):
        view_template = EvaluationCategoryConfirm.as_view()(
            self.get_request(),
            pk=ScoreCategory.objects.get(category__slug="lgbt").pk,
            target="collaborator",
            category="lgbt",
        )
        view = view_template.context_data["view"]
        with self.assertNumQueries(17):
            view_template.render()
        self.assertEqual(
            view.get_next_action(view_template.context_data),
            "Continuer vers student / Transversal / Chiffres-clefs",
        )

    def test_key_figures_and_category_answers_rate_reset(self):
        sc = ScoreCategory.objects.get(category__slug="all")
        self.assertIsNone(sc.key_figures_filled)
        self.assertIsNone(sc.category_answers_rate_cache)
        with self.assertNumQueries(129):  # no cache yet
            self.get_page("evaluation_confirm", [self.e.id])
        with self.assertNumQueries(125):  # cache available
            self.get_page("evaluation_confirm", [self.e.id])


class HumanEvaluationTest(TestCaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(HumanEvaluationTest, cls).setUpClass()
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

        # Structure
        juridic_name = "My Human"
        slug = "my_human"
        workforce = 100
        category = "Diversity"
        cls.s = cls.make_structure(
            juridic_name, slug, workforce, category, business_line
        )
        e_lvl_0 = cls.make_entity_level(cls.s, "Groupe", 0)
        cls.entity = cls.make_entity(cls.s.juridic_name, e_lvl_0, cls.s.workforce)

        # User
        u = cls.make_common_user()

        # Subscription Type
        label = "Mixity Human"
        pme_label = "Mixity Human"
        slug = "human"
        order = 3
        desc = ""
        sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)
        # Subscription
        subscription = cls.make_subscription(sheet_type, sub_type, cls.s)
        sub_pack = cls.make_subscription_pack(datetime.date.today(), cls.s)
        product = cls.make_product(label, "human", sheet_type)
        sub_opt = cls.make_subscription_option(sub_pack, product.slug)

        # Membership
        cls.make_membership(u, cls.s)
        cls.make_entity_membership(u, cls.entity)

        # Attributes
        cls.user = u
        cls.scoring_client = Client()
        cls.scoring_client.force_login(cls.user)

        cls.e = Evaluation.objects.create(
            sheet=sheet, entity=cls.entity, subscription=subscription
        )
        criteria_json = [
            {
                "label": "Fonction",
                "choices": [
                    "Agent de maîtrise",
                    "Technicien.ne",
                    "Associé.e",
                    "Cadre",
                    "Employé.e",
                    "Autre",
                ],
            },
            {"label": "test", "choices": ["test1", "test2", "test3"]},
        ]
        for criteria in criteria_json:
            human_criteria = HumanCriteria.objects.create(
                evaluation=cls.e, label=criteria["label"]
            )
            for choice in criteria["choices"]:
                HumanCriteriaChoice.objects.create(
                    criteria=human_criteria, label=choice
                )

    @csrf_exempt
    def get_page(self, path, args):
        path = reverse(path, args=args)
        response = self.scoring_client.get(
            path,
        )
        self.assertEqual(response.status_code, 200)

    def test_load_footprint_public_page(self):
        management.call_command("generate_random_human_answers", self.e.id, 10)
        self.e.do_user_validation()
        self.e.public_display = True
        self.e.private_display = True
        self.e.do_admin_validation()
        with self.assertNumQueries(92):
            self.get_page("detail_public", args=[self.entity.slug])
        with self.assertNumQueries(68):
            self.get_page("detail_public", args=[self.entity.slug])
        management.call_command(
            "generate_random_human_answers", self.e.id, 10
        )  # TODO: this seems impossible, we should not generate responses after validation ?
        self.e.do_user_validation(True)
        self.e.do_admin_validation()
        with self.assertNumQueries(68):
            self.get_page("detail_public", args=[self.entity.slug])


# class EvaluationExportQuestionsSheetTest(TestCaseMixin, TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super(EvaluationExportQuestionsSheetTest, cls).setUpClass()
#         # Categories
#         cls.make_categories()

#         # Sheet
#         name = "Sheet Type"
#         sheet_path = "csv/society2021/questionnaire_society2021_20240527_1005.csv"
#         sheet, sheet_type = cls.make_sheet_global(name, sheet_path)

#         # BusinessLine
#         slug = "others"
#         name_fr = "Autre - précisez"
#         name_en = "Others"
#         businessLine = cls.make_business_line(slug, name_fr, name_en)

#         # Structure
#         juridic_name = "Structure Test"
#         slug = "structure_test"
#         workforce = 100
#         category = "Diversity"
#         s = cls.make_structure(juridic_name, slug, workforce, category, businessLine)
#         e_lvl_0 = cls.make_entity_level(s, "Groupe", 0)
#         e = cls.make_entity(s.juridic_name, e_lvl_0, s.workforce)

#         # User
#         u = cls.make_common_user()

#         # Subscription Type
#         label = "Mixity Diag"
#         pme_label = "Mixity Global"
#         slug = "global"
#         order = 4
#         desc = ""
#         sub = cls.make_subscription_type(label, pme_label, slug, order, desc)

#         # Subscription
#         subscription = cls.make_subscription(sheet_type, sub, s)
#         sub_pack = cls.make_subscription_pack(datetime.date.today(), s)
#         product = cls.make_product(label, "diag", sheet_type)
#         sub_opt = cls.make_subscription_option(sub_pack, product.slug)

#         # Membership
#         cls.make_membership(u, s)
#         cls.make_entity_membership(u, e)

#         # Attributes
#         # References files for test
#         empty_file_path = os.path.join(
#             settings.STATICFILES_DIRS[0],
#             "test_questions_sheets/empty_questions_sheet/Summary_Empty.xlsx",
#         )
#         filled_file_path = os.path.join(
#             settings.STATICFILES_DIRS[0],
#             "test_questions_sheets/filled_questions_sheet/Summary_Filled.xlsx",
#         )
#         cls.e = Evaluation.objects.create(
#             sheet=sheet, entity=e, subscription=subscription
#         )
#         cls.e.generate_answers()
#         cls.user = u
#         cls.scoring_client = Client()
#         cls.scoring_client.force_login(cls.user)
#         cls.empty_file_path = empty_file_path
#         cls.filled_file_path = filled_file_path

#     def test_empty_questions_sheet(self):
#         # Paths
#         # Generated questions sheet path
#         generated_path = self.e.export_answer_sheet()
#         # Reference empty questions sheet path
#         reference_path = self.empty_file_path

#         self.assertTrue(compare_excel_files(generated_path, reference_path))

#     def test_filled_questions_sheet(self):
#         """
#         NOTE: this function test if a filled generated questions sheet have the same answers as the reference file

#         """

#         # Filling the generated evaluation
#         questions_id = [20214106, 20214093, 20214071, 20214146, 20214162, 20214002]
#         answers = [
#             "C'est une action planifiée pour les 6 prochains mois",
#             "Oui",
#             "Rien",
#             "Oui, c'est formalisé et suivi depuis plusieurs années dans une démarche d'amélioration continue",
#             "Oui, c'est un dispositif existant depuis peu et qui nécessite d'être renforcé",
#         ]

#         for i in range(len(questions_id)):
#             current_question = self.e.sheet.questions.filter(
#                 google_sheets_id=questions_id[i]
#             ).first()
#             current_answer = current_question.answers.filter(evaluation=self.e).first()

#             if current_question.category.name != "Transversal":
#                 current_answer.choice = current_question.choices.filter(
#                     label=answers[i]
#                 ).first()
#                 current_answer.save()
#             else:
#                 sub_answers = [45.0, 45.0, 10.0]
#                 for j in range(len(sub_answers)):
#                     sq = current_question.subquestions.all()[j]
#                     SubAnswer.objects.update_or_create(
#                         subquestion=sq,
#                         answer=current_answer,
#                         value=sub_answers[j],
#                     )

#         # Comparing
#         # Generated questions sheet path
#         generated_path = self.e.export_answer_sheet()
#         # Reference empty questions sheet path
#         reference_path = self.filled_file_path
#         self.assertTrue(compare_excel_files(generated_path, reference_path))


class DashboardTest(TestCaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(DashboardTest, cls).setUpClass()
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

        # Structure
        juridic_name = "My Human"
        slug = "my_human"
        workforce = 100
        category = "Diversity"
        cls.s = cls.make_structure(
            juridic_name, slug, workforce, category, business_line
        )
        e_lvl_0 = cls.make_entity_level(cls.s, "Groupe", 0)
        cls.entity = cls.make_entity(cls.s.juridic_name, e_lvl_0, cls.s.workforce)

        # User
        u = cls.make_common_user()

        # Subscription Type
        label = "Mixity Human"
        pme_label = "Mixity Human"
        slug = "human"
        order = 3
        desc = ""
        sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)
        # Subscription
        subscription = cls.make_subscription(sheet_type, sub_type, cls.s)
        sub_pack = cls.make_subscription_pack(datetime.date.today(), cls.s)
        product = cls.make_product(label, "human", sheet_type)
        sub_opt = cls.make_subscription_option(sub_pack, product.slug)

        # Membership
        cls.make_membership(u, cls.s)
        cls.make_entity_membership(u, cls.entity)

        # Attributes
        cls.user = u
        cls.scoring_client = Client()

        cls.e = Evaluation.objects.create(
            sheet=sheet, entity=cls.entity, subscription=subscription
        )
        criteria_json = [
            {
                "label": "Fonction",
                "choices": [
                    "Agent de maîtrise",
                    "Technicien.ne",
                    "Associé.e",
                    "Cadre",
                    "Employé.e",
                    "Autre",
                ],
            },
            {"label": "test", "choices": ["test1", "test2", "test3"]},
        ]
        for criteria in criteria_json:
            human_criteria = HumanCriteria.objects.create(
                evaluation=cls.e, label=criteria["label"]
            )
            for choice in criteria["choices"]:
                HumanCriteriaChoice.objects.create(
                    criteria=human_criteria, label=choice
                )

    @csrf_exempt
    def get_page(self, path, args):
        path = reverse(path, args=args)
        response = self.scoring_client.get(
            path,
        )
        self.assertEqual(response.status_code, 200)

    @csrf_exempt
    def get_page_redirect(self, path, args):
        path = reverse(path, args=args)
        response = self.scoring_client.get(
            path,
        )
        self.assertEqual(response.status_code, 302)

    def test_dashboard_assess_pages(self):
        management.call_command("generate_random_human_answers", self.e.id, 10)
        self.e.do_user_validation()
        self.e.public_display = True
        self.e.private_display = True
        self.e.do_admin_validation()
        self.get_page_redirect("home", args=[self.entity.slug])
        self.get_page_redirect(
            "dashboard:dashboard_assess",
            args=[
                self.entity.slug,
                self.e.subscription.subscription_type.slug,
                self.e.display_version_slugified,
            ],
        )
        self.scoring_client.force_login(self.user)
        with self.assertNumQueries(37):
            self.get_page("home", args=[self.entity.slug])
        with self.assertNumQueries(
            7
        ):  # Todo opti (85 a l'origine avant la refonte de fiche)
            self.get_page_redirect(
                "dashboard:dashboard_assess",
                args=[
                    self.entity.slug,
                    self.e.subscription.subscription_type.slug,
                    self.e.display_version_slugified,
                ],
            )


class ImportSheetTest(TestCaseMixin, TestCase):
    """
    Tests for question_sheet import.
    By default, it tests the last version of the script. But you can provide a specific version of the script in some
    tests if some versions have to be treated differently
    """

    @classmethod
    def setUpClass(cls):
        super(ImportSheetTest, cls).setUpClass()
        sheet_type = QuestionSheetType.objects.create(
            slug="mixity_evaluation_campus",
            name="Evaluation Mixity Campus",
        )
        general = Category.objects.create(
            name="Transversal", slug="all", weight_index=1
        )
        subcat = SubCategory.objects.create(name="Gouvernance", slug="governance")
        subcat.categories.add(general)
        genre = Category.objects.create(name="Genre", slug="gender", weight_index=1)
        subcat1 = SubCategory.objects.create(name="Sensibilisation", slug="awareness")
        subcat1.categories.add(genre)

    def get_file(self, name):
        return f"scoring/importsheets/test_scenarios/{name}.csv"

    def import_sheet(self, package, file):
        package.import_questions(apps, self.get_file(file), "mixity_evaluation_campus")

    def get_last_script(self):
        files = next(os.walk("scoring/importsheets"), (None, None, []))[2]
        files.sort()
        last_script = files[-1].split(".")[0]
        return importlib.import_module(f"scoring.importsheets.{last_script}")

    def scenarios(
        self,
        replace_lang=False,
        updated=False,
        marks=[[5, 4, 2, 1, 0], [5, 3, 2, 1, 0], [5, 4, 3, 2, 1]],
        choices_count=3,
    ):
        """
        Main test function to verify if import went well
        @param replace_lang: True or False. Allow to replace es strings with fr. Useful for one of the tests
        @param updated: True or False. For the update tests, we change some things (update_ string, reverse, ...)
        @param marks: Marks also change sometimes depending on tests
        @param choices_count: Useful for the tests to add/remove choices, subquestions and subchoices
        @return:
        """
        q = Question.objects.select_related("subcategory", "category")
        print(q)
        q1 = q.get(google_sheets_id=2021000)
        print(q1)
        q2 = q.get(google_sheets_id=2021001)
        if updated:
            update = "update_"
        else:
            update = ""
        comment_plus_q1 = Comment.objects.get(
            question__google_sheets_id=2021000, is_good=True
        )
        comment_minus_q1 = Comment.objects.get(
            question__google_sheets_id=2021000, is_good=False
        )
        comment_plus_q2 = Comment.objects.get(
            question__google_sheets_id=2021001, is_good=True
        )
        comment_minus_q2 = Comment.objects.get(
            question__google_sheets_id=2021001, is_good=False
        )
        if not updated:
            self.assertEqual(q1.subcategory.slug, "governance")
            self.assertEqual(q2.subcategory.slug, "awareness")
            self.assertEqual(q1.category.slug, "all")
            self.assertEqual(q2.category.slug, "gender")
            self.assertEqual(q1.weight_index, 0)
            self.assertEqual(q2.weight_index, 1)
            self.assertEqual(q1.ask_detail, True)
            self.assertEqual(q2.ask_detail, False)
        self.assertEqual(
            list(q1.mandatory_tags.values_list("name", flat=True)),
            [update + "mandat1", update + "mandat2"],
        )
        self.assertEqual(
            list(q2.mandatory_tags.values_list("name", flat=True)),
            [update + "mandat21", update + "mandat22"],
        )
        self.assertEqual(
            list(q1.forbidden_tags.values_list("name", flat=True)),
            [update + "forbid1", update + "forbid2"],
        )
        self.assertEqual(
            list(q2.forbidden_tags.values_list("name", flat=True)),
            [update + "forbid21", update + "forbid22"],
        )
        for lang in settings.LANGUAGES_GOOGLE_SHEETS.values():
            lang2 = lang.replace("es", "fr") if replace_lang else lang
            self.assertEqual(getattr(q1, f"label_{lang}"), update + f"label{lang2}")
            self.assertEqual(getattr(q2, f"label_{lang}"), update + f"label{lang2}2")
            self.assertEqual(getattr(q1, f"help_text_{lang}"), update + f"help{lang2}")
            self.assertEqual(getattr(q2, f"help_text_{lang}"), update + f"help{lang2}2")
            lang2 = lang.replace("es", "en") if replace_lang else lang
            self.assertEqual(
                getattr(comment_plus_q1, f"description_{lang}"),
                update + f"strength{lang2}",
            )
            self.assertEqual(
                getattr(comment_plus_q2, f"description_{lang}"),
                update + f"strength{lang2}2",
            )
            self.assertEqual(
                getattr(comment_minus_q1, f"description_{lang}"),
                update + f"weakness{lang2}",
            )
            self.assertEqual(
                getattr(comment_minus_q2, f"description_{lang}"),
                update + f"weakness{lang2}2",
            )
            lang2 = lang.replace("es", "fr") if replace_lang else lang
            i = 0
            mark = marks[0]
            for choice in q1.choices.all():
                i += 1
                self.assertEqual(
                    getattr(choice, f"label_{lang}"), update + f"{lang2}{i}"
                )
                self.assertEqual(choice.value, mark[i - 1])
            self.assertEqual(i, choices_count)
            i = 0
            mark = marks[1]
            for choice in q2.choices.all():
                i += 1
                self.assertEqual(
                    getattr(choice, f"label_{lang}"), update + f"{lang2}2{i}"
                )
                self.assertEqual(choice.value, mark[i - 1])
            self.assertEqual(i, 3)
            i = 0
            for sq in q1.subquestions.all():
                i += 1
                self.assertEqual(
                    getattr(sq, f"label_{lang}"), update + f"sub{lang2}{i}"
                )
            self.assertEqual(i, choices_count)
            i = 0
            mark = marks[2]
            for sq in q2.subquestions.all():
                i += 1
                self.assertEqual(
                    getattr(sq, f"label_{lang}"), update + f"sub{lang2}2{i}"
                )
                j = 0
                for choice in sq.choices.all():
                    j += 1
                    self.assertEqual(
                        getattr(choice, f"label_{lang}"),
                        update + f"subchoice{lang2}{j}",
                    )
                    self.assertEqual(getattr(choice, f"value"), mark[j - 1])
                self.assertEqual(j, choices_count)
            self.assertEqual(i, 3)

    def test_all_langs(self):
        self.import_sheet(self.get_last_script(), "main_file_all_lang")
        self.scenarios()

    def test_reimport_no_change(self):
        self.import_sheet(self.get_last_script(), "main_file_all_lang")
        self.import_sheet(self.get_last_script(), "main_file_all_lang")
        self.scenarios()

    def test_without_es(self):
        """
        Expected behaviour : Non-filled languages will be replaced by default lang. For simple fields, it will be the
        column without the lang provided. For multiple fields (Subquestions, ...) it will be the first language
        provided in the sheet.
        """
        self.import_sheet(self.get_last_script(), "main_file_without_es")
        self.scenarios(replace_lang=True)

    def test_missing_subcategory(self):
        """
        Expected behaviour : We don't create subcategories in the script anymore. The script has to crash.
        """
        try:
            self.import_sheet(self.get_last_script(), "missing_subcategory")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual("Missing subcategory JeNexistePasXD", e.__str__())

    def test_missing_category(self):
        """
        Expected behaviour : We don't create categories in the script anymore. The script has to crash.
        """
        try:
            self.import_sheet(self.get_last_script(), "missing_category")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual(
                "Missing category MoiNonPlus for question 2021001", e.__str__()
            )

    def test_wrong_sheet_name(self):
        """
        Expected behaviour : We check if we import the correct sheet (to prevent an import of Human sheet in
        Diag for instance). The script has to crash.
        """
        try:
            self.import_sheet(self.get_last_script(), "wrong_sheet_name")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual(
                "Wrong CSV. Expected a 'mixity_evaluation_campus' questions sheet but got "
                "'mixity_evaluation_campus_pas_bon'",
                e.__str__(),
            )

    def test_no_question_label(self):
        """
        Expected behaviour : QUESTION_LABEL column is mandatory (even if other languages are provided)
        """
        try:
            self.import_sheet(self.get_last_script(), "no_question_label")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual(
                "QUESTION_LABEL missing for Question 2021001",
                e.__str__(),
            )

    def test_missing_default(self):
        """
        Expected behaviour : same as QUESTION_LABEL. However, if nothing is provided at all, it'll not crash
        """
        cases = ["help_text", "recommandation", "indicators"]
        for case in cases:
            try:
                self.import_sheet(self.get_last_script(), "missing_" + case)
                self.fail("Import should have failed")
            except ValueError as e:
                self.assertEqual(
                    f"No default lang for column {case.upper()} (Question : 2021001)",
                    e.__str__(),
                )

    def test_update_sheet(self):
        """
        Test to check if all fields are updated when we import again a sheet
        @return:
        """
        self.import_sheet(self.get_last_script(), "main_file_all_lang")
        self.import_sheet(self.get_last_script(), "main_file_updated")
        self.scenarios(
            updated=True,
            marks=[
                [1, 2, 3],
                [3, 2, 1],
                [3, 2, 1],
            ],
        )
        q = Question.objects.select_related("subcategory", "category")
        q1 = q.get(google_sheets_id=2021000)
        q2 = q.get(google_sheets_id=2021001)
        self.assertEqual(q2.subcategory.slug, "governance")
        self.assertEqual(q1.subcategory.slug, "awareness")
        self.assertEqual(q2.category.slug, "all")
        self.assertEqual(q1.category.slug, "gender")
        self.assertEqual(q2.weight_index, 0)
        self.assertEqual(q1.weight_index, 1)
        self.assertEqual(q2.ask_detail, True)
        self.assertEqual(q1.ask_detail, False)

    def test_remove_item(self):
        """
        Expected behaviour : In this test, we remove one element in choices and one in subquestions for first question. We remove one
        element in subquestion choices for the second question. Removed elements have to be deleted. @return:
        """
        self.import_sheet(self.get_last_script(), "main_file_all_lang")
        self.import_sheet(self.get_last_script(), "removing_one_item")
        self.scenarios(choices_count=2)

    def test_remove_items(self):
        """
        Expected behaviour : Same as previous test but with TWO items removed
        """
        self.import_sheet(self.get_last_script(), "main_file_all_lang")
        self.import_sheet(self.get_last_script(), "removing_two_items")
        self.scenarios(choices_count=1)

    def test_add_item(self):
        """
        Expected behaviour : In this test, we add one element in choices and one in subquestions for first question. We add one
        element in subquestion choices for the second question. @return:
        """
        print("hereeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        self.import_sheet(self.get_last_script(), "main_file_all_lang")
        self.import_sheet(self.get_last_script(), "adding_one_item")
        self.scenarios(choices_count=4)

    def test_add_items(self):
        """
        Expected behaviour : Same as previous test but with TWO items removed
        """
        self.import_sheet(self.get_last_script(), "main_file_all_lang")
        self.import_sheet(self.get_last_script(), "adding_two_items")
        self.scenarios(choices_count=5)

    def test_missing_translation_choices(self):
        """
        Expected behaviour : If number of choices are different depending on the language, script should crash
        """
        try:
            self.import_sheet(self.get_last_script(), "missing_one_lang_choices")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual(
                "not all lists have same length! (choices Question 2021001)",
                e.__str__(),
            )

    def test_missing_translation_subquestions(self):
        """
        Expected behaviour : If number of subquestions are different depending on the language, script should crash
        """
        try:
            self.import_sheet(self.get_last_script(), "missing_one_lang_subquestions")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual(
                "not all lists have same length! (subquestions Question 2021001)",
                e.__str__(),
            )

    def test_missing_translation_subchoices(self):
        """
        Expected behaviour : If number of subquestion_choices are different depending on the language, script should
        crash
        """
        try:
            self.import_sheet(self.get_last_script(), "missing_one_lang_subchoices")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual(
                "not all lists have same length! (sub_choices Question 2021001, Subquestion subfr21)",
                e.__str__(),
            )

    def test_missing_mark(self):
        """
        Expected behaviour : If number of marks are lower than answer choices
        """
        try:
            self.import_sheet(self.get_last_script(), "missing_mark")
            self.fail("Import should have failed")
        except IndexError as e:
            self.assertEqual(
                "list index out of range",
                e.__str__(),
            )

    def test_unexpected_mark(self):
        """
        Expected behaviour : If number of marks are greater than answer choices
        """
        try:
            self.import_sheet(self.get_last_script(), "unexpected_mark")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual(
                "There are not the same number of points and choices for question 2021000",
                e.__str__(),
            )

    def test_missing_subquestion_point(self):
        """
        Expected behaviour : If number of marks are lower than answer choices
        """
        try:
            self.import_sheet(self.get_last_script(), "missing_subquestion_point")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual(
                "Question 2021001: Number of subquestion points is different of number of subquestion choices",
                e.__str__(),
            )

    def test_unexpected_subquestion_point(self):
        """
        Expected behaviour : If number of marks are greater than answer choices
        """
        try:
            self.import_sheet(self.get_last_script(), "unexpected_subquestion_point")
            self.fail("Import should have failed")
        except ValueError as e:
            self.assertEqual(
                "Question 2021001: Number of subquestion points is different of number of subquestion choices",
                e.__str__(),
            )


class MultiEntitiesTest(TestCaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(MultiEntitiesTest, cls).setUpClass()
        # Categories
        cls.make_categories()

        # Sheet
        name = "Sheet Type"
        sheet_path = "csv/diag/questionnaire_diag_20240527_1005.csv"
        sheet, sheet_type = cls.make_sheet_diag(name, sheet_path)

        slug = "others"
        name_fr = "Autre - précisez"
        name_en = "Others"
        business_line = cls.make_business_line(slug, name_fr, name_en)

        # Structure
        juridic_name = "Multi Structure"
        slug = "multi-structure-structure"
        workforce = 10000
        category = "Diversity"
        cls.s = cls.make_structure(
            juridic_name, slug, workforce, category, business_line
        )

        # Niveaux d'entités
        e_lvl_0 = cls.make_entity_level(cls.s, "Groupe", 0)
        e_lvl_1 = cls.make_entity_level(cls.s, "Région", 1)
        e_lvl_2 = cls.make_entity_level(cls.s, "Pays", 2)

        # Entités
        cls.entity_ms = cls.make_entity(cls.s.juridic_name, e_lvl_0, cls.s.workforce)

        cls.entity_as = cls.make_entity("Asie", e_lvl_1, 3000, cls.entity_ms)
        cls.entity_us = cls.make_entity("Amérique", e_lvl_1, 2000, cls.entity_ms)
        cls.entity_eu = cls.make_entity("Europe", e_lvl_1, 5000, cls.entity_ms)

        cls.entity_ch = cls.make_entity("Chine", e_lvl_2, 1500, cls.entity_as)
        cls.entity_ja = cls.make_entity("Japon", e_lvl_2, 1000, cls.entity_as)
        cls.entity_la = cls.make_entity("Laos", e_lvl_2, 500, cls.entity_as)
        cls.entity_fr = cls.make_entity("France", e_lvl_2, 3000, cls.entity_eu)
        cls.entity_es = cls.make_entity("Espagne", e_lvl_2, 1500, cls.entity_eu)
        cls.entity_it = cls.make_entity("Italie", e_lvl_2, 450, cls.entity_eu)
        cls.entity_de = cls.make_entity("Allemagne", e_lvl_2, 50, cls.entity_eu)

        # User
        u = cls.make_common_user()

        # Subscription Type
        label = "Mixity Diag"
        pme_label = "Mixity Diag"
        slug = "diag"
        order = 1
        desc = ""
        sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)
        # Subscription
        subscription = cls.make_subscription(sheet_type, sub_type, cls.s)
        sub_pack = cls.make_subscription_pack(datetime.date.today(), cls.s)
        product = cls.make_product(label, "diag", sheet_type)
        sub_opt = cls.make_subscription_option(sub_pack, product.slug)

        # Membership
        cls.make_membership(u, cls.s)

        # Attributes
        cls.user = u
        cls.scoring_client = Client()

        cls.ms_eval = Evaluation.objects.create(
            sheet=sheet, entity=cls.entity_ms, subscription=subscription
        )
        cls.ms_eval.generate_answers()
        cls.eu_eval = Evaluation.objects.create(
            sheet=sheet, entity=cls.entity_eu, subscription=subscription
        )
        cls.eu_eval.generate_answers()
        cls.fr_eval = Evaluation.objects.create(
            sheet=sheet, entity=cls.entity_fr, subscription=subscription
        )
        cls.fr_eval.generate_answers()
        cls.es_eval = Evaluation.objects.create(
            sheet=sheet, entity=cls.entity_es, subscription=subscription
        )
        cls.es_eval.generate_answers()

    @csrf_exempt
    def get_page(self, path, args):
        path = reverse(path, args=args)
        response = self.scoring_client.get(
            path,
        )
        self.assertEqual(response.status_code, 200)

    @csrf_exempt
    def get_page_redirect(self, path, args):
        path = reverse(path, args=args)
        response = self.scoring_client.get(
            path,
        )
        self.assertEqual(response.status_code, 302)

    @csrf_exempt
    def post_form(self, path, args, data):
        path = reverse(path, args=args)
        response = self.scoring_client.post(
            path,
            data=data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "None")  # None = same url

    def test_access_to_any_entities_dashboard(self):
        self.get_page_redirect("home", args=[self.entity_fr.slug])
        self.get_page_redirect(
            "dashboard:dashboard_assess",
            args=[
                self.entity_fr.slug,
                self.fr_eval.subscription.subscription_type.slug,
                self.fr_eval.display_version_slugified,
            ],
        )
        self.scoring_client.force_login(self.user)
        with self.assertNumQueries(39):
            self.get_page("home", args=[self.entity_fr.slug])

    ## Will correct this test once the refacto on the questionnaire will be done ##
    # def test_multi_aggregation(self):
    #     self.scoring_client.force_login(self.user)
    #     # Will fill some fr and es questions
    #     q1 = Question.objects.get(google_sheets_id=20236001)  # Date
    #     q2 = Question.objects.get(google_sheets_id=20236002)  # Subquestion (sum)
    #     q3 = Question.objects.get(google_sheets_id=20236003)  # Sum
    #     q4 = Question.objects.get(google_sheets_id=20236016)  # Avg
    #     q5 = Question.objects.get(google_sheets_id=20236169)  # QCM
    #     q6 = Question.objects.get(google_sheets_id=20236168)  # Subquestion QCM
    #     sq = q2.subquestions.all()
    #     sq1 = q6.subquestions.all()
    #     # Initialising data to post
    #     data_cases_all = [
    #         {
    #             f"question_{q1.id}": "2023",
    #             f"question_{q2.id}_sub_{sq[0].id}": "50",
    #             f"question_{q2.id}_sub_{sq[1].id}": "40",
    #             f"question_{q2.id}_sub_{sq[2].id}": "30",
    #             f"question_{q2.id}_sub_{sq[3].id}": "20",
    #             f"question_{q2.id}_sub_{sq[4].id}": "50",
    #             f"question_{q2.id}_sub_{sq[5].id}": "40",
    #             f"question_{q2.id}_sub_{sq[6].id}": "30",
    #             f"question_{q2.id}_sub_{sq[7].id}": "20",
    #             f"question_{q2.id}_sub_{sq[8].id}": "50",
    #             f"question_{q2.id}_sub_{sq[9].id}": "40",
    #             f"question_{q2.id}_sub_{sq[10].id}": "30",
    #             f"question_{q2.id}_sub_{sq[11].id}": "20",
    #             f"question_{q3.id}": "50",
    #         },
    #         {
    #             f"question_{q1.id}": "2022",
    #             f"question_{q2.id}_sub_{sq[0].id}": "25",
    #             f"question_{q2.id}_sub_{sq[1].id}": "20",
    #             f"question_{q2.id}_sub_{sq[2].id}": "10",
    #             f"question_{q2.id}_sub_{sq[3].id}": "5",
    #             f"question_{q2.id}_sub_{sq[4].id}": "25",
    #             f"question_{q2.id}_sub_{sq[5].id}": "20",
    #             f"question_{q2.id}_sub_{sq[6].id}": "10",
    #             f"question_{q2.id}_sub_{sq[7].id}": "5",
    #             f"question_{q2.id}_sub_{sq[8].id}": "25",
    #             f"question_{q2.id}_sub_{sq[9].id}": "20",
    #             f"question_{q2.id}_sub_{sq[10].id}": "10",
    #             f"question_{q2.id}_sub_{sq[11].id}": "5",
    #             f"question_{q3.id}": "110",
    #         },
    #     ]
    #     data_cases_gender = [
    #         {
    #             f"question_{q5.id}": str(q5.choices.get(value=5).id),
    #             f"question_{q6.id}_sub_{sq1[0].id}": "1",
    #             f"question_{q6.id}_sub_{sq1[3].id}": "1",
    #             f"question_{q6.id}_sub_{sq1[7].id}": "1",
    #         },
    #         {
    #             f"question_{q5.id}": str(q5.choices.get(value=1).id),
    #             f"question_{q6.id}_sub_{sq1[0].id}": "1",
    #             f"question_{q6.id}_sub_{sq1[1].id}": "1",
    #             f"question_{q6.id}_sub_{sq1[4].id}": "1",
    #             f"question_{q6.id}_sub_{sq1[7].id}": "1",
    #         },
    #     ]
    #
    #     # Filling answers for french evaluation
    #     self.post_form(
    #         "evaluation_fill",
    #         [self.fr_eval.id, "all", "chiffres", 0],
    #         data_cases_all[0],
    #     )
    #     self.post_form(
    #         "evaluation_fill",
    #         [self.fr_eval.id, "all", "chiffres", 2],
    #         {f"question_{q4.id}": "50"},
    #     )
    #     self.post_form(
    #         "evaluation_fill",
    #         [self.fr_eval.id, "gender", "work-life-balance", 0],
    #         data_cases_gender[0],
    #     )
    #
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q1.id, evaluation=self.fr_eval).value,
    #         2023,
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q1.id, evaluation=self.eu_eval).value,
    #         None,
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q3.id, evaluation=self.fr_eval).value, 50
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q3.id, evaluation=self.eu_eval).value, 50
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q4.id, evaluation=self.fr_eval).value, 50
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q4.id, evaluation=self.eu_eval).value, 50
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q5.id, evaluation=self.fr_eval).choice.value,
    #         5,
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q5.id, evaluation=self.eu_eval).choice.value,
    #         5,
    #     )
    #
    #     # Filling answers for spain evaluation
    #     self.post_form(
    #         "evaluation_fill",
    #         [self.es_eval.id, "all", "chiffres", 0],
    #         data_cases_all[1],
    #     )
    #     self.post_form(
    #         "evaluation_fill",
    #         [self.es_eval.id, "all", "chiffres", 2],
    #         {f"question_{q4.id}": "80"},
    #     )
    #     self.post_form(
    #         "evaluation_fill",
    #         [self.es_eval.id, "gender", "work-life-balance", 0],
    #         data_cases_gender[1],
    #     )
    #
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q1.id, evaluation=self.es_eval).value,
    #         2022,
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q1.id, evaluation=self.eu_eval).value,
    #         None,
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q3.id, evaluation=self.es_eval).value, 110
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q3.id, evaluation=self.eu_eval).value, 160
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q4.id, evaluation=self.es_eval).value, 80
    #     )
    #     self.assertEqual(
    #         round(Answer.objects.get(question_id=q4.id, evaluation=self.eu_eval).value),
    #         60,
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q5.id, evaluation=self.fr_eval).choice.value,
    #         5,
    #     )
    #     self.assertEqual(
    #         Answer.objects.get(question_id=q5.id, evaluation=self.eu_eval).choice.value,
    #         4,
    #     )
    #     subanswers = Answer.objects.get(
    #         question_id=q2.id, evaluation=self.ms_eval
    #     ).subanswers.all()
    #     self.assertEqual(subanswers[0].value, 75)
    #     self.assertEqual(subanswers[1].value, 60)
    #     self.assertEqual(subanswers[2].value, 40)
    #     self.assertEqual(subanswers[3].value, 25)
    #     self.assertEqual(subanswers[4].value, 75)
    #     self.assertEqual(subanswers[5].value, 60)
    #     self.assertEqual(subanswers[6].value, 40)
    #     self.assertEqual(subanswers[7].value, 25)
    #     self.assertEqual(subanswers[8].value, 75)
    #     self.assertEqual(subanswers[9].value, 60)
    #     self.assertEqual(subanswers[10].value, 40)
    #     self.assertEqual(subanswers[11].value, 25)
    #     subanswers = Answer.objects.get(
    #         question_id=q6.id, evaluation=self.ms_eval
    #     ).subanswers.all()
    #     self.assertEqual(subanswers[0].value, 1)
    #     self.assertEqual(subanswers[1].value, 0)
    #     self.assertEqual(subanswers[2].value, 0)
    #     self.assertEqual(subanswers[3].value, 1)
    #     self.assertEqual(subanswers[4].value, 0)
    #     self.assertEqual(subanswers[5].value, 0)
    #     self.assertEqual(subanswers[6].value, 0)
    #     self.assertEqual(subanswers[7].value, 1)
    #     self.assertEqual(subanswers[8].value, 0)


# class ScoreCategorySiblingTest(TestCaseMixin, TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super(ScoreCategorySiblingTest, cls).setUpClass()
#         # Categories
#         cls.make_categories()

#         # BusinessLine
#         slug = "others"
#         name_fr = "Autre - précisez"
#         name_en = "Others"
#         business_line = cls.make_business_line(slug, name_fr, name_en)

#         # Structure
#         juridic_name = "My Structure"
#         slug = "my_structure"
#         workforce = 100
#         category = "Diversity"
#         s = cls.make_structure(juridic_name, slug, workforce, category, business_line)
#         e_lvl_0 = cls.make_entity_level(s, "Groupe", 0)
#         entity = cls.make_entity(s.juridic_name, e_lvl_0, s.workforce)

#         def create_subscription_type(type):
#             # Sheet
#             name = "Sheet Type"
#             sheet_path = "csv/startflash/questionnaire_startflash_20240527_1005.csv"
#             sheet, sheet_type = cls.make_sheet_start(name, sheet_path)

#             # Subscription Type
#             label = "Mixity Start"
#             pme_label = "Mixity Start"
#             slug = "mixity_start"
#             order = 4
#             desc = "L'évaluation instantanée pour débuter votre politique de diversité et inclusion"
#             sub_type = cls.make_subscription_type(label, pme_label, slug, order, desc)
#             # Subscription
#             subscription = cls.make_subscription(sheet_type, sub_type, s)
#             sub_pack = cls.make_subscription_pack(datetime.date.today(), s)
#             product = cls.make_product(label, type, sheet_type)
#             sub_opt = cls.make_subscription_option(sub_pack, product.slug)
#             QuestionSheetType.objects.filter(slug="mixity_start").update(slug=type)
#             QuestionSheet.objects.filter(slug="mixity_start").update(slug=type)
#             SubscriptionType.objects.filter(slug="mixity_start").update(slug=type)
#             subscription.refresh_from_db()
#             sheet.refresh_from_db()
#             logger.exception(subscription.subscription_type.slug)
#             return subscription, sheet

#         human_subscription, human_sheet = create_subscription_type("human")
#         international_subscription, international_sheet = create_subscription_type(
#             "international"
#         )
#         global_subscription, global_sheet = create_subscription_type("global")
#         start_subscription, start_sheet = create_subscription_type("mixity_start")
#         human_subscription2 = cls.make_subscription(
#             QuestionSheetType.objects.get(slug="human"),
#             SubscriptionType.objects.get(slug="human"),
#             s,
#         )
#         start_subscription2 = cls.make_subscription(
#             QuestionSheetType.objects.get(slug="mixity_start"),
#             SubscriptionType.objects.get(slug="mixity_start"),
#             s,
#         )
#         global_subscription2 = cls.make_subscription(
#             QuestionSheetType.objects.get(slug="global"),
#             SubscriptionType.objects.get(slug="global"),
#             s,
#         )

#         # User
#         u = cls.make_common_user()

#         # Membership
#         cls.make_membership(u, s)
#         cls.make_entity_membership(u, entity)

#         # Attributes
#         cls.e6 = Evaluation.objects.create(
#             sheet=start_sheet,
#             is_validated_by_admin=True,
#             entity=entity,
#             subscription=start_subscription,
#         )
#         cls.e6.modified_by_user_date = datetime.datetime.fromtimestamp(
#             0, tz=timezone.get_default_timezone()
#         )
#         cls.e6.save()
#         cls.e6.generate_answers()

#         # Attributes
#         cls.e = Evaluation.objects.create(
#             sheet=human_sheet,
#             entity=entity,
#             is_validated_by_admin=True,
#             subscription=human_subscription,
#         )
#         cls.e.generate_answers()
#         cls.e.modified_by_user_date = datetime.datetime.fromtimestamp(
#             2, tz=timezone.get_default_timezone()
#         )
#         cls.e.save()

#         cls.e2 = Evaluation.objects.create(
#             sheet=international_sheet,
#             entity=entity,
#             is_validated_by_admin=True,
#             subscription=international_subscription,
#         )
#         cls.e2.generate_answers()
#         cls.e2.modified_by_user_date = datetime.datetime.fromtimestamp(
#             12, tz=timezone.get_default_timezone()
#         )
#         cls.e2.save()

#         cls.e3 = Evaluation.objects.create(
#             sheet=global_sheet,
#             entity=entity,
#             is_validated_by_admin=True,
#             subscription=global_subscription,
#         )
#         cls.e3.generate_answers()
#         cls.e3.modified_by_user_date = datetime.datetime.fromtimestamp(
#             15, tz=timezone.get_default_timezone()
#         )
#         cls.e3.save()

#         cls.e4 = Evaluation.objects.create(
#             sheet=human_sheet,
#             entity=entity,
#             is_validated_by_admin=True,
#             subscription=human_subscription2,
#         )
#         cls.e4.generate_answers()
#         cls.e4.modified_by_user_date = datetime.datetime.fromtimestamp(
#             20, tz=timezone.get_default_timezone()
#         )
#         cls.e4.save()
#         cls.e5 = Evaluation.objects.create(
#             sheet=global_sheet,
#             entity=entity,
#             is_validated_by_admin=True,
#             subscription=global_subscription2,
#         )
#         cls.e5.generate_answers()
#         cls.e5.modified_by_user_date = datetime.datetime.fromtimestamp(
#             30, tz=timezone.get_default_timezone()
#         )
#         cls.e5.save()

#         cls.e7 = Evaluation.objects.create(
#             sheet=start_sheet,
#             entity=entity,
#             is_validated_by_admin=True,
#             subscription=start_subscription2,
#         )
#         cls.e7.generate_answers()
#         cls.e7.modified_by_user_date = datetime.datetime.fromtimestamp(
#             35, tz=timezone.get_default_timezone()
#         )
#         cls.e7.save()
#         cls.user = u

#     def test_human_no_sibling(self):
#         self.assertEqual(self.e.scores_categories.first().sibling, None)

#     def test_global_no_sibling(self):
#         self.assertEqual(self.e2.scores_categories.first().sibling, None)

#     def test_global_sibling(self):
#         self.assertEqual(
#             self.e3.scores_categories.first().sibling.evaluation.pk, self.e2.pk
#         )

#     def test_human_sibling(self):
#         self.assertEqual(
#             self.e4.scores_categories.first().sibling.evaluation.pk, self.e.pk
#         )

#     def test_global_sibling2(self):
#         self.assertEqual(
#             self.e5.scores_categories.first().sibling.evaluation.pk, self.e3.pk
#         )

#     def test_start_no_sibling(self):
#         self.assertEqual(self.e6.scores_categories.first().sibling, None)

#     def test_start(self):
#         self.assertEqual(
#             self.e7.scores_categories.first().sibling.evaluation.pk, self.e6.pk
#         )
