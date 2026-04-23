from scoring.importsheets.import_20241003_1025 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    Category = apps.get_model("scoring", "Category")

    personal_engagement = Category.objects.get(slug="personal_engagement")

    personal_engagement.name = "Engagement professionnel"
    personal_engagement.slug = "professional_engagement"
    personal_engagement.save()

    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/scan/questionnaire_scan_20241211_1110.csv",
    )

    import_questions(apps, file, "mixity_evaluation_scan")


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0464_import_scan_v4"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
