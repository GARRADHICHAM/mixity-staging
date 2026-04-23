import os

from django.conf import settings
from django.db import migrations

from scoring.importsheets.import_20210420_1643 import import_questions


def migrate_data(apps, schemaeditor):
    Question = apps.get_model("scoring", "Question")
    Choice = apps.get_model("scoring", "Choice")
    q = Question.objects.filter(google_sheets_id=2020037).first()
    if q is not None and not q.choices.exists():
        Choice.objects.create(question=q, value=5, label="Entre 0 et 1%")
        Choice.objects.create(question=q, value=4, label="Entre 1 et 3%")
        Choice.objects.create(question=q, value=3, label="Entre 3 et 5%")
        Choice.objects.create(question=q, value=2, label="Entre 5 et 10%")
        Choice.objects.create(question=q, value=1, label="Plus de 10%")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0187_auto_20210625_1406"),
    ]

    operations = [migrations.RunPython(migrate_data)]
