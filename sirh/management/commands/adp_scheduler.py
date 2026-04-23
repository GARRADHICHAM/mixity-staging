# encoding: utf-8
import logging
from datetime import datetime, timedelta

from django.core.management import BaseCommand
from django.db.models import Q
from django.utils import timezone

from sirh.models import ADPCredentials, ADPStatus
from sirh.services import APIConnection, ADPAdapter

# Command to update ADP data on entities that have an automatic update
class Command(BaseCommand):
    def handle(self, *args, **options):
        for status in ADPStatus.objects.filter(
            can_update=True, update_automatically=True
        ).select_related("entity__entity_level__structure"):
            try:
                if status.last_updated < (
                    timezone.now() - timedelta(days=30 * status.update_frequency)
                ):
                    print(status.entity, status.structure)
                    structure = status.structure
                    if not status.structure:
                        structure = status.entity.entity_level.structure
                    client_id, client_secret = ADPCredentials.objects.get(
                        Q(structure=structure) | Q(entity=status.entity)
                    ).get_credentials()
                    client = APIConnection(client_id, client_secret)
                    adapter = ADPAdapter(client, structure=structure)
                    adapter.gather_data()
            except Exception as e:
                print(f"{e}")
                logging.exception(f"{e}")
