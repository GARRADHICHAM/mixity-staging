from scoring.importsheets.import_20210224_1427 import import_questions, revert_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/international/questionnaire_international_20210621_1531.csv",
    )
    import_questions(apps, file, "mixity_international")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0185_import_ref_start_2021_7"),
    ]

    operations = [migrations.RunPython(migrate_data)]
