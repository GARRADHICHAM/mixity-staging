from scoring.importsheets.import_20220131_1642 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/collaborateurs360/questionnaire_collaborateurs360_20220309_1252.csv",
    )
    import_questions(apps, file, "evaluation_collaborateurs_360")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0257_scorecategory_is_evolution_delta_hidden"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
