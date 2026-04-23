from scoring.importsheets.import_20220907_0927 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/international/questionnaire_international_20220913_1449.csv",
    )
    import_questions(apps, file, "mixity_international")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0297_merge_20220912_1445"),
    ]

    operations = [migrations.RunPython(migrate_data)]
