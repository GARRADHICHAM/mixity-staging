import datetime
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Membership
from act.forms import SolutionForm
from act.models import Solver, Solution
from mixity.testing import TestCase
from django.test import Client
from django.contrib import auth
from django.urls import reverse


from scoring.models import QuestionSheetType, Category, SubCategory
from django.core.files.uploadedfile import SimpleUploadedFile


class CreateStructureSolverTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(CreateStructureSolverTest, cls).setUpClass()

        # Categories
        cls.make_categories()

        # Sheet Type
        sheet_type = QuestionSheetType.objects.create(
            slug="mixity_evaluation_globale_pme",
            name="Evaluation Mixity Global",
            workforce_limit=500,
        )

        # BusinessLine
        slug = "others"
        name_fr = "Autre - précisez"
        name_en = "Others"
        businessLine = cls.make_business_line(slug, name_fr, name_en)

        # Structure
        juridic_name = "Structure Test"
        slug = "structure_test"
        workforce = 100
        category = "Diversity"
        s = cls.make_structure(juridic_name, slug, workforce, category, businessLine)

        # User
        u = cls.make_common_user()
        u_not_owner = cls.make_user(
            "user_not_owner@test.com", "NOT_OWNER45682", "Not_Owner_User"
        )

        # Subscription Type
        label = "Mixity Diag"
        pme_label = "Mixity Global"
        slug = "global"
        order = 4
        desc = ""
        sub = cls.make_subscription_type(label, pme_label, slug, order, desc)

        # Subscription
        subscription = cls.make_subscription(sheet_type, sub, s)
        sub_pack = cls.make_subscription_pack(datetime.date.today(), s)
        product = cls.make_product(label, "diag", sheet_type)
        sub_opt = cls.make_subscription_option(sub_pack, product.slug)

        # Membership
        Membership.objects.create(structure=s, user=u, is_owner=True)

        # Attributes
        cls.structure_customer = s
        cls.client = Client()
        cls.user_owner = u
        cls.user_not_owner = u_not_owner

    # def test_create_structure_solver_owner(self):

    #     # Forcing authentication
    #     self.client.force_login(self.user_owner)
    #     auth_user_owner = auth.get_user(self.client)

    #     # Testing if the user is already authenticated
    #     assert auth_user_owner.is_authenticated

    #     # Creating a new solver and Checking creation and redirection
    #     with self.assertNumQueries(6):
    #         response = self.client.post(
    #             reverse(
    #                 "dashboard:solver:create",
    #                 kwargs={"slug": self.structure_customer.slug},
    #             )
    #         )
    #     self.assertRedirects(
    #         response,
    #         expected_url=reverse(
    #             "dashboard:solver:home", kwargs={"slug": self.structure_customer.slug}
    #         ),
    #     )

    # def test_create_structure_solver_not_owner(self):

    #     # Forcing authentication
    #     self.client.force_login(self.user_not_owner)
    #     auth_user_not_owner = auth.get_user(self.client)

    #     # Testing if the user is already authenticated
    #     assert auth_user_not_owner.is_authenticated

    #     # Creating a new solver and Checking creation and redirection
    #     with self.assertNumQueries(7):
    #         response = self.client.post(
    #             reverse(
    #                 "dashboard:solver:create",
    #                 kwargs={"slug": self.structure_customer.slug},
    #             )
    #         )
    #     self.assertEqual(response.status_code, 403)


# class SolverInterfaceAdminTest(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super(SolverInterfaceAdminTest, cls).setUpClass()
#         # Categories
#         cls.make_categories()

#         # Sheet Type
#         sheet_type = QuestionSheetType.objects.create(
#             slug="mixity_evaluation_globale_pme",
#             name="Evaluation Mixity Global",
#             workforce_limit=500,
#         )

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

#         # Membership
#         Membership.objects.create(structure=s, user=u, is_owner=True)

#         # Solver
#         solver = cls.make_solver(s)

#         # Language
#         language = cls.make_language("fr", "Français", "French", "Francés")
#         language_update = cls.make_language("en", "Anglais", "English", "inglés")

#         # Keyword
#         keyword = cls.make_keyword("test-kw", "Test Keyword")
#         keyword_update = cls.make_keyword("test-kw-update", "Test Keyword Update")

#         # Solution to update
#         solution = cls.make_solution(
#             solver=solver,
#             title="test",
#             referent="Monsieur A",
#             email="monsieur.a@gmail.com",
#             category="Transversal",
#             subcategory="Sensibilisation",
#             summary="test",
#             country="FR",
#             region="FR-HDF",
#             description="test",
#             languages=[language.id],
#             price_desc="test",
#             keywords=[keyword.id],
#         )

#         # Attributes
#         cls.s = s
#         cls.solver = solver
#         cls.client = Client()
#         cls.user_owner = u
#         cls.language = language
#         cls.keyword = keyword
#         cls.solution = solution
#         cls.keyword_update = keyword_update
#         cls.language_update = language_update

#     def test_solutions_home_page(self):

#         # Forcing authentication
#         self.client.force_login(self.user_owner)
#         auth_user_owner = auth.get_user(self.client)

#         # Testing if the user is already authenticated
#         assert auth_user_owner.is_authenticated

