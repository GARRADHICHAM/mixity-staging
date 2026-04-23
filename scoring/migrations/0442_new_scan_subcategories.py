from django.db import migrations


def new_subcategories(apps, schema_editor):
    SubCategory = apps.get_model("scoring", "SubCategory")

    SubCategory.objects.create(
        slug="sourcing",
        name="Sourcing",
        name_fr="Sourcing",
        name_en="Sourcing",
        name_es="Búsqueda de fuentes",
        short_name="Sourcing",
        order=30,
        color="#ffcfc9",
    )
    SubCategory.objects.create(
        slug="interview",
        name="Entretien",
        name_fr="Entretien",
        name_en="Interview",
        name_es="Entrevista",
        short_name="Entretien",
        order=31,
        color="#ffc8aa",
    )
    SubCategory.objects.create(
        slug="planning",
        name="Préparation",
        name_fr="Préparation",
        name_en="Planning",
        name_es="Planificación",
        short_name="Préparation",
        order=32,
        color="#ffe59f",
    )
    SubCategory.objects.create(
        slug="prerequisites",
        name="Prérequis",
        name_fr="Prérequis",
        name_en="Pre-requisites",
        name_es="Prerrequisitos",
        short_name="Prérequis",
        order=33,
        color="#d4edbc",
    )
    SubCategory.objects.create(
        slug="selection",
        name="Sélection",
        name_fr="Sélection",
        name_en="Selection",
        name_es="Selección",
        short_name="Sélection",
        order=34,
        color="#bfe1f6",
    )
    SubCategory.objects.create(
        slug="onboarding",
        name="Onboarding",
        name_fr="Onboarding",
        name_en="Onboarding",
        name_es="Incorporación",
        short_name="Onboarding",
        order=35,
        color="#e8eaed",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0441_merge_20240814_1422"),
    ]

    operations = [
        migrations.RunPython(new_subcategories, lambda x, y: None),
    ]
