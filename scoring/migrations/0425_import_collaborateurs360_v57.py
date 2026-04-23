from scoring.importsheets.import_20231011_1553 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/collaborateurs360/questionnaire_collaborateurs360_20240424_1249.csv",
    )
    import_questions(apps, file, "evaluation_collaborateurs_360")


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0424_import_collaborateurs360_v56"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
