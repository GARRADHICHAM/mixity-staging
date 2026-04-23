import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210420_1643 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/society2021/questionnaire_society2021_20210507_1133.csv",
    )
    import_questions(apps, file, "mixity_evaluation_globale", "society")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0179_import_ref_start_2021_6"),
    ]

    operations = [migrations.RunPython(migrate_data)]
