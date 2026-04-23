from scoring.importsheets.import_20220919_1405 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/collaborateurs360/questionnaire_collaborateurs360_20230223_1113.csv",
    )
    import_questions(apps, file, "evaluation_collaborateurs_360")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0328_auto_20230223_1116"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
