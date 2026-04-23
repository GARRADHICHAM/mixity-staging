import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20220131_1642 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startflash/questionnaire_startflash_20220301_1215.csv",
    )
    import_questions(apps, file, "mixity_start")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0255_fix_international_sheet25"),
    ]

    operations = [migrations.RunPython(migrate_data)]
