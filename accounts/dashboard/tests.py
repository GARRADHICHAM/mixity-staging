import datetime
from django.apps import apps
from mixity.testing import TestCase
from smart_testing.testcase import TestCaseMixin
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.test import Client, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.utils.text import slugify
from django.core.files.uploadedfile import SimpleUploadedFile

from lead.models import Objective
from scoring.models import Category, SubCategory, Evaluation, Aim, QuestionTag
from accounts.models import Entity, Structure, EntityLevel, BusinessLine
from accounts.vocabularies import ACTION_STATUS, UNIT_CHOICE


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
        u_not_owner = cls.make_user(
            "user_not_owner@test.com", "NOT_OWNER45682", "Not_Owner_User"
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
        cls.user_not_owner = u_not_owner
        cls.lead_client = Client()

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
            "dashboard:lead:home", args=[self.s.slug], nb_requests=0, code=302
        )

    def test_lead_pages_not_owner(self):
        self.lead_client.force_login(self.user_not_owner)
        self.get_page(
            "dashboard:lead:home", args=[self.s.slug], nb_requests=9, code=403
        )

    def test_lead_pages_owner(self):
        self.lead_client.force_login(self.user)
        self.get_page(
            "dashboard:lead:home", args=[self.s.slug], nb_requests=20, code=200
        )


