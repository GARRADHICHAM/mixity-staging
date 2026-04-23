import json

from mixity.testing import TestCase
from django.test import Client

from accounts.models import MixityUser, BusinessLine, Structure, Membership
from sirh.models import ADPSoftware, ADPIndicatorType, ADPIndicator
from sirh.services import APIConnection, ADPDecidium, ADPAdapter


def create_adp_related_infos():
    s = ADPSoftware.objects.create(name="decidium")
    for a in [
        "promotion",
        "citizenships",
        "remuneration_increase",
        "turnover",
        "exiting",
        "hiring",
        "gender_paygap",
        "gender_repartition",
        "age_pyramid",
    ]:
        a = ADPIndicatorType(name=a)
        a.save()
        a.softwares.add(s)
        a.save()


####NEED TO CHECK IF WE CAN PUT THE CREDENTIALS IN THE TEST DIRECTLY BEFORE TESTING
# Create your tests here.
# class ADPCoreTest(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.client = Client()
#         create_adp_related_infos()
#         user = MixityUser.objects.create_user(
#             username="toto",
#             email="tt@gg.com",
#             password="12345",
#         )
#         cls.client.login(username="tt@gg.com", password="12345")
#         businessLine = BusinessLine.objects.create(
#             slug="others",
#             name_fr="Autre - précisez",
#             name_en="Others",
#         )
#         cls.structure = Structure.objects.create(
#             juridic_name="ste test",
#             siret="1234",
#             workforce=1,
#             adp_software=ADPSoftware.objects.first(),
#             business_line=businessLine,
#         )
#         e_lvl = cls.make_entity_level(cls.structure, "Groupe", 0)
#         cls.entity = cls.make_entity("Entity", e_lvl, 1)
#         Membership.objects.create(structure=cls.structure, user=user, is_owner=True)
#
#         def e(*args, **kwargs):
#             return
#
#         # we mock the data gathering with another method to get a JSON provided by ADP (see on their Github)
#         def get_data(self, *args, **kwargs):
#             if not self.has_retrieved:
#                 self.has_retrieved = True
#                 f = open("sirh/test_data/workers-all-workers-http-200-response.json")
#                 w = json.loads(f.read())["workers"]
#                 f.close()
#                 return w
#             return None
#
#         APIConnection.login = e
#         ADPDecidium.get_data = get_data
#         ADPDecidium.has_retrieved = False
#         co = APIConnection("TEST", "TEST")
#         cls.adp_a = ADPAdapter(co, structure=cls.structure)
#         cls.adp_a.gather_data()
#
#     def setUp(self) -> None:
#         pass
#
#     def test_indicator_count(self):
#         self.assertEqual(8, ADPIndicator.objects.count())

# def test_integrity(self):
#     for i in ADPIndicator.objects.select_related("type").filter(
#         type__name="gender_paygap"
#     ):
#         self.assertEqual(
#             i.data, json.loads(open(f"sirh/test_data/{i.type.name}.json").read())
#         )

# def test_refresh_for_remuneration_and_promotion(self):
#     # TODO update indicator dates
#     self.adp_a.gather_data()
