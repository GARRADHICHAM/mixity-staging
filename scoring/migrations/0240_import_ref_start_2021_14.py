import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210909_1138 import import_questions


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startup2021/questionnaire_start2021_20211203_1205.csv",
    )
    import_questions(apps, file, "mixity_evaluation_globale_pme", "startup")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0239_create_subscription_for_evaluation"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: x)]
