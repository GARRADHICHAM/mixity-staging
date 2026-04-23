from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    Question = apps.get_model("scoring", "Question")
    q = Question.objects.filter(google_sheets_id=20213040).first()
    if q:
        q.subquestions.filter(ui_type="valeur").delete()
        q.subquestions.update(ui_type="valeur")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0160_fix_international_sheet13"),
    ]

    operations = [migrations.RunPython(migrate_data)]
