import json

from django.core import mail
from django.test import TestCase

from accounts.models import MixityUser


class RegisterAndLoginTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        MixityUser.objects.create_user(
            username="exists@example.com", email="exists@example.com", password="OldPassword-123"
        )

    def post(self, path, **data):
        return self.client.post(f"/api/{path}/", json.dumps(data), content_type="application/json")

    def test_registration_creates_the_account_and_sends_the_confirmation_mail(self):
        response = self.post("register", email="New@Example.com", password="Passw0rd-123")
        self.assertEqual(response.status_code, 200)
        user = MixityUser.objects.get(email="new@example.com")  # adresse mise en minuscules
        self.assertTrue(user.check_password("Passw0rd-123"))
        self.assertEqual(len(mail.outbox), 1)

    def test_existing_email_gets_a_specific_409_instead_of_a_generic_400(self):
        before = MixityUser.objects.count()
        response = self.post("register", email="exists@example.com", password="Passw0rd-123")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(MixityUser.objects.count(), before)

    def test_existing_email_is_detected_whatever_the_case(self):
        response = self.post("register", email="EXISTS@Example.com", password="Passw0rd-123")
        self.assertEqual(response.status_code, 409)

    def test_missing_fields_give_400_not_500(self):
        self.assertEqual(self.post("register", password="x").status_code, 400)
        self.assertEqual(self.post("register", email="a@example.com").status_code, 400)
        self.assertEqual(self.post("login", password="x").status_code, 400)
        self.assertEqual(self.post("forgotten_password_mail").status_code, 400)

    def test_login_still_works(self):
        ok = self.post("login", email="exists@example.com", password="OldPassword-123")
        self.assertEqual(ok.status_code, 200)
        bad = self.post("login", email="exists@example.com", password="wrong")
        self.assertEqual(bad.status_code, 401)
