import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210909_1138 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startflash/questionnaire_startflash_20211011_1024.csv",
    )
    import_questions(apps, file, "mixity_start")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0226_import_ref_start_2021_12"),
    ]

    operations = [migrations.RunPython(migrate_data)]
