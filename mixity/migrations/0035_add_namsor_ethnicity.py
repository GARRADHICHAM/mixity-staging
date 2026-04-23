from django.db import migrations

from address.models import Country


def migrate_data(apps, schemaeditor):

    # Solution Format choices

    NamsorEthnicity = apps.get_model("mixity", "NamsorEthnicity")

    newEthnicity = NamsorEthnicity.objects.update_or_create(
        key="Filipino",
        defaults={
            "name": "Philippin",
            "country_id": Country.objects.get(code="PH").id,
            "region": "Asie",
            "region2": "Asie",
            "sub_region": "Asie du Sud-Est",
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ("mixity", "0034_auto_20240621_1436"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
