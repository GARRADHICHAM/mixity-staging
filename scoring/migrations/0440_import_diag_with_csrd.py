from scoring.importsheets.import_20240527_1005 import import_questions
from django.db import migrations
import os
from django.conf import settings

def migrate_data(apps, schemaeditor):
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/diag/questionnaire_diag_20240819_1025.csv"
    )
    import_questions(apps, file, "mixity_evaluation_diag")
    

class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0439_create_csrd_category_and_subcategories"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
