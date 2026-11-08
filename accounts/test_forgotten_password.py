import json

from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import MixityUser

CHANGE_URL = "/api/forgotten_password_change/"


def reset_link(user):
    return reverse(
        "user:password_reset_confirm",
        kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        },
    )


class ForgottenPasswordTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.victim = MixityUser.objects.create_user(
            username="victim@example.com", email="victim@example.com", password="OldPassword-123"
        )
        cls.other = MixityUser.objects.create_user(
            username="other@example.com", email="other@example.com", password="OtherPassword-123"
        )

    def change(self, user, password="NewPassword-456"):
        return self.client.post(
            CHANGE_URL,
            json.dumps({"uuid": urlsafe_base64_encode(force_bytes(user.pk)), "new_password": password}),
            content_type="application/json",
        )

    def test_user_number_alone_is_not_enough(self):
        response = self.change(self.victim, "Hacked-789")
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(authenticate(email="victim@example.com", password="Hacked-789"))
        self.assertIsNotNone(authenticate(email="victim@example.com", password="OldPassword-123"))

    def test_emailed_link_lets_the_owner_change_the_password(self):
        page = self.client.get(reset_link(self.victim))
        self.assertEqual(page.status_code, 200)
        response = self.change(self.victim)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(authenticate(email="victim@example.com", password="NewPassword-456"))

    def test_link_with_wrong_token_is_refused(self):
        bad = reverse(
            "user:password_reset_confirm",
            kwargs={"uidb64": urlsafe_base64_encode(force_bytes(self.victim.pk)), "token": "abc-1234567890abcdef"},
        )
        response = self.client.get(bad)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.change(self.victim).status_code, 400)

    def test_proof_for_one_user_cannot_change_another_user(self):
        self.client.get(reset_link(self.victim))
        response = self.change(self.other, "Hacked-789")
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(authenticate(email="other@example.com", password="Hacked-789"))

    def test_link_works_only_once(self):
        link = reset_link(self.victim)
        self.client.get(link)
        self.assertEqual(self.change(self.victim).status_code, 200)
        self.assertEqual(self.change(self.victim, "Second-789").status_code, 400)
        self.client.get(link)  # le jeton ne correspond plus à l'ancien mot de passe
        self.assertEqual(self.change(self.victim, "Second-789").status_code, 400)
        self.assertIsNone(authenticate(email="victim@example.com", password="Second-789"))

    def test_inactive_user_cannot_reset(self):
        self.victim.is_active = False
        self.victim.save()
        self.assertEqual(self.client.get(reset_link(self.victim)).status_code, 302)
