from scoring.importsheets.import_20210701_1141 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/collaborateurs360/questionnaire_collaborateurs360_20210827_1007.csv",
    )
    import_questions(apps, file, "evaluation_collaborateurs_360")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0209_fix_international_sheet22"),
    ]

    operations = [migrations.RunPython(migrate_data)]
