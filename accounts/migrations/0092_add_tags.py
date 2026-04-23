from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    QuestionTag = apps.get_model("scoring", "QuestionTag")
    for tag in [
        "no_general",
        "no_gender",
        "no_disability",
        "no_ethnicity",
        "no_generations",
        "no_lgbt",
    ]:
        QuestionTag.objects.get_or_create(name=tag)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0091_alter_structure_booleans"),
    ]

    operations = [migrations.RunPython(migrate_data)]
