from scoring.importsheets.import_20210903_0942 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    QuestionSheetType.objects.filter(slug="mixity_start").update(
        suffix_company_sheet="_start"
    )
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startflash/questionnaire_startflash_20210903_0947.csv",
    )
    import_questions(apps, file, "mixity_start")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0219_fix_international_sheet23"),
    ]

    operations = [migrations.RunPython(migrate_data)]
