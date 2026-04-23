import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20220316_1033 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startup2021/questionnaire_start2021_20220808_1505.csv",
    )
    import_questions(apps, file, "mixity_evaluation_globale_pme", "startup")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0282_merge_20220630_1513"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: x)]
