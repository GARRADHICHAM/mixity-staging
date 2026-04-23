from django.db import migrations
from django.utils.translation import ugettext_lazy as _


def migrate_data(apps, schemaeditor):
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    diag = QuestionSheetType.objects.get(slug="mixity_evaluation_diag")
    diag.suffix_company_sheet = ""
    diag.save()


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0382_import_diag_v7"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
