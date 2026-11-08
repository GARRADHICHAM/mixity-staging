import datetime
from django.apps import apps
from mixity.testing import TestCase
from smart_testing.testcase import TestCaseMixin
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.test import Client, RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import AnonymousUser

from mixity.dashboard.views_api import ApiHandleCollaboratorsList

from lead.models import Objective
from accounts.models import (
    HumanCriteria,
)
from scoring.models import (
    Category,
    SubCategory,
    Evaluation,
    Aim,
    MixityUser,
)
from accounts.vocabularies import ACTION_STATUS, UNIT_CHOICE
from mixity.dashboard import views_api


class HomeTest(TestCaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(HomeTest, cls).setUpClass()
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
        cls.e = cls.make_entity(cls.s.juridic_name, e_lvl_0, cls.s.workforce)

        # User
        u = cls.make_common_user()
        u_not_member = cls.make_user(
            "user_not_member@test.com", "NOT_MEMBER45682", "Not_Member_User"
        )

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
        cls.make_entity_membership(u, cls.e)

        # Objective
        label = "Test objectif 1"
        category = "Transversal"
        subcategory = "Sensibilisation"
        cls.obj = cls.make_objective(label, category, subcategory, cls.s)

        # Action
        label = "First Action"
        status = ACTION_STATUS[0][0]
        budget = 2000
        referent = u
        cls.action = cls.make_action(label, status, budget, referent, cls.obj)

        # ActionKpi
        label = "Nombre de personne sensibilisées"
        unit = UNIT_CHOICE[0][0]
        goal = 150
        cls.actionkpi = cls.make_actionkpi(
            label, unit, goal, category, subcategory, cls.action
        )

        # GenericKpi
        label = "Nombre d'étudiants sensibilisés"
        unit = UNIT_CHOICE[0][0]
        cls.generickpi = cls.make_generickpi(label, unit, category, subcategory)

        # Attributes
        cls.user = u
        cls.user_not_member = u_not_member
        cls.home_client = Client()
        cls.factory = APIRequestFactory()

    @csrf_exempt
    def get_api_request(self, path, view, user, nb_requests, code):
        with self.assertNumQueries(nb_requests):
            request = self.factory.get(path)
            request.user = user
            response = view(request, slug=self.e.slug)
            self.assertEqual(response.status_code, code)

    @csrf_exempt
    def get_page(self, path, args, nb_requests, code):
        with self.assertNumQueries(nb_requests):
            path = reverse(path, args=args)
            response = self.home_client.get(
                path,
            )
            self.assertEqual(response.status_code, code)

    def test_home_pages_anonymous_user(self):
        self.home_client.user = AnonymousUser()
        self.get_page(
            "home",
            args=[self.e.slug],
            nb_requests=1,
            code=302,
        )

    def test_home_pages_not_member(self):
        self.home_client.force_login(self.user_not_member)
        self.get_page(
            "home",
            args=[self.e.slug],
            nb_requests=13,
            code=403,
        )

    def test_home_pages_member(self):
        self.home_client.force_login(self.user)
        self.get_page(
            "home",
            args=[self.e.slug],
            nb_requests=37,
            code=200,
        )

    def test_home_api_routes_anonymous_user(self):
        self.home_client.user = AnonymousUser()
        self.get_page(
            "api_membership",
            args=[self.e.slug],
            nb_requests=0,
            code=302,
        )
        self.get_page("dashboard:api_url", args=[self.e.slug], nb_requests=0, code=302)
        self.get_api_request(
            self.e.slug + "/api/structure",
            views_api.ApiStructure.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            self.e.slug + "/api/category",
            views_api.ApiCategory.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        # self.get_api_request(
        #     self.e.slug + "/api/global-evaluation",
        #     views_api.ApiGlobalEvaluation.as_view({"get": "list"}),
        #     AnonymousUser(),
        #     nb_requests=0,
        #     code=302,
        # )
        # self.get_api_request(
        #     self.e.slug + "/api/human-evaluation",
        #     views_api.ApiHumanEvaluation.as_view({"get": "list"}),
        #     AnonymousUser(),
        #     nb_requests=0,
        #     code=302,
        # )
        self.get_api_request(
            self.e.slug + "/api/action",
            views_api.ApiAction.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            self.e.slug + "/api/first-five-actions",
            views_api.ApiFirstFiveAction.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            self.e.slug + "/api/solution",
            views_api.ApiSolution.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            self.e.slug + "/api/first-five-solutions",
            views_api.ApiFirstFiveSolution.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )

    def test_home_api_routes_not_member(self):
        self.home_client.force_login(self.user_not_member)
        self.get_page(
            "api_membership",
            args=[self.e.slug],
            nb_requests=10,
            code=403,
        )
        self.get_page("dashboard:api_url", args=[self.e.slug], nb_requests=8, code=403)
        # self.get_api_request(
        #     self.e.slug + "/api/structure",
        #     views_api.ApiStructure.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     self.e.slug + "/api/category",
        #     views_api.ApiCategory.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     self.e.slug + "/api/global-evaluation",
        #     views_api.ApiGlobalEvaluation.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     self.e.slug + "/api/human-evaluation",
        #     views_api.ApiHumanEvaluation.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     self.e.slug + "/api/action",
        #     views_api.ApiAction.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     self.e.slug + "/api/first-five-actions",
        #     views_api.ApiFirstFiveAction.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     self.e.slug + "/api/solution",
        #     views_api.ApiSolution.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     self.e.slug + "/api/first-five-solutions",
        #     views_api.ApiFirstFiveSolution.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )

    def test_home_api_routes_member(self):
        self.home_client.force_login(self.user)
        self.get_page(
            "api_membership",
            args=[self.e.slug],
            nb_requests=9,
            code=200,
        )
        self.get_page("dashboard:api_url", args=[self.e.slug], nb_requests=6, code=200)
        self.get_api_request(
            self.e.slug + "/api/structure",
            views_api.ApiStructure.as_view({"get": "list"}),
            self.user,
            nb_requests=11,
            code=200,
        )
        self.get_api_request(
            self.e.slug + "/api/category",
            views_api.ApiCategory.as_view({"get": "list"}),
            self.user,
            nb_requests=11,
            code=200,
        )
        # self.get_api_request(
        #     self.e.slug + "/api/global-evaluation",
        #     views_api.ApiGlobalEvaluation.as_view({"get": "list"}),
        #     self.user,
        #     nb_requests=5,
        #     code=200,
        # )
        # self.get_api_request(
        #     self.e.slug + "/api/human-evaluation",
        #     views_api.ApiHumanEvaluation.as_view({"get": "list"}),
        #     self.user,
        #     nb_requests=7,
        #     code=200,
        # )
        self.get_api_request(
            self.e.slug + "/api/action",
            views_api.ApiAction.as_view({"get": "list"}),
            self.user,
            nb_requests=5,
            code=200,
        )
        self.get_api_request(
            self.e.slug + "/api/first-five-actions",
            views_api.ApiFirstFiveAction.as_view({"get": "list"}),
            self.user,
            nb_requests=5,
            code=200,
        )
        self.get_api_request(
            self.e.slug + "/api/solution",
            views_api.ApiSolution.as_view({"get": "list"}),
            self.user,
            nb_requests=4,
            code=200,
        )
        self.get_api_request(
            self.e.slug + "/api/first-five-solutions",
            views_api.ApiFirstFiveSolution.as_view({"get": "list"}),
            self.user,
            nb_requests=4,
            code=200,
        )


class CollaboratorApiTest(TestCaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(CollaboratorApiTest, cls).setUpClass()
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
        cls.e = cls.make_entity(cls.s.juridic_name, e_lvl_0, cls.s.workforce)

        # User
        u = cls.make_common_user()
        u_not_member = cls.make_user(
            "user_not_member@test.com", "NOT_MEMBER45682", "Not_Member_User"
        )

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
        cls.make_entity_membership(u, cls.e)

        # Create Evaluation
        cls.make_evaluation(cls.e, sheet, subscription)

        # Objective
        label = "Test objectif 1"
        category = "Transversal"
        subcategory = "Sensibilisation"
        cls.obj = cls.make_objective(label, category, subcategory, cls.s)

        # Action
        label = "First Action"
        status = ACTION_STATUS[0][0]
        budget = 2000
        referent = u
        cls.action = cls.make_action(label, status, budget, referent, cls.obj)

        # ActionKpi
        label = "Nombre des personnes sensibilisées"
        unit = UNIT_CHOICE[0][0]
        goal = 150
        cls.actionkpi = cls.make_actionkpi(
            label, unit, goal, category, subcategory, cls.action
        )

        # GenericKpi
        label = "Nombre d'étudiants sensibilisés"
        unit = UNIT_CHOICE[0][0]
        cls.generickpi = cls.make_generickpi(label, unit, category, subcategory)

        # Attributes
        cls.user = u
        cls.user_not_member = u_not_member
        cls.home_client = Client()
        cls.factory = APIRequestFactory()

        # All CSV files
        cls.valid_file = open("mixity/static/csv/collaborators_lists/valid.csv").read()
        cls.empty_file = open(
            "mixity/static/csv/collaborators_lists/really_empty.csv"
        ).read()
        cls.only_mandatory_columns_file = open(
            "mixity/static/csv/collaborators_lists/only_mandatory_columns.csv"
        ).read()
        cls.bad_collaborators_name_file = open(
            "mixity/static/csv/collaborators_lists/bad_collaborators_name.csv"
        ).read()
        cls.no_mandatory_columns_file = open(
            "mixity/static/csv/collaborators_lists/no_mandatory_columns.csv"
        ).read()
        cls.bad_emails_format_file = open(
            "mixity/static/csv/collaborators_lists/bad_emails_format.csv"
        ).read()

    @csrf_exempt
    def get_api_request(
        self, path, evaluation_pk, file_content, view, user, nb_requests, code
    ):
        with self.assertNumQueries(nb_requests):
            request = self.factory.post(path, {"file_content": file_content})
            request.user = user
            response = view(request, slug=self.e.slug, evaluation_pk=evaluation_pk)
            self.assertEqual(response.status_code, code)

    @csrf_exempt
    def test_upload_valid_csv(self):
        u = MixityUser.objects.filter(email__icontains="example")
        e = Evaluation.objects.get(entity=self.e)
        h = HumanCriteria.objects.filter(evaluation=e)
        self.assertEqual(h.count(), 0)
        self.get_api_request(
            self.e.slug + "/api/handle-collaborators-list/",
            e.pk,
            self.valid_file,
            views_api.ApiHandleCollaboratorsList.as_view(),
            self.user,
            nb_requests=89,
            code=200,
        )
        u = MixityUser.objects.filter(email__icontains="example")
        e = Evaluation.objects.get(entity=self.e)
        h = HumanCriteria.objects.filter(evaluation=e)
        self.assertEqual(h.count(), 3)
        self.assertEqual(u.count(), 3)

    @csrf_exempt
    def test_upload_empty_csv(self):
        e = Evaluation.objects.get(entity=self.e)
        self.get_api_request(
            self.e.slug + "/api/handle-collaborators-list/",
            e.pk,
            self.empty_file,
            views_api.ApiHandleCollaboratorsList.as_view(),
            self.user,
            nb_requests=2,
            code=400,
        )

    @csrf_exempt
    def test_upload_only_mandatory_columns_csv(self):
        e = Evaluation.objects.get(entity=self.e)
        self.get_api_request(
            self.e.slug + "/api/handle-collaborators-list/",
            e.pk,
            self.only_mandatory_columns_file,
            views_api.ApiHandleCollaboratorsList.as_view(),
            self.user,
            nb_requests=408,
            code=200,
        )

    @csrf_exempt
    def test_upload_no_mandatory_columns_csv(self):
        e = Evaluation.objects.get(entity=self.e)
        self.get_api_request(
            self.e.slug + "/api/handle-collaborators-list/",
            e.pk,
            self.no_mandatory_columns_file,
            views_api.ApiHandleCollaboratorsList.as_view(),
            self.user,
            nb_requests=2,
            code=400,
        )

    @csrf_exempt
    def test_upload_bad_emails_format_csv(self):
        e = Evaluation.objects.get(entity=self.e)
        self.get_api_request(
            self.e.slug + "/api/handle-collaborators-list/",
            e.pk,
            self.bad_emails_format_file,
            views_api.ApiHandleCollaboratorsList.as_view(),
            self.user,
            nb_requests=2,
            code=400,
        )
