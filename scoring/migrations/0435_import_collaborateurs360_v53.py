from scoring.importsheets.import_20240527_1005 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/collaborateurs360/questionnaire_collaborateurs360_20240722_0846.csv",
    )
    import_questions(apps, file, "evaluation_collaborateurs_360")


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0434_import_collaborateurs360_v52"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
