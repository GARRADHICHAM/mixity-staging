from scoring.importsheets.import_20210831_1505 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startflash/questionnaire_startflash_20210831_1512.csv",
    )
    import_questions(apps, file, "mixity_start")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0214_import_ref_mixity_startflash"),
    ]

    operations = [migrations.RunPython(migrate_data)]
