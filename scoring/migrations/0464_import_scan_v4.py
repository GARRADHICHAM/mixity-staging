from scoring.importsheets.import_20241003_1025 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    SubCategory = apps.get_model("scoring", "SubCategory")
    Question = apps.get_model("scoring", "Question")

    planning = SubCategory.objects.get(slug="planning")
    planning.order = 30
    planning.save()

    sourcing = SubCategory.objects.get(slug="sourcing")
    sourcing.order = 31
    sourcing.save()

    interview = SubCategory.objects.get(slug="interview")
    interview.order = 32
    interview.save()

    selection = SubCategory.objects.get(slug="selection")
    selection.order = 33
    selection.save()

    onboarding = SubCategory.objects.get(slug="onboarding")
    onboarding.order = 34
    onboarding.save()

    if SubCategory.objects.filter(slug="prerequisites").exists():
        prerequisites = SubCategory.objects.get(slug="prerequisites")

        relatedObjects = Question.objects.filter(subcategory=prerequisites, google_sheets_id__in=["202403001", "202403005", "202403022", "202403024"])
        relatedObjects.update(subcategory=selection)

        relatedObjects = Question.objects.filter(subcategory=prerequisites, google_sheets_id__in=["202403002", "202403003", "202403004", "202403007"])
        relatedObjects.update(subcategory=sourcing)

        relatedObjects = Question.objects.filter(subcategory=prerequisites, google_sheets_id__in=["202403032", "202403037", "202403039"])
        relatedObjects.update(subcategory=planning)

        prerequisites.delete()

    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/scan/questionnaire_scan_20241204_1615.csv",
    )

    import_questions(apps, file, "mixity_evaluation_scan")


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0463_import_diag_v16"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
