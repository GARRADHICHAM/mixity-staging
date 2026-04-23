import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210224_1427 import clean_database


def migrate_data(apps, schemaeditor):
    QuestionSheet = apps.get_model("scoring", "QuestionSheet")
    QuestionSheet.objects.filter(slug="mixity_international", version__lte=0.6).delete()

    clean_database(apps)


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0150_fix_international_sheet4"),
    ]

    operations = [migrations.RunPython(migrate_data)]
