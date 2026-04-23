import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20220701_1122 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/campus2022/questionnaire_campus2022_20220905_1149.csv",
    )
    import_questions(apps, file, "mixity_evaluation_campus", "campus")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0291_import_ref_campus_2022_02"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
