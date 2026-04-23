from scoring.importsheets.import_20241219_1200 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/diag/questionnaire_diag_20241219_1700.csv",
    )
    import_questions(apps, file, "mixity_evaluation_diag")


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0469_merge_20241219_1453"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
