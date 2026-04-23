from scoring.importsheets.import_20230614_0945 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/diag/questionnaire_diag_20230807_1145.csv",
    )
    import_questions(apps, file, "mixity_evaluation_diag")


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0366_alter_evaluation_active_aggregation_with_children"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
