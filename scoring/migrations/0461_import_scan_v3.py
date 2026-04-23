from scoring.importsheets.import_20241003_1025 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/scan/questionnaire_scan_20241119_1202.csv",
    )
    import_questions(apps, file, "mixity_evaluation_scan")


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0460_evaluationexpertiseproxy"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
