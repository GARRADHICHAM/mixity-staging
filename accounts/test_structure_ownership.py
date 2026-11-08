import datetime
import json

from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import Membership, Structure
from mixity.testing import TestCase
from subscriptions.models import SubscriptionPack


class StructureOwnershipTest(TestCase):
    """Les API qui désignent une entreprise (SIRET) vérifient l'appartenance de l'utilisateur."""

    @classmethod
    def setUpTestData(cls):
        business_line = cls.make_business_line("bl", "Secteur", "Sector")
        cls.a = cls.make_structure("Société A", "societe-a", 100, "Diversity", business_line)
        cls.b = cls.make_structure("Société B", "societe-b", 50, "Diversity", business_line)
        Structure.objects.filter(pk=cls.a.pk).update(siret="11111111111111", duns="111111111")
        Structure.objects.filter(pk=cls.b.pk).update(siret="22222222222222", duns="222222222")
        cls.a.refresh_from_db()
        cls.b.refresh_from_db()
        cls.entity_a = cls.make_entity(cls.a.juridic_name, cls.make_entity_level(cls.a, "Groupe", 0), 100)
        cls.make_entity(cls.b.juridic_name, cls.make_entity_level(cls.b, "Groupe", 0), 50)

        def user(name):
            return cls.make_user(f"{name}@example.com", "pw", username=f"{name}@example.com")

        cls.owner = user("owner")
        Membership.objects.create(user=cls.owner, structure=cls.a, is_owner=True)
        cls.member = user("member")
        Membership.objects.create(user=cls.member, structure=cls.a)
        cls.reader = user("reader")
        Membership.objects.create(user=cls.reader, structure=cls.a, is_reader=True)
        cls.outsider = user("outsider")
        Membership.objects.create(user=cls.outsider, structure=cls.b, is_owner=True)
        cls.staff = user("staff")
        cls.staff.is_staff = True
        cls.staff.save()
        cls.pack = SubscriptionPack.objects.create(structure=cls.a, start_date=datetime.date.today())

    def post(self, path, **data):
        return self.client.post(f"/api/{path}/", json.dumps(data), content_type="application/json")

    # --- lecture des collaborateurs : propriétaires seulement
    def test_owner_and_staff_can_list_collaborators(self):
        for who in (self.owner, self.staff):
            with self.subTest(who=who.username):
                self.client.force_login(who)
                self.assertEqual(self.post("get_collaborators", siret=self.a.siret).status_code, 200)

    def test_others_cannot_list_collaborators(self):
        for who in (self.member, self.reader, self.outsider):
            with self.subTest(who=who.username):
                self.client.force_login(who)
                self.assertEqual(self.post("get_collaborators", siret=self.a.siret).status_code, 403)

    def test_structure_can_be_designated_by_duns(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.post("get_collaborators", duns=self.a.duns).status_code, 200)

    def test_unknown_structure_gives_404_not_500(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.post("get_collaborators", siret="99999999999999").status_code, 404)

    # --- un lecteur ne peut pas s'attribuer des droits
    def test_reader_cannot_promote_himself_to_owner(self):
        entity_membership = Membership.objects.create(user=self.reader, entity=self.entity_a)
        self.client.force_login(self.reader)
        response = self.post(
            "update_collaborator", siret=self.a.siret, entity_name=self.entity_a.name,
            email=self.reader.email, is_owner=True, is_reader=False,
        )
        self.assertEqual(response.status_code, 403)
        entity_membership.refresh_from_db()
        self.assertFalse(entity_membership.is_owner)

    # --- un propriétaire d'une autre entreprise ne peut rien modifier
    def test_outsider_cannot_delete_a_collaborator(self):
        entity_membership = Membership.objects.create(user=self.member, entity=self.entity_a)
        self.client.force_login(self.outsider)
        response = self.post(
            "delete_collaborator", siret=self.a.siret, entity_name=self.entity_a.name, email=self.member.email
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Membership.objects.filter(pk=entity_membership.pk).exists())

    def test_outsider_cannot_invite_collaborators(self):
        self.client.force_login(self.outsider)
        response = self.post(
            "invite_collaborators", siret=self.a.siret,
            collaborators=[{"email": "new@example.com", "entity": self.entity_a.name}],
        )
        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_edit_the_description(self):
        self.client.force_login(self.outsider)
        response = self.post("update_structure_description", siret=self.a.siret, activity_description="piratée")
        self.assertEqual(response.status_code, 403)
        self.a.refresh_from_db()
        self.assertNotEqual(self.a.description, "piratée")

    def test_owner_can_edit_the_description(self):
        self.client.force_login(self.owner)
        response = self.post("update_structure_description", siret=self.a.siret, activity_description="ok")
        self.assertEqual(response.status_code, 200)
        self.a.refresh_from_db()
        self.assertEqual(self.a.description, "ok")

    def test_reading_the_description_needs_membership_only(self):
        self.client.force_login(self.reader)
        self.assertEqual(self.post("get_structure_description", siret=self.a.siret).status_code, 200)
        self.client.force_login(self.outsider)
        self.assertEqual(self.post("get_structure_description", siret=self.a.siret).status_code, 403)

    def test_update_structure_requires_ownership(self):
        self.client.force_login(self.outsider)
        response = self.client.patch(
            "/api/update_structure/", json.dumps({"old_siret": self.a.siret, "website": "https://evil.example"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.owner)
        response = self.client.patch(
            "/api/update_structure/", json.dumps({"old_siret": self.a.siret, "website": "https://ok.example"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.a.refresh_from_db()
        self.assertEqual(self.a.website, "https://ok.example")

    def test_outsider_cannot_create_subscription_options(self):
        self.client.force_login(self.outsider)
        response = self.post("create_options", product="diag", structure_id=self.a.pk)
        self.assertEqual(response.status_code, 403)

    # --- imports CSV
    def test_outsider_cannot_import_collaborators(self):
        self.client.force_login(self.outsider)
        csv_file = SimpleUploadedFile(
            "c.csv", b"first_name,last_name,email,entity_slug,is_owner,is_reader\n", content_type="text/csv"
        )
        response = self.client.post(
            "/api/upload_collaborators_csv/", {"file": csv_file, "entity_slug": self.entity_a.slug}
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_is_not_refused_by_the_ownership_check(self):
        self.client.force_login(self.owner)
        csv_file = SimpleUploadedFile("c.csv", b"bad header\n", content_type="text/csv")
        response = self.client.post(
            "/api/upload_collaborators_csv/", {"file": csv_file, "entity_slug": self.entity_a.slug}
        )
        self.assertNotEqual(response.status_code, 403)

    # --- données d'abonnement
    def test_subscription_pack_visible_to_members_only(self):
        url = f"/api/{self.a.pk}/subscription-pack/"
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_subscription_pack_without_pack_gives_404(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(f"/api/{self.b.pk}/subscription-pack/").status_code, 404)