class ApiUploadEntitiesCSVTest(TestCase):
    def setUp(self):
        # Configuration initiale pour les tests
        self.client = Client()
        self.url = reverse(
            "upload_entities_csv"
        )  # Assurez-vous que cette URL est correcte

        self.business_line = BusinessLine.objects.create(name="Tech")
        # Données pour la création de la structure
        structure_data = {
            "juridic_name": "Test Organisation",
            "commercial_name": "Test Organisation",
            "category": "Entreprise",
            "address": "123 Test St",
            "phone1": "123456789",
            "business_line": self.business_line,
            "workforce": 100,
            "website": "https://test.org",
            "slug": slugify("Test Organisation"),
            "duns": 123321123,
        }

        self.structure = Structure.objects.create(**structure_data)

        # Création de l'entity_level pour l'entité principale
        self.entity_level_main = EntityLevel.objects.create(
            structure=self.structure, level=0
        )

        # Création de l'entité principale
        entity_name = "Test Organisation-main"
        entity_slug = "test-organisation-main"
        self.entity = Entity.objects.create(
            name=entity_name,
            slug=entity_slug,
            entity_level=self.entity_level_main,
            workforce=self.structure.workforce,
            address=self.structure.address,
            phone=self.structure.phone1,
        )

        self.tags = {
            "uk": QuestionTag.objects.create(name="uk"),
            "fr": QuestionTag.objects.create(name="fr"),
            "cn": QuestionTag.objects.create(name="cn"),
            "vn": QuestionTag.objects.create(name="vn"),
            "very_small_company": QuestionTag.objects.create(name="very_small_company"),
            "50_250_company": QuestionTag.objects.create(name="50_250_company"),
            "small_company": QuestionTag.objects.create(name="small_company"),
            "middle_company": QuestionTag.objects.create(name="middle_company"),
            "1000_4999_company": QuestionTag.objects.create(name="1000_4999_company"),
            "5000_company": QuestionTag.objects.create(name="5000_company"),
        }

        tag = QuestionTag.objects.get(name="very_small_company")
        self.entity.tags.add(tag)

        # Création du pack de souscription (si nécessaire)
        self.sub_pack = self.structure.create_subscriptionPack()

    def initialize_test(self, csv_content):
        csv_file = SimpleUploadedFile(
            "entities.csv", csv_content.encode("utf-8"), content_type="text/csv"
        )

        # Variables initiales
        initial_entity_count = Entity.objects.count()
        entities = Entity.objects.all()
        initial_tags = []
        for entity in entities:
            for tag in entity.tags.all():
                initial_tags.append(tag)

        # Lancement de la méthode
        response = self.client.post(
            self.url, {"file": csv_file, "entity_slug": self.entity.slug}
        )

        return initial_entity_count, initial_tags, response

    def is_expected_result(self, initial_entity_count, initial_tags, response):
        final_entities = Entity.objects.all()
        final_tags = []
        for entity in final_entities:
            for tag in entity.tags.all():
                final_tags.append(tag)

        new_entity_count = final_entities.count() - initial_entity_count
        new_tag_count = len(final_tags) - len(initial_tags)
        return new_entity_count, new_tag_count

    # Tests Valides
    def test_csv_with_semicolon_separator(self):
        csv_content = (
            "name;slug;workforce;entity_level;parent_entity_slug;tag\n"
            "Test Organisation-main;test-organisation-main;100;0;;fr\n"
        )
        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["success"], True)

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie qu'aucune nouvelle entité n'a été créée
        self.assertEqual(new_entity_count, 0)
        # Vérifie que le nombre de tags de l'entité principale a augmenté de 1
        self.assertEqual(new_tag_count, 1)

    def test_main_entity_already_exists(self):
        csv_content = (
            "name,slug,workforce,entity_level,parent_entity_slug,tag\n"
            "Test Organisation-main,test-organisation-main,100,0,,fr\n"
        )

        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["success"], True)

        main_entity = Entity.objects.get(slug=self.entity.slug)
        self.assertEqual(main_entity.name, "Test Organisation-main")

        tag_fr = QuestionTag.objects.get(name="fr")
        self.assertIn(tag_fr, main_entity.tags.all())

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie qu'aucune nouvelle entité n'a été créée
        self.assertEqual(new_entity_count, 0)
        # Vérifie que le nombre de tags de l'entité principale a augmenté de 1
        self.assertEqual(new_tag_count, 1)

    def test_main_entity_not_mentioned(self):
        csv_content = (
            "name,slug,workforce,entity_level,parent_entity_slug,tag\n"
            "Entity1,entity1,100,1,test-organisation-main,fr\n"
        )

        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["success"], True)

        # Vérifie que la nouvelle entitée est bien retrouvée dans la base de données
        new_entity = Entity.objects.get(slug="entity1")
        self.assertEqual(new_entity.name, "Entity1")

        # Vérifie que la nouvelle entité a désormais une relation avec le tag "fr"
        tag_fr = QuestionTag.objects.get(name="fr")
        self.assertIn(tag_fr, new_entity.tags.all())
        tag_very_small_company = QuestionTag.objects.get(name="50_250_company")
        self.assertIn(tag_very_small_company, new_entity.tags.all())

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie qu'une seule entité a été créée
        self.assertEqual(new_entity_count, 1)
        # Vérifie que le nombre de tags de l'entité principale a augmenté de 1
        self.assertEqual(new_tag_count, 2)

    def test_create_six_entities_ordered(self):
        csv_content = (
            "name,slug,workforce,entity_level,parent_entity_slug,tag\n"
            "Entity1,entity1,100,1,test-organisation-main,uk\n"
            "Entity2,entity2,200,1,test-organisation-main,fr\n"
            "Entity3,entity3,50,2,entity1,cn\n"
            "Entity4,entity4,60,2,entity1,vn\n"
            "Entity5,entity5,70,2,entity2,uk\n"
            "Entity6,entity6,80,2,entity2,fr\n"
        )

        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertIn(response.status_code, [200, 201])
        self.assertEqual(response.json()["success"], True)

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie que 6 entités ont été crées
        self.assertEqual(new_entity_count, 6)
        # Vérifie que le nombre de tags de l'entité principale a augmenté de 12
        self.assertEqual(new_tag_count, 12)

    def test_create_five_entities_unordered(self):
        csv_content = (
            "name,slug,workforce,entity_level,parent_entity_slug,tag\n"
            "Entity3,entity3,50,2,entity1,cn\n"
            "Entity6,entity6,80,2,entity2,fr\n"
            "Entity1,entity1,100,1,test-organisation-main,uk\n"
            "Entity2,entity2,200,1,test-organisation-main,fr\n"
            "Entity5,entity5,70,2,entity2,uk\n"
        )

        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["success"], True)

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie que 5 nouvelles entités ont été créées
        self.assertEqual(new_entity_count, 5)
        # Vérifie que le nombre de tags de l'entité principale a augmenté de 10
        self.assertEqual(new_tag_count, 10)

    # Tests invalides
    def test_entity_not_linked_to_main(self):
        csv_content = (
            "name,slug,workforce,entity_level,parent_entity_slug,tag\n"
            "Entity1,entity1,100,1,other-entity,uk\n"
        )

        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "L'entité correspondant au slug other-entity n'existe pas !",
            response.json().get("message", ""),
        )

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie qu'aucune nouvelle entité n'a été créée
        self.assertEqual(new_entity_count, 0)
        # Vérifie qu'aucun tag n'a été créé
        self.assertEqual(new_tag_count, 0)

    def test_entity_not_linked_in_list(self):
        csv_content = (
            "name,slug,workforce,entity_level,parent_entity_slug,tag\n"
            "Entity1,entity1,100,1,test-organisation-main,uk\n"
            "Entity2,entity2,200,2,entity-1,fr\n"
            "Entity3,entity3,300,1,other-entity,cn\n"
        )

        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "L'entité correspondant au slug other-entity n'existe pas !",
            response.json()["message"],
        )

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie qu'aucune nouvelle entité n'a été créée
        self.assertEqual(new_entity_count, 0)
        # Vérifie qu'aucun tag n'a été créé
        self.assertEqual(new_tag_count, 0)

    def test_wrong_file_extension(self):
        wrong_file = SimpleUploadedFile(
            "entities.txt", b"dummy content", content_type="text/plain"
        )

        # Lancement de la méthode
        response = self.client.post(
            self.url, {"file": wrong_file, "entity_slug": self.entity.slug}
        )

        # Vérifications des résultats
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"], "Merci d'importer un fichier CSV !"
        )

    def test_missing_parent_entity_column(self):
        csv_content = (
            "name,slug,workforce,entity_level,tag\n" "Entity1,entity1,100,1,uk\n"
        )

        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["message"],
            "Les colonnes ne correspondent pas, merci d'utiliser la template CSV prévue à cet effet",
        )

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie qu'aucune nouvelle entité n'a été créée
        self.assertEqual(new_entity_count, 0)
        # Vérifie qu'aucun tag n'a été créé
        self.assertEqual(new_tag_count, 0)

    def test_disordered_columns(self):
        csv_content = (
            "slug,name,workforce,parent_entity_slug,entity_level,tag\n"
            "entity1,Entity1,100,test-organisation-main,1,uk\n"
        )

        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["message"],
            "Les colonnes ne correspondent pas, merci d'utiliser la template CSV prévue à cet effet",
        )

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie qu'aucune nouvelle entité n'a été créée
        self.assertEqual(new_entity_count, 0)
        # Vérifie qu'aucun tag n'a été créé
        self.assertEqual(new_tag_count, 0)

    def test_non_existent_tag(self):
        csv_content = (
            "name,slug,workforce,entity_level,parent_entity_slug,tag\n"
            "Entity1,entity1,100,1,test-organisation-main,nonexistenttag\n"
        )

        initial_entity_count, initial_tags, response = self.initialize_test(csv_content)

        # Vérifications des résultats
        self.assertEqual(response.status_code, 404)
        self.assertIn("Tag nonexistenttag n'existe pas", response.json()["message"])

        new_entity_count, new_tag_count = self.is_expected_result(
            initial_entity_count, initial_tags, response
        )
        # Vérifie qu'aucune nouvelle entité n'a été créée
        self.assertEqual(new_entity_count, 0)
        # Vérifie qu'aucun tag n'a été créé
        self.assertEqual(new_tag_count, 0)
