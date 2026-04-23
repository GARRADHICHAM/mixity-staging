from scoring.importsheets.import_20220907_0927 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/collaborateurs360/questionnaire_collaborateurs360_20220920_1149.csv",
    )
    import_questions(apps, file, "evaluation_collaborateurs_360")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0304_import_collaborateurs360_v22"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
