from django.db import migrations, models


def rename_lgbt_category(apps, schema_editor):
    Category = apps.get_model("scoring", "Category")

    category = Category.objects.get(slug="lgbt")
    category.name = "LGBTQIA+"
    category.save()


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0360_ref_2023_new_questionsheet_type"),
    ]

    operations = [
        migrations.RunPython(rename_lgbt_category, lambda x, y: None),
    ]
