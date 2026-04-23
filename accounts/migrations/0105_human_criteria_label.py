from django.db import migrations, models


def translate_label(apps, schemaeditor):
    Criteria = apps.get_model("accounts", "HumanCriteria")
    Choice = apps.get_model("accounts", "HumanCriteriaChoice")

    all_criteria = Criteria.objects.all()
    for criteria in all_criteria:
        criteria.label_fr = criteria.__dict__["label"]
        criteria.save()

    choices = Choice.objects.all()
    for choice in choices:
        choice.label_fr = choice.__dict__["label"]
        choice.save()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0104_auto_20220404_1112"),
        ("scoring", "0266_change_collaborator_position_to_criteria"),
    ]

    operations = [migrations.RunPython(translate_label, lambda x, y: None)]
