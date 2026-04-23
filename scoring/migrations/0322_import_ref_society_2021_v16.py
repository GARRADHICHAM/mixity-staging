from scoring.importsheets.import_20220919_1405 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/society2021/questionnaire_society2021_20230104_1035.csv",
    )
    import_questions(apps, file, "mixity_evaluation_globale", "society")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0321_import_collaborateurs360_v27"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
