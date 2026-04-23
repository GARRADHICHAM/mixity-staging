import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210420_1643 import import_questions


def migrate_data(apps, schemaeditor):
    Answer = apps.get_model("scoring", "Answer")
    for answer in Answer.objects.all():
        answer.mean_score_in_business_line = None
        answer.save()


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0185_import_ref_start_2021_7"),
    ]

    operations = [migrations.RunPython(migrate_data)]
