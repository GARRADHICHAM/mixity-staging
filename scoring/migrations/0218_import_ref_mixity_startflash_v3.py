from scoring.importsheets.import_20210831_1505 import import_questions
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
        "csv/startflash/questionnaire_startflash_20210901_1007.csv",
    )
    import_questions(apps, file, "mixity_start")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0217_import_ref_mixity_startflash_v2"),
    ]

    operations = [migrations.RunPython(migrate_data)]
