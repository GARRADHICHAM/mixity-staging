from scoring.importsheets.import_20231011_1553 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/diag/questionnaire_diag_20240315_1149.csv",
    )
    import_questions(apps, file, "mixity_evaluation_diag")


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0405_import_collaborateurs360_v50"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
