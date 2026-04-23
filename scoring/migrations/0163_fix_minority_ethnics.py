from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    SubQuestion = apps.get_model("scoring", "SubQuestion")
    subquestions = SubQuestion.objects.filter(
        question__sheets__type__slug="mixity_international"
    )
    subquestions.filter(label="Percentage of Minority ethnics").delete()
    subquestions.filter(label="Percentage of Minority ethnies").update(
        label="Percentage of Minority ethnics"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0162_fix_international_sheet14"),
    ]

    operations = [migrations.RunPython(migrate_data)]
