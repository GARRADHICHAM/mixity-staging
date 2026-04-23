from scoring.importsheets.import_20210420_1643 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startup2021/questionnaire_start2021_20210428_1627.csv",
    )
    import_questions(apps, file, "mixity_evaluation_globale_pme", "startup")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0171_import_ref_society_2021_3"),
    ]

    operations = [migrations.RunPython(migrate_data)]
