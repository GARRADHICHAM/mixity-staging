import json
import re
import traceback
from operator import xor

import responses
import requests

from unittest import mock
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.template import Context, RequestContext, Template
from django.test import Client
from mixity.testing import TestCase
from django.urls import reverse
from django.utils import translation
from accounts.vocabularies import CURRENCY_CHOICES
from django.test import RequestFactory

from accounts.forms import MixityUserCreationForm
from accounts.models import MixityUser, Structure, Membership, BusinessLine
from mixity.models import NonEvaluatedClient, PressArticle
from mixity.settings import BLOG_API_URL
from mixity.views import (
    FAQPageView,
)
from subscriptions.models import SubscriptionType


def disable_network(fn):
    for net_fn in (
        "urllib.request.urlopen",
        "requests.adapters.HTTPAdapter.send",
        "urllib.request.OpenerDirector.open",
    ):

        class _raise_network_error(object):
            _net_fn = net_fn

            def get_traceback(self):
                stack = traceback.extract_stack()
                for path, line_number, _, _ in reversed(stack):
                    if (
                        "lib/python" in path
                        or "settings/test.py" in path
                        or "manage.py" in path
                        or "smart_testing/" in path
                    ):
                        continue
                    return "%s:%d" % (path, line_number)
                return "TRACEBACK NOT FOUND"

            def __call__(self, *args, **kwargs):
                callback = self._net_fn
                origin = self.get_traceback()
                message = (
                    "\n\n" + "Trying to access network during tests" + "\n\n"
                    f" - Origin: {origin}\n"
                    f" - Callback: {callback}\n"
                    f" - Args: {args}\n"
                    f" - Kwargs: {kwargs}\n"
                )
                raise Exception(message)

        mocker = mock.patch(net_fn, _raise_network_error())
        fn = mocker(fn)
    return fn


class SignUpPageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.subscriptionType = SubscriptionType.objects.create(
            label="test", pme_label="test pme"
        )

    def test_signup(self):
        response = self.client.get("/account/register/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_signupForm_blank(self):
        form = MixityUserCreationForm({})
        self.assertFalse(form.is_valid())


# class UpdatePartnerTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         user = MixityUser.objects.create_user(
#             username="toto",
#             email="tt@gg.com",
#             password="12345",
#         )
#         self.client.login(username="tt@gg.com", password="12345")
#         businessLine = BusinessLine.objects.create(
#             slug="others",
#             name_fr="Autre - précisez",
#             name_en="Others",
#         )
#         self.structure = Structure.objects.create(
#             juridic_name="ste test",
#             siret="1234",
#             workforce=1,
#             business_line=businessLine,
#         )
#         e_lvl_0 = self.make_entity_level(self.structure, "Groupe", 0)
#         entity = self.make_entity(
#             self.structure.juridic_name, e_lvl_0, self.structure.workforce
#         )
#         Membership.objects.create(structure=self.structure, user=user, is_owner=True)
#
#     def test_page(self):
#         response = self.client.get(
#             reverse("dashboard:account:update_members", args=(self.structure.slug,))
#         )
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, "accounts/structure_members_update.html")
#
#     def test_add_sendingmail(self):
#         tst = self.structure.owners.filter(username="jojo@gmail.com").first()
#         self.assertIsNone(tst)
#         data_form = {"email": "jojo@gmail.com"}
#         self.client.post(
#             reverse("dashboard:account:update_members", args=(self.structure.slug,)),
#             data_form,
#             follow=True,
#         )
#         self.assertEqual(len(mail.outbox), 1)
#         self.assertEqual(mail.outbox[0].to, ["jojo@gmail.com"])
#         # verification url de connexion
#         m = re.search(
#             """(http:)(.*)(/user/reset/)(.*)(/)""",
#             str(mail.outbox[0].alternatives[0][0]),
#         )
#         response = self.client.get(m.group(), follow=True)
#         self.assertEqual(response.status_code, 200)
#         # verification insertion dans bdd
#         u = MixityUser.objects.get(username="jojo@gmail.com")
#         tst = self.structure.owners.filter(username="jojo@gmail.com").first()
#         self.assertIsNone(tst)
#         # self.client.get(
#         #     reverse(
#         #         "structure:set_owner_member",
#         #         args=(
#         #             self.structure.pk,
#         #             self.structure.members.filter(username="jojo@gmail.com").first().pk,
#         #         ),
#         #     )
#         # )
#         # tst = self.structure.owners.filter(username="jojo@gmail.com").first()
#         # self.assertIsNotNone(tst)