#         with self.assertNumQueries(17):
#             path = reverse(
#                 "dashboard:solver:home",
#                 kwargs={"slug": self.solver.structure.slug},
#             )
#             response = self.client.get(path)
#         self.assertEqual(response.status_code, 200)

#     @csrf_exempt
#     def test_add_solution(self):

#         # Forcing authentication
#         self.client.force_login(self.user_owner)
#         auth_user_owner = auth.get_user(self.client)

#         # Testing if the user is already authenticated
#         assert auth_user_owner.is_authenticated

#         # Before creation
#         self.assertEqual(
#             Solution.objects.count(), 1
#         )  # 1 stands to the solution existed for others tests

#         # Creating a solution
#         data_form = {
#             "title": "Adding a solution test - title",
#             "summary": "Adding a solution test - summary",
#             "referent": "Monsieur B",
#             "email": "monsieur.b@gmail.com",
#             "categories": [Category.objects.get(name="Transversal").pk],
#             "subcategories": [
#                 SubCategory.objects.get(
#                     name="Sensibilisation", category__name="Transversal"
#                 ).pk
#             ],
#             "country": "FR",
#             "region": "FR-PDL",
#             "description": "Adding a solution test - description",
#             "languages": [self.language.id],
#             "price_desc": "Adding a solution test - price description",
#             "keywords": [self.keyword.id],
#         }
#         with self.assertNumQueries(26):
#             path = reverse(
#                 "dashboard:solver:add_solution",
#                 kwargs={"slug": self.solver.structure.slug},
#             )
#             response = self.client.post(path, data=data_form)

#         self.assertRedirects(
#             response,
#             expected_url=reverse(
#                 "dashboard:solver:home",
#                 kwargs={"slug": self.solver.structure.slug},
#             ),
#         )

#         # Before creation
#         self.assertEqual(Solution.objects.count(), 2)

#     @csrf_exempt
#     def test_update_solution(self):

#         # Forcing authentication
#         self.client.force_login(self.user_owner)
#         auth_user_owner = auth.get_user(self.client)

#         # Testing if the user is already authenticated
#         assert auth_user_owner.is_authenticated

#         # Before updating
#         self.assertEqual(self.solution.title, "test")
#         self.assertEqual(self.solution.summary, "test")
#         self.assertEqual(self.solution.description, "test")
#         self.assertEqual(self.solution.price_desc, "test")
#         self.assertEqual(self.solution.country, "FR")
#         self.assertEqual(self.solution.region, "FR-HDF")
#         self.assertEqual(self.solution.languages.first().id, self.language.id)
#         self.assertEqual(self.solution.keywords.first().id, self.keyword.id)

#         # Updating a solution
#         data_form = {
#             "title": "Adding a solution test - title - update",
#             "summary": "Adding a solution test - summary - update",
#             "referent": "Monsieur B",
#             "email": "monsieur.b@gmail.com",
#             "categories": [Category.objects.get(name="Transversal").pk],
#             "subcategories": [
#                 SubCategory.objects.get(
#                     name="Sensibilisation", category__name="Transversal"
#                 ).pk
#             ],
#             "description": "Adding a solution test - description - update",
#             "price_desc": "Adding a solution test - price desc - update",
#             "country": "CA",
#             "region": "",
#             "languages": [self.language_update.id],
#             "keywords": [self.keyword_update.id],
#         }

#         with self.assertNumQueries(24):
#             path = reverse(
#                 "dashboard:solver:update_solution",
#                 kwargs={"slug": self.solver.structure.slug, "id": self.solution.id},
#             )
#             response = self.client.post(path, data=data_form)
#         self.assertRedirects(
#             response,
#             expected_url=reverse(
#                 "dashboard:solver:home",
#                 kwargs={"slug": self.solver.structure.slug},
#             ),
#         )
#         self.solution.refresh_from_db()
#         # After updating
#         self.assertEqual(self.solution.title, "Adding a solution test - title - update")
#         self.assertEqual(
#             self.solution.summary, "Adding a solution test - summary - update"
#         )
#         self.assertEqual(
#             self.solution.description, "Adding a solution test - description - update"
#         )
#         self.assertEqual(
#             self.solution.price_desc, "Adding a solution test - price desc - update"
#         )
#         self.assertEqual(self.solution.country, "CA")
#         self.assertEqual(self.solution.region, None)
#         self.assertEqual(self.solution.languages.first().id, self.language_update.id)
#         self.assertEqual(self.solution.keywords.first().id, self.keyword_update.id)

#     @csrf_exempt
#     def test_delete_solution(self):

#         # Forcing authentication
#         self.client.force_login(self.user_owner)
#         auth_user_owner = auth.get_user(self.client)

#         # Testing if the user is already authenticated
#         assert auth_user_owner.is_authenticated

#         # Before deleting
#         self.assertEqual(Solution.objects.count(), 1)

#         # Deleting
#         with self.assertNumQueries(13):
#             path = reverse(
#                 "dashboard:solver:delete_solution",
#                 kwargs={"slug": self.solver.structure.slug, "id": self.solution.id},
#             )
#             response = self.client.post(path)
#         self.assertRedirects(
#             response,
#             expected_url=reverse(
#                 "dashboard:solver:home",
#                 kwargs={"slug": self.solver.structure.slug},
#             ),
#         )

#         # After deleting
#         self.assertEqual(Solution.objects.count(), 0)
