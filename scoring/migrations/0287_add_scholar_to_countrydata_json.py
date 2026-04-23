from django.db import migrations, models
import django.db.models.deletion


def add_scholarshipstudent(apps, schema_editor):
    CountryData = apps.get_model("scoring", "CountryData")

    for countrydata in CountryData.objects.only("data"):
        countrydata.data["scholarshipstudent"] = 0
        countrydata.save(update_fields=["data"])


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0286_import_ref_campus_2022_01"),
    ]

    operations = [
        migrations.RunPython(add_scholarshipstudent, lambda x, y: None),
    ]