class NumFormatTemplateTagTest(TestCase):
    def tearDown(self):
        settings.LANGUAGES = self.old_languages
        translation.deactivate()

    def setUp(self):
        self.old_languages = settings.LANGUAGES
        settings.LANGUAGES = [
            ("fr", "Français"),
            ("en", "English"),
            ("es", "Español"),
        ]  # TODO : Add compatibility
        # with new languages

    # POINTS TAG
    def test_points_tag(self):
        test_list = [
            # Test priority
            {
                "value": 10,
                "current_year": 1,
                "last_year": 1,
                "fr": "10 pts",
                "en": "10 pts",
                "es": "10 puntos",
            },
            # Test null/zero return
            {"value": 0, "fr": "0 pts", "en": "0 pts", "es": "0 puntos"},
            {
                "value": 0,
                "show_evolution": True,
                "fr": settings.EVOLUTION_EQU_SYMBOL + " 0 pts",
                "es": settings.EVOLUTION_EQU_SYMBOL + " 0 puntos",
                "en": settings.EVOLUTION_EQU_SYMBOL + " 0 pts",
            },
            {
                "current_year": 1,
                "last_year": 1,
                "fr": "0 pts",
                "en": "0 pts",
                "es": "0 puntos",
            },
            {
                "current_year": 1,
                "last_year": 1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_EQU_SYMBOL + " 0 pts",
                "es": settings.EVOLUTION_EQU_SYMBOL + " 0 puntos",
                "en": settings.EVOLUTION_EQU_SYMBOL + " 0 pts",
            },
            {
                "current_year": 1.09,
                "last_year": 1.05,
                "fr": "0 pts",
                "en": "0 pts",
                "es": "0 puntos",
            },
            {
                "current_year": 1.09,
                "last_year": 1.05,
                "show_evolution": True,
                "fr": settings.EVOLUTION_EQU_SYMBOL + " 0 pts",
                "en": settings.EVOLUTION_EQU_SYMBOL + " 0 pts",
                "es": settings.EVOLUTION_EQU_SYMBOL + " 0 puntos",
            },
            {
                "current_year": 80.3,
                "last_year": 80.2,
                "fr": "0 pts",
                "en": "0 pts",
                "es": "0 puntos",
            },
            # Test positive return
            {"value": 1, "fr": "1 pts", "en": "1 pts", "es": "1 puntos"},
            {
                "value": 1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_POS_SYMBOL + " 1 pts",
                "en": settings.EVOLUTION_POS_SYMBOL + " 1 pts",
                "es": settings.EVOLUTION_POS_SYMBOL + " 1 puntos",
            },
            {
                "current_year": 1,
                "last_year": 0,
                "fr": "1 pts",
                "en": "1 pts",
                "es": "1 puntos",
            },
            {
                "current_year": 1,
                "last_year": 0,
                "show_evolution": True,
                "fr": settings.EVOLUTION_POS_SYMBOL + " 1 pts",
                "en": settings.EVOLUTION_POS_SYMBOL + " 1 pts",
                "es": settings.EVOLUTION_POS_SYMBOL + " 1 puntos",
            },
            {
                "current_year": 0.5,
                "last_year": 0,
                "fr": "1 pts",
                "en": "1 pts",
                "es": "1 puntos",
            },
            {
                "current_year": 0.5,
                "last_year": 0,
                "show_evolution": True,
                "fr": settings.EVOLUTION_POS_SYMBOL + " 1 pts",
                "en": settings.EVOLUTION_POS_SYMBOL + " 1 pts",
                "es": settings.EVOLUTION_POS_SYMBOL + " 1 puntos",
            },
            # Test negative return
            {"value": -1, "fr": "-1 pts", "en": "-1 pts", "es": "-1 puntos"},
            {
                "value": -1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_NEG_SYMBOL + " -1 pts",
                "en": settings.EVOLUTION_NEG_SYMBOL + " -1 pts",
                "es": settings.EVOLUTION_NEG_SYMBOL + " -1 puntos",
            },
            {
                "current_year": 0,
                "last_year": 1,
                "fr": "-1 pts",
                "en": "-1 pts",
                "es": "-1 puntos",
            },
            {
                "current_year": 0,
                "last_year": 1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_NEG_SYMBOL + " -1 pts",
                "en": settings.EVOLUTION_NEG_SYMBOL + " -1 pts",
                "es": settings.EVOLUTION_NEG_SYMBOL + " -1 puntos",
            },
            {
                "current_year": 85.4,
                "last_year": 85.6,
                "fr": "-1 pts",
                "en": "-1 pts",
                "es": "-1 puntos",
            },
            # Test greater 10 with no decimal return
            {"value": 15.2123, "fr": "15 pts", "en": "15 pts", "es": "15 puntos"},
            {
                "current_year": 20.2123,
                "last_year": 5,
                "fr": "15 pts",
                "en": "15 pts",
                "es": "15 puntos",
            },
            # Test greater 0 and less 10 with decimal return
            {"value": 5.2123, "fr": "5,21 pts", "en": "5.21 pts", "es": "5,21 puntos"},
            {
                "current_year": 10.2123,
                "last_year": 5,
                "fr": "5 pts",
                "en": "5 pts",
                "es": "5 puntos",
            },
            # Test groupe return
            {
                "value": 10000.2123,
                "fr": "10\xa0000 pts",
                "en": "10,000 pts",
                "es": "10.000 puntos",
            },
            {
                "current_year": 10005.2123,
                "last_year": 5,
                "fr": "10\xa0000 pts",
                "en": "10,000 pts",
                "es": "10.000 puntos",
            },
            # Test groupe return
            {
                "current_year": 1,
                "last_year": None,
                "fr": "ND*",
                "es": "N / A*",
                "en": "UA*",
            },
            {
                "current_year": None,
                "last_year": 1,
                "fr": "ND*",
                "es": "N / A*",
                "en": "UA*",
            },
            {"fr": "ND*", "es": "N / A*", "en": "UA*"},
        ]

        for test in test_list:
            if "es" not in test:
                # Spanish formats are identical to french when not specified
                test["es"] = test["fr"]
            for language in settings.LANGUAGES:
                translation.activate(language[0])

                template_str = "points value={} current_year={} last_year={} delta=0 show_evolution={}".format(
                    test.get("value", None),
                    test.get("current_year", None),
                    test.get("last_year", None),
                    test.get("show_evolution", False),
                )
                template_str = "{% load format_number %}{% " + template_str + " %}"
                template = Template(template_str)

                rendered = template.render(Context({}))

                self.assertEqual(rendered, test[language[0]], msg=f"{language} {test}")

    # PERCENTAGE TAG
    def test_percentage_tag(self):
        test_list = [
            # Test priority
            {"value": 10, "current_year": 1, "last_year": 1, "fr": "10 %", "en": "10%"},
            # Test null/zero return
            {"value": 0, "fr": "0 %", "en": "0%"},
            {
                "value": 0,
                "show_evolution": True,
                "fr": settings.EVOLUTION_EQU_SYMBOL + " 0 %",
                "en": settings.EVOLUTION_EQU_SYMBOL + " 0%",
            },
            {"current_year": 1, "last_year": 1, "fr": "0 %", "en": "0%"},
            {
                "current_year": 1,
                "last_year": 1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_EQU_SYMBOL + " 0 %",
                "en": settings.EVOLUTION_EQU_SYMBOL + " 0%",
            },
            # Test positive return
            {"value": 1, "fr": "1 %", "en": "1%"},
            {
                "value": 1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_POS_SYMBOL + " 1 %",
                "en": settings.EVOLUTION_POS_SYMBOL + " 1%",
            },
            {"current_year": 1, "last_year": 0, "fr": "1 %", "en": "1%"},
            {
                "current_year": 1,
                "last_year": 0,
                "show_evolution": True,
                "fr": settings.EVOLUTION_POS_SYMBOL + " 1 %",
                "en": settings.EVOLUTION_POS_SYMBOL + " 1%",
            },
            # Test negative return
            {"value": -1, "fr": "-1 %", "en": "-1%"},
            {
                "value": -1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_NEG_SYMBOL + " -1 %",
                "en": settings.EVOLUTION_NEG_SYMBOL + " -1%",
            },
            {"current_year": 0, "last_year": 1, "fr": "-1 %", "en": "-1%"},
            {
                "current_year": 0,
                "last_year": 1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_NEG_SYMBOL + " -1 %",
                "en": settings.EVOLUTION_NEG_SYMBOL + " -1%",
            },
            # Test greater 10 with no decimal return
            {"value": 15.2123, "fr": "15 %", "en": "15%"},
            {"current_year": 20.2123, "last_year": 5.2, "fr": "15 %", "en": "15%"},
            # Test greater 0 and less 10 with decimal return
            {"value": 5.2123, "fr": "5,21 %", "en": "5.21%"},
            {"current_year": 10.2123, "last_year": 5, "fr": "5 %", "en": "5%"},
            # Test groupe return
            {
                "value": 10000.2123,
                "fr": "10\xa0000 %",
                "en": "10,000%",
                "es": "10.000 %",
            },
            {
                "current_year": 10005.2123,
                "last_year": 5,
                "fr": "10\xa0000 %",
                "en": "10,000%",
                "es": "10.000 %",
            },
            # Test groupe return
            {
                "current_year": 1,
                "last_year": None,
                "fr": "ND*",
                "es": "N / A*",
                "en": "UA*",
            },
            {
                "current_year": None,
                "last_year": 1,
                "fr": "ND*",
                "es": "N / A*",
                "en": "UA*",
            },
            {"fr": "ND*", "es": "N / A*", "en": "UA*"},
        ]

        for test in test_list:
            if "es" not in test:
                # Spanish formats are identical to french when not specified
                test["es"] = test["fr"]
            for language in settings.LANGUAGES:
                translation.activate(language[0])

                template_str = "percentage value={} current_year={} last_year={} delta=0 show_evolution={}".format(
                    test.get("value", None),
                    test.get("current_year", None),
                    test.get("last_year", None),
                    test.get("show_evolution", False),
                )
                template_str = "{% load format_number %}{% " + template_str + " %}"
                template = Template(template_str)

                rendered = template.render(Context({}))

                self.assertEqual(rendered, test[language[0]], msg=f"{language} {test}")

    # CURRENCY TAG
    def test_currency_tag(self):
        test_list = [
            # Test priority
            {
                "value": 10,
                "current_year": 1,
                "last_year": 1,
                "fr": "10 {symbol}",
                "en": "10 {symbol}",
            },
            # Test null/zero return
            {
                "value": 0,
                "fr": "0 {symbol}",
                "en": "0 {symbol}",
            },
            {
                "value": 0,
                "show_evolution": True,
                "fr": settings.EVOLUTION_EQU_SYMBOL + " 0 {symbol}",
                "en": settings.EVOLUTION_EQU_SYMBOL + " 0 {symbol}",
            },
            {
                "current_year": 1,
                "last_year": 1,
                "fr": "0 {symbol}",
                "en": "0 {symbol}",
            },
            {
                "current_year": 1,
                "last_year": 1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_EQU_SYMBOL + " 0 {symbol}",
                "en": settings.EVOLUTION_EQU_SYMBOL + " 0 {symbol}",
            },
            # Test positive return
            {
                "value": 1,
                "fr": "1 {symbol}",
                "en": "1 {symbol}",
            },
            {
                "value": 1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_POS_SYMBOL + " 1 {symbol}",
                "en": settings.EVOLUTION_POS_SYMBOL + " 1 {symbol}",
            },
            {
                "current_year": 1,
                "last_year": 0,
                "fr": "1 {symbol}",
                "en": "1 {symbol}",
            },
            {
                "current_year": 1,
                "last_year": 0,
                "show_evolution": True,
                "fr": settings.EVOLUTION_POS_SYMBOL + " 1 {symbol}",
                "en": settings.EVOLUTION_POS_SYMBOL + " 1 {symbol}",
            },
            # Test negative return
            {
                "value": -1,
                "fr": "-1 {symbol}",
                "en": "-1 {symbol}",
            },
            {
                "value": -1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_NEG_SYMBOL + " -1 {symbol}",
                "en": settings.EVOLUTION_NEG_SYMBOL + " -1 {symbol}",
            },
            {
                "current_year": 0,
                "last_year": 1,
                "fr": "-1 {symbol}",
                "en": "-1 {symbol}",
            },
            {
                "current_year": 0,
                "last_year": 1,
                "show_evolution": True,
                "fr": settings.EVOLUTION_NEG_SYMBOL + " -1 {symbol}",
                "en": settings.EVOLUTION_NEG_SYMBOL + " -1 {symbol}",
            },
            # Test greater 10 with no decimal return
            {
                "value": 15.2123,
                "fr": "15 {symbol}",
                "en": "15 {symbol}",
            },
            {
                "current_year": 20.2123,
                "last_year": 5,
                "fr": "15 {symbol}",
                "en": "15 {symbol}",
            },
            # Test greater 0 and less 10 with decimal return
            {
                "value": 5.2123,
                "fr": "5,21 {symbol}",
                "en": "5.21 {symbol}",
            },
            {
                "current_year": 10.2123,
                "last_year": 5,
                "fr": "5 {symbol}",
                "en": "5 {symbol}",
            },
            # Test groupe return
            {
                "value": 10000.2123,
                "fr": "10\xa0000 {symbol}",
                "en": "10,000 {symbol}",
                "es": "10.000 {symbol}",
            },
            {
                "current_year": 10005.2123,
                "last_year": 5,
                "fr": "10\xa0000 {symbol}",
                "en": "10,000 {symbol}",
                "es": "10.000 {symbol}",
            },
        ]

        for test in test_list:
            if "es" not in test:
                # Spanish formats are identical to french when not specified
                test["es"] = test["fr"]
            for language in settings.LANGUAGES:
                for currency_symbol in CURRENCY_CHOICES:
                    translation.activate(language[0])

                    template_str = "currency value={} current_year={} last_year={} delta=0 show_evolution={}".format(
                        test.get("value", None),
                        test.get("current_year", None),
                        test.get("last_year", None),
                        test.get("show_evolution", False),
                    )
                    template_str = "{% load format_number %}{% " + template_str + " %}"
                    template = Template(template_str)

                    class FakeRequest:
                        CURRENCY_SYMBOL = currency_symbol[1]

                    rendered = template.render(Context({"request": FakeRequest()}))
                    self.assertEqual(
                        rendered,
                        test[language[0]].format(symbol=currency_symbol[1]),
                        msg=f"{language} {currency_symbol} {test}",
                    )

        test_list = [
            # With no symbol return test
            {
                "current_year": 1,
                "last_year": None,
                "fr": "ND*",
                "es": "N / A*",
                "en": "UA*",
            },
            {
                "current_year": None,
                "last_year": 1,
                "fr": "ND*",
                "es": "N / A*",
                "en": "UA*",
            },
            {
                "fr": "ND*",
                "es": "N / A*",
                "en": "UA*",
            },
        ]

        for test in test_list:
            if "es" not in test:
                # Spanish formats are identical to french when not specified
                test["es"] = test["fr"]
            for language in settings.LANGUAGES:
                for currency_symbol in CURRENCY_CHOICES:
                    translation.activate(language[0])

                    template_str = "currency value={} current_year={} last_year={} delta=0 show_evolution={}".format(
                        test.get("value", None),
                        test.get("current_year", None),
                        test.get("last_year", None),
                        test.get("show_evolution", False),
                    )
                    template_str = "{% load format_number %}{% " + template_str + " %}"
                    template = Template(template_str)

                    class FakeRequest:
                        CURRENCY_SYMBOL = currency_symbol[1]

                    rendered = template.render(Context({"request": FakeRequest()}))

                    self.assertEqual(
                        rendered, test[language[0]], msg=f"{language} {test}"
                    )

        # No currency symbol provided test
        template_str = "currency value=1"
        template_str = "{% load format_number %}{% " + template_str + " %}"
        template = Template(template_str)

        translation.activate("fr")

        class FakeRequest:
            CURRENCY_SYMBOL = None

        rendered = template.render(Context({"request": FakeRequest()}))

        self.assertEqual(rendered, "ND*")

    # SIMPLE NUMBER TAG
    def test_simple_number_tag(self):
        test_list = [
            {"value": 0, "fr": "0", "en": "0"},
            {"value": 1, "fr": "1", "en": "1"},
            {"value": -1, "fr": "-1", "en": "-1"},
            {"value": 5, "fr": "5", "en": "5"},
            {"value": 5.2, "fr": "5", "en": "5"},
            {"value": 5.2123, "fr": "5", "en": "5"},
            {"value": 4.8123, "fr": "5", "en": "5"},
            {"value": -5.2123, "fr": "-5", "en": "-5"},
            {"value": -4.8123, "fr": "-5", "en": "-5"},
            {"value": 15, "fr": "15", "en": "15"},
            {"value": 15.2, "fr": "15", "en": "15"},
            {"value": 15.2123, "fr": "15", "en": "15"},
            {"value": 15.8123, "fr": "16", "en": "16"},
            {"value": 15.5, "fr": "16", "en": "16"},
            {"value": 10000, "fr": "10\xa0000", "en": "10,000", "es": "10.000"},
            {"value": 10000.2, "fr": "10\xa0000", "en": "10,000", "es": "10.000"},
            {"value": 10000.2123, "fr": "10\xa0000", "en": "10,000", "es": "10.000"},
            {"value": None, "fr": "ND*", "es": "N / A*", "en": "UA*"},
        ]

        for test in test_list:
            if "es" not in test:
                # Spanish formats are identical to french when not specified
                test["es"] = test["fr"]
            for language in settings.LANGUAGES:
                translation.activate(language[0])

                template_str = "simple_number value={}".format(test["value"])
                template_str = "{% load format_number %}{% " + template_str + " %}"
                template = Template(template_str)

                rendered = template.render(Context({}))

                self.assertEqual(rendered, test[language[0]], msg=f"{language} {test}")
