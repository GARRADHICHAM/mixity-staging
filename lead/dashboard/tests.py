import datetime
from django.apps import apps
from mixity.testing import TestCase
from smart_testing.testcase import TestCaseMixin
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.test import Client, RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import AnonymousUser

from lead.models import Objective
from scoring.models import Category, SubCategory, Evaluation, Aim
from accounts.vocabularies import ACTION_STATUS, UNIT_CHOICE
from lead.dashboard import views


class LeadTest(TestCaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(LeadTest, cls).setUpClass()
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

        # Objective
        label = "Test objectif 1"
        category = "Transversal"
        subcategory = "Sensibilisation"
        cls.obj = cls.make_objective(label, category, subcategory, cls.s)

        # Action
        label = "First Action"
        status = ACTION_STATUS[0][0]
        budget = 2000
        referent = "Paul Martin"
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
        cls.lead_client = Client()
        cls.factory = APIRequestFactory()

    @csrf_exempt
    def get_api_request(self, path, view, user, nb_requests, code):
        with self.assertNumQueries(nb_requests):
            request = self.factory.get(path)
            request.user = user
            response = view(request, slug=self.s.slug)
            self.assertEqual(response.status_code, code)

    @csrf_exempt
    def get_page(self, path, args, nb_requests, code):
        with self.assertNumQueries(nb_requests):
            path = reverse(path, args=args)
            response = self.lead_client.get(
                path,
            )
            self.assertEqual(response.status_code, code)

    def test_lead_pages_anonymous_user(self):
        self.lead_client.user = AnonymousUser()
        self.get_page(
            "dashboard:lead:home", args=[self.s.slug], nb_requests=1, code=302
        )
        self.get_page(
            "dashboard:lead:overview", args=[self.s.slug], nb_requests=0, code=302
        )

    def test_lead_pages_not_member(self):
        self.lead_client.force_login(self.user_not_member)
        self.get_page(
            "dashboard:lead:home", args=[self.s.slug], nb_requests=9, code=403
        )
        self.get_page(
            "dashboard:lead:overview", args=[self.s.slug], nb_requests=7, code=403
        )

    def test_lead_pages_member(self):
        self.lead_client.force_login(self.user)
        self.get_page(
            "dashboard:lead:home", args=[self.s.slug], nb_requests=16, code=200
        )
        self.get_page(
            "dashboard:lead:overview", args=[self.s.slug], nb_requests=14, code=200
        )

    def test_lead_api_routes_anonymous_user(self):
        self.lead_client.user = AnonymousUser()
        self.get_page(
            "dashboard:lead:api_membership", args=[self.s.slug], nb_requests=0, code=302
        )
        self.get_page(
            "dashboard:lead:api_url", args=[self.s.slug], nb_requests=0, code=302
        )
        self.get_page(
            "dashboard:lead:api_overview_url",
            args=[self.s.slug],
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/objective",
            views.ApiObjective.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/aims_to_objectives",
            views.ApiCreateObjectiveFromEvaluation.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/overview/api/objective",
            views.ApiObjective.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/category",
            views.ApiCategory.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/overview/api/category",
            views.ApiCategory.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/action",
            views.ApiAction.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/overview/api/action",
            views.ApiAction.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/kpi",
            views.ApiKpi.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/generickpi",
            views.ApiGenericKpi.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/structure",
            views.ApiStructure.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/overview/api/structure",
            views.ApiStructure.as_view({"get": "list"}),
            AnonymousUser(),
            nb_requests=0,
            code=302,
        )

    def test_lead_api_routes_not_member(self):
        self.lead_client.force_login(self.user_not_member)
        self.get_page(
            "dashboard:lead:api_membership", args=[self.s.slug], nb_requests=9, code=403
        )
        self.get_page(
            "dashboard:lead:api_url", args=[self.s.slug], nb_requests=7, code=403
        )
        self.get_page(
            "dashboard:lead:api_overview_url",
            args=[self.s.slug],
            nb_requests=7,
            code=403,
        )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/api/objective",
        #     views.ApiObjective.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/api/aims_to_objectives",
        #     views.ApiCreateObjectiveFromEvaluation.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/overview/api/objective",
        #     views.ApiObjective.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/api/category",
        #     views.ApiCategory.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/overview/api/category",
        #     views.ApiCategory.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/api/action",
        #     views.ApiAction.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/overview/api/action",
        #     views.ApiAction.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/api/kpi",
        #     views.ApiKpi.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/api/generickpi",
        #     views.ApiGenericKpi.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/api/structure",
        #     views.ApiStructure.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )
        # self.get_api_request(
        #     "dashboard/" + self.s.slug + "/lead/overview/api/structure",
        #     views.ApiStructure.as_view({"get": "list"}),
        #     self.user_not_member,
        #     nb_requests=7,
        #     code=403,
        # )

    def test_lead_api_routes_member(self):
        self.lead_client.force_login(self.user)
        self.get_page(
            "dashboard:lead:api_membership",
            args=[self.s.slug],
            nb_requests=8,
            code=200,
        )
        self.get_page(
            "dashboard:lead:api_url", args=[self.s.slug], nb_requests=5, code=200
        )
        self.get_page(
            "dashboard:lead:api_overview_url",
            args=[self.s.slug],
            nb_requests=5,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/objective",
            views.ApiObjective.as_view({"get": "list"}),
            self.user,
            nb_requests=7,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/aims_to_objectives",
            views.ApiCreateObjectiveFromEvaluation.as_view({"get": "list"}),
            self.user,
            nb_requests=9,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/overview/api/objective",
            views.ApiObjective.as_view({"get": "list"}),
            self.user,
            nb_requests=7,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/category",
            views.ApiCategory.as_view({"get": "list"}),
            self.user,
            nb_requests=9,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/overview/api/category",
            views.ApiCategory.as_view({"get": "list"}),
            self.user,
            nb_requests=9,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/action",
            views.ApiAction.as_view({"get": "list"}),
            self.user,
            nb_requests=4,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/overview/api/action",
            views.ApiAction.as_view({"get": "list"}),
            self.user,
            nb_requests=4,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/kpi",
            views.ApiKpi.as_view({"get": "list"}),
            self.user,
            nb_requests=3,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/generickpi",
            views.ApiGenericKpi.as_view({"get": "list"}),
            self.user,
            nb_requests=3,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/api/structure",
            views.ApiStructure.as_view({"get": "list"}),
            self.user,
            nb_requests=3,
            code=200,
        )
        self.get_api_request(
            "dashboard/" + self.s.slug + "/lead/overview/api/structure",
            views.ApiStructure.as_view({"get": "list"}),
            self.user,
            nb_requests=3,
            code=200,
        )
