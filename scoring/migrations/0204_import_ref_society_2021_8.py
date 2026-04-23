import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210701_1141 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/society2021/questionnaire_society2021_20210728_1433.csv",
    )
    import_questions(apps, file, "mixity_evaluation_globale", "society")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0203_fix_international_sheet21"),
    ]

    operations = [migrations.RunPython(migrate_data)]
