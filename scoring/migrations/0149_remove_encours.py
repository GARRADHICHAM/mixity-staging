from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    Comment = apps.get_model("scoring", "Comment")
    Comment.objects.filter(description_fr="en cours").update(description_fr=None)


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0148_fix_international_sheet3"),
    ]

    operations = [migrations.RunPython(migrate_data)]
