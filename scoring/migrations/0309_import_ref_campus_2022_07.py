import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20220907_0927 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/campus2022/questionnaire_campus2022_20220926_1016.csv",
    )
    import_questions(apps, file, "mixity_evaluation_campus", "campus")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0308_import_ref_society_2021_v15"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
