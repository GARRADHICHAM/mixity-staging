from scoring.importsheets.import_20230614_0945 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/diag/questionnaire_diag_20230915_1000.csv",
    )
    import_questions(apps, file, "mixity_evaluation_diag")


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0380_import_collaborateurs360_v42"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
