from django.db.models import Q

from scoring.importsheets.import_20210909_1138 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    Category = apps.get_model("scoring", "Category")
    categories = Category.objects.exclude(
        Q(slug="your-suggestions") | Q(slug="gender") | Q(slug="all")
    )
    colors = {
        "disability": ["#0099FF", "#4F6CFF", "#47B1FF", "#BDDABD", "#8056FE"],
        "cultural_diversity": ["#18FFC3", "#AFF892", "#00BFB7", "#73B1F0", "#8056FE"],
        "generational_diversity": [
            "#423C6B",
            "#723486",
            "#40B6FF",
            "#73B1F0",
            "#3242D9",
        ],
        "lgbt": ["#47D4FF", "#2797E0", "#00FFF7", "#307BA2", "#9E9AB2"],
    }
    for category in categories:
        subcategories = category.subcategories.filter(
            Q(slug="recrutement")
            | Q(slug="gouvernance")
            | Q(slug="sensibilisation")
            | Q(slug="qualite-de-vie-au-travail")
            | Q(slug="carriere")
        )
        for i in range(len(subcategories)):
            subcategory = subcategories[i]
            subcategory.color = colors[category.slug][i]
            subcategory.save()


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0244_import_collaborateurs360_v7"),
    ]

    operations = [migrations.RunPython(migrate_data)]
