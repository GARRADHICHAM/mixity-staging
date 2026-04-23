from django.db import migrations
from django.utils.translation import ugettext_lazy as _


def migrate_data(apps, schemaeditor):
    # Preparing models to not be imported in migrations
    ADPIndicatorType = apps.get_model("sirh", "ADPIndicatorType")
    ADPSoftware = apps.get_model("sirh", "ADPSoftware")
    software, _ = ADPSoftware.objects.get_or_create(name="decidium")

    for indicator in [
        "promotion_age",
        "age_paygap",
        "remuneration_increase_age",
        "promotion_gender",
        "citizenships",
        "remuneration_increase_gender",
        "turnover",
        "exiting",
        "hiring",
        "gender_paygap",
        "gender_repartition",
        "age_pyramid",
    ]:
        indicator, created = ADPIndicatorType.objects.get_or_create(name=indicator)
        indicator.softwares.set([software])


class Migration(migrations.Migration):
    dependencies = [
        (
            "sirh",
            "0012_adpindicatortype_label",
        ),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
