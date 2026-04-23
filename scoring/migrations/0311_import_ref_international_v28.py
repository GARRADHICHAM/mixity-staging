from scoring.importsheets.import_20220907_0927 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/international/questionnaire_international_20221012_1208.csv",
    )
    import_questions(apps, file, "mixity_international")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0310_import_collaborateurs360_v25"),
    ]

    operations = [migrations.RunPython(migrate_data)]
