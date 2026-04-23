# encoding: utf-8
import logging

from django.core.management import BaseCommand

from accounts.models import Structure
from sirh.models import ADPCredentials
from sirh.services import APIConnection, ADPAdapter


class Command(BaseCommand):
    def handle(self, *args, **options):
        structure = Structure.objects.get(slug="maaf-structure")
        client_id, client_secret = ADPCredentials.objects.get(
            structure=structure
        ).get_credentials()
        client = APIConnection(client_id, client_secret)
        adapter = ADPAdapter(client, structure=structure)
        adapter.gather_data()
