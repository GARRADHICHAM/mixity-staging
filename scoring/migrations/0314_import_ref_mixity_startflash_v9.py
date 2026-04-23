import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20220919_1405 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startflash/questionnaire_startflash_20221103_1646.csv",
    )
    import_questions(apps, file, "mixity_start")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0313_merge_20221103_1613"),
    ]

    operations = [migrations.RunPython(migrate_data)]
