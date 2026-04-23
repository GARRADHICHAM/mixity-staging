from scoring.importsheets.import_20210224_1427 import import_questions, revert_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(settings.STATICFILES_DIRS[0], "csv/international/questionnaire_international_20210310_1458.csv")
    import_questions(apps, file, "mixity_international")


def revert_data(apps, schemaeditor):
    revert_questions(apps)


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0134_fix_international_sheet_split_by_ethnies"),
    ]

    operations = [migrations.RunPython(migrate_data, revert_data)]
