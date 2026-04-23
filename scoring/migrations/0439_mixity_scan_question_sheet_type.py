from django.db import migrations


def new_questionsheettype(apps, schema_editor):
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")

    QuestionSheetType.objects.create(
        slug="mixity_evaluation_scan",
        name="Evaluation Mixity Scan",
        is_collaborator=True,
        workforce_limit=None,
        suffix_company_sheet="_scan",
        tag="scan",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0438_fill_profile_and_skill_models"),
    ]

    operations = [
        migrations.RunPython(new_questionsheettype, lambda x, y: None),
    ]
