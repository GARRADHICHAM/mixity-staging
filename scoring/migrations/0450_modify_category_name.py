from django.db import migrations


def new_subcategories(apps, schema_editor):
    Category = apps.get_model("scoring", "Category")

    cat = Category.objects.get(slug="professional_practices")
    cat.name="Pratique professionnelle"
    cat.slug="professional_practice"
    cat.save()

class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0449_refactor_categories_colors_and_orders"),
    ]

    operations = [
        migrations.RunPython(new_subcategories, lambda x, y: None),
    ]
