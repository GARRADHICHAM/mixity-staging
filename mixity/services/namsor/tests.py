import json
import os
from unittest import mock

import requests
from address.models import Country
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from django.test import Client
import responses
from django.test import RequestFactory
from smart_testing.testcase import TestCaseMixin

from accounts.vocabularies import TYPE_CHOICES, WRONG_CSV, TOO_MANY_COLLABORATORS
from mixity.dashboard.views_api import ApiUploadCSV
from mixity.dashboard.views_api import ApiHandleCollaboratorsList
from mixity.testing import TestCase
from mixity.tests import disable_network
from scoring.models import Evaluation, CollaboratorsStatistics, QuestionTag
from scoring.tests import generate_global_evaluation
from mixity.services.namsor.api import Namsor

import time


def get_result(file):
    class FakeRequest:
        data = open(f"mixity/test_data/namsor/{file}.json", "r").read()

    return FakeRequest()


def name_diaspora(*args, **kwargs):
    return get_result("name_diaspora")


def us_race(*args, **kwargs):
    return get_result("us_race")


def bad_response(*args, **kwargs):
    class FakeRequest:
        data = '{"error": "error"}'

    return FakeRequest()


class NamsorApiTest(TestCase, TestCaseMixin):
    @classmethod
    def setUpClass(cls):
        super(NamsorApiTest, cls).setUpClass()
        cls.e : Evaluation = None
        cls.user = None
        cls.scoring_client = None
        generate_global_evaluation(cls=cls)
        cls.e.do_user_validation()
        cls.e.do_admin_validation()
        cls.e.save()

    def global_test(self, median, confidence, credits, computed_data):
        for type in TYPE_CHOICES:
            form_data = {
                "file": open("mixity/static/csv/namsor/ethnicity_example.csv"),
                "type": type[0],
                "ignoreFirstLine": "false",
            }
            l = CollaboratorsStatistics.objects.all()
            for c in l:
                c.delete()

            path = f"/{self.e.entity.slug}/api/upload-csv/?eval_id={self.e.id}&version={self.e.display_version_slugified}"
            response = self.scoring_client.post(
                path,
                data=form_data,
            )
            found = False
            for element in response.data:
                if element["name"] == type[1]:
                    found = True
                    self.assertEqual("processing", element["status"])
            self.assertTrue(found)
            finished = False
            c = 0
            while (not finished):
                f = False
                u = f"/{self.e.entity.slug}/api/collaboratorstatistics"
                r = self.scoring_client.get(u)
                if c > 5:
                    finished = True
                self.assertEqual(r.content.decode('utf-8'), "e")
                for e in r.content:
                    if e["name"] == type[1]:
                        f = True
                        if e["status"] == "processing":
                            time.sleep(5)
                            c += 1
                        else:
                            finished = True
                self.assertTrue(f)
            last_obj = CollaboratorsStatistics.objects.last()
            statistics = last_obj.statistics
            self.assertFalse(last_obj.can_delete)
            self.assertEqual(last_obj.status, "finished")
            self.assertEqual(statistics.processed_collaborators, 3)
            self.assertEqual(statistics.unprocessed_collaborators, 0)
            self.assertEqual(statistics.credits_used, credits)
            self.assertEqual(
                statistics.computed_data,
                computed_data,
            )
            self.assertEqual(round(statistics.median, 3), median)
            self.assertEqual(round(statistics.confidence, 3), confidence)

        for type in TYPE_CHOICES:
            form_data = {
                "file": open("mixity/static/csv/namsor/ethnicity_example.csv"),
                "type": type[0],
                "ignoreFirstLine": "false",
            }

            path = f"/{self.e.entity.slug}/api/upload-csv/?eval_id={self.e.id}&version={self.e.display_version_slugified}"
            response = self.scoring_client.post(
                path,
                data=form_data,
            )
            self.assertEqual(400, response.status_code)


    # TODO: Trouver pourquoi les tests ne fonctionnent pas
    
    # @csrf_exempt
    # def test_upload_valid_csv(self):  
    #     return self.global_test(
    #         0.612,
    #         0.508,
    #         60,
    #         [{"name": "British", "value": 2}, {"name": "German", "value": 1}],
    #     )

    # @csrf_exempt
    # def test_upload_valid_csv_us(self):
    #     tag = QuestionTag.objects.create(name="us")
    #     self.e.tags.add(tag)
    #     Country.objects.create(name="Us", code="US")
    #     return self.global_test(
    #         0.727, 0.687, 30, [{"name": "A", "value": 2}, {"name": "W_NL", "value": 1}]
    #     )

    @disable_network
    @mock.patch(
        "requests.request",
        side_effect=bad_response,
    )
    @csrf_exempt
    def test_api_exception(self, patch):
        for type in TYPE_CHOICES:
            form_data = {
                "file": open("mixity/static/csv/namsor/ethnicity_example.csv"),
                "type": type[0],
                "ignoreFirstLine": "false",
            }

            path = f"/{self.e.entity.slug}/api/upload-csv/?eval_id={self.e.id}&version={self.e.display_version_slugified}"
            response = self.scoring_client.post(
                path,
                data=form_data,
            )
            last_obj = CollaboratorsStatistics.objects.last()
            self.assertFalse(last_obj.can_delete)
            self.assertTrue("Une erreur avec notre service partenaire est survenue" in last_obj.status)

    @csrf_exempt
    def test_wrong_csv(self):
        for csv_name in [
            ("wrong_csv", "Le fichier n'a pas le bon nombre de colonnes, une virgule a peut être été oubliée dans une case"),
            ("wrong_csv_too_many_columns", "Le fichier n'a pas le bon nombre de colonnes, une virgule a peut être été oubliée dans une case"),
            ("wrong_csv_too_many_collaborators", TOO_MANY_COLLABORATORS),
        ]:
            for type in TYPE_CHOICES:
                form_data = {
                    "file": open(f"mixity/test_data/namsor/{csv_name[0]}.csv"),
                    "type": type[0],
                    "ignoreFirstLine": "false",
                }

                path = f"/{self.e.entity.slug}/api/upload-csv/?eval_id={self.e.id}&version={self.e.display_version_slugified}"
                response = self.scoring_client.post(
                    path,
                    data=form_data,
                )
                last_obj = CollaboratorsStatistics.objects.last()
                self.assertTrue(last_obj.can_delete)
                self.assertEqual(csv_name[1], last_obj.status)
