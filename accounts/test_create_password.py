import json
import time
from unittest import mock
from urllib.parse import quote_plus

from django.contrib.auth import authenticate
from django.test import TestCase

from accounts.models import MixityUser
from mixity.utils import encryption

URL = "/api/create_password/"


def link_for(email):
    """Reproduit l'encodage du lien envoyé par e-mail (accounts/mails.py)."""
    token = quote_plus(encryption().encrypt_data(email))
    return token.replace("%2F", "%252F")


class CreatePasswordTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.invited = MixityUser.objects.create(username="invited@example.com", email="invited@example.com")
        cls.invited.set_unusable_password()
        cls.invited.save()
        cls.member = MixityUser.objects.create_user(
            username="member@example.com", email="member@example.com", password="OldPassword-123"
        )

    def post(self, **data):
        return self.client.post(URL, json.dumps(data), content_type="application/json")

    def test_invited_user_can_set_first_password(self):
        response = self.post(encrypted_email=link_for("invited@example.com"), password="NewPassword-456")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(authenticate(email="invited@example.com", password="NewPassword-456"))

    def test_account_with_a_password_cannot_be_overwritten(self):
        response = self.post(encrypted_email=link_for("member@example.com"), password="Hacked-789")
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(authenticate(email="member@example.com", password="Hacked-789"))
        self.assertIsNotNone(authenticate(email="member@example.com", password="OldPassword-123"))

    def test_expired_link_is_refused(self):
        link = link_for("invited@example.com")
        later = time.time() + 31 * 24 * 3600
        with mock.patch("cryptography.fernet.time.time", return_value=later):
            response = self.post(encrypted_email=link, password="NewPassword-456")
        self.assertEqual(response.status_code, 400)
        self.invited.refresh_from_db()
        self.assertFalse(self.invited.has_usable_password())

    def test_link_still_valid_after_a_few_days(self):
        link = link_for("invited@example.com")
        later = time.time() + 10 * 24 * 3600
        with mock.patch("cryptography.fernet.time.time", return_value=later):
            response = self.post(encrypted_email=link, password="NewPassword-456")
        self.assertEqual(response.status_code, 200)

    def test_tampered_link_is_refused(self):
        response = self.post(encrypted_email="not-a-valid-token", password="NewPassword-456")
        self.assertEqual(response.status_code, 400)

    def test_missing_fields_are_refused(self):
        self.assertEqual(self.post(password="x").status_code, 400)
        self.assertEqual(self.post(encrypted_email=link_for("invited@example.com")).status_code, 400)

    def test_unknown_user_gets_404(self):
        response = self.post(encrypted_email=link_for("ghost@example.com"), password="NewPassword-456")
        self.assertEqual(response.status_code, 404)
