from scoring.importsheets.import_20220919_1405 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/collaborateurs360/questionnaire_collaborateurs360_20221116_0948.csv",
    )
    import_questions(apps, file, "evaluation_collaborateurs_360")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0315_import_ref_mixity_startflash_v10"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
