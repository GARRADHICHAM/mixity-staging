from django.db import migrations


def migrate_data(apps, schemaeditor):
    ComputedAnswerScore = apps.get_model("scoring", "ComputedAnswerScore")
    ComputedAnswerScore.objects.update(is_obsolete=True, is_own_data_obsolete=True)


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0250_alter_scorecategory_options"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
