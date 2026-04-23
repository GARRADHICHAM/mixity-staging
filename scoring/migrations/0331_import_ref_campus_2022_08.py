import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20220919_1405 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/campus2022/questionnaire_campus2022_20230302_1003.csv",
    )
    import_questions(apps, file, "mixity_evaluation_campus", "campus")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0330_import_collaborateurs360_v31"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
