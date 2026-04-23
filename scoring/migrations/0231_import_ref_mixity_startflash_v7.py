import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210909_1138 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startflash/questionnaire_startflash_20211025_1032.csv",
    )
    import_questions(apps, file, "mixity_start")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0230_import_ref_society_2021_14"),
    ]

    operations = [migrations.RunPython(migrate_data)]
