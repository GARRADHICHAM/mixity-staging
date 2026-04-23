import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210730_1000 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startup2021/questionnaire_start2021_20210908_0948.csv",
    )
    import_questions(apps, file, "mixity_evaluation_globale_pme", "startup")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0223_import_ref_society_2021_11"),
    ]

    operations = [migrations.RunPython(migrate_data)]
