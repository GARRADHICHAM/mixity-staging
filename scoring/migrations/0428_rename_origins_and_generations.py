from django.db import migrations, models


def rename_origins_and_generations_category(apps, schema_editor):
    Category = apps.get_model("scoring", "Category")

    origins = Category.objects.get(slug="cultural_diversity")
    origins.name = "Origines"
    origins.save()
    generations = Category.objects.get(slug="generational_diversity")
    generations.name = "Générations"
    generations.save()


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0427_import_collaborateurs360_v59"),
    ]

    operations = [
        migrations.RunPython(rename_origins_and_generations_category, lambda x, y: None),
    ]
