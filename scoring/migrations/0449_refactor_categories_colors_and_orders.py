from django.db import migrations


def refactor_categories_colors_and_orders(apps, schema_editor):
    Category = apps.get_model("scoring", "Category")

    category = Category.objects.get(slug="general_concept")
    category.color = "#FF7070"
    category.order = 101
    category.save()
    category = Category.objects.get(slug="professional_practices")
    category.color = "#0099FF"
    category.order = 102
    category.save()
    category = Category.objects.get(slug="cognitive_biases")
    category.color = "#03A87C"
    category.order = 103
    category.save()
    category = Category.objects.get(slug="communication")
    category.color = "#423C6B"
    category.order = 104
    category.save()
    category = Category.objects.get(slug="personal_engagement")
    category.color = "#47D4FF"
    category.order = 105
    category.save()
    category = Category.objects.get(slug="bonus_posture")
    category.color = "#E8EAED"
    category.order = 106
    category.save()

class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0448_import_diag_v13"),
    ]

    operations = [
        migrations.RunPython(refactor_categories_colors_and_orders, lambda x, y: None),
    ]
