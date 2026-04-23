import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210420_1643 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startup2021/questionnaire_start2021_20210621_0933.csv",
    )
    import_questions(apps, file, "mixity_evaluation_globale_pme", "startup")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0184_auto_20210618_1026"),
    ]

    operations = [migrations.RunPython(migrate_data)]
