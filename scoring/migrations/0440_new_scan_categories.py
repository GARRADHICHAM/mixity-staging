from django.db import migrations


def new_categories(apps, schema_editor):
    Category = apps.get_model("scoring", "Category")

    Category.objects.create(
        slug="general_concept",
        name="Notions générales",
        order=100,
        weight_index=1,
        color="#ffcfc9",
    )
    Category.objects.create(
        slug="communication",
        name="Communication",
        order=101,
        weight_index=1,
        color="#ffc8aa",
    )
    Category.objects.create(
        slug="personal_engagement",
        name="Engagement personnel",
        order=102,
        weight_index=1,
        color="#ffe59f",
    )
    Category.objects.create(
        slug="professional_practices",
        name="Pratiques professionnelles",
        order=103,
        weight_index=1,
        color="#d4edbc",
    )
    Category.objects.create(
        slug="cognitive_biases",
        name="Biais cognitifs",
        order=104,
        weight_index=1,
        color="#bfe1f6",
    )
    Category.objects.create(
        slug="bonus_posture",
        name="Bonus - Attitude",
        order=105,
        weight_index=1,
        color="#e8eaed",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0439_mixity_scan_question_sheet_type"),
    ]

    operations = [
        migrations.RunPython(new_categories, lambda x, y: None),
    ]
