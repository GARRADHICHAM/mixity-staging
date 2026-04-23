from scoring.importsheets.import_20210701_1141 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/international/questionnaire_international_20211025_1035.csv",
    )
    import_questions(apps, file, "mixity_international")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0231_import_ref_mixity_startflash_v7"),
    ]

    operations = [migrations.RunPython(migrate_data)]
