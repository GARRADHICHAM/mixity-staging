from django.db import migrations, models


def new_questionsheettype(apps, schema_editor):
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")

    QuestionSheetType.objects.create(
        slug="mixity_evaluation_diag",
        name="Evaluation Mixity Diag",
        is_collaborator=False,
        workforce_limit=None,
        suffix_company_sheet="_global",
        tag="global",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0359_auto_20230612_0936"),
    ]

    operations = [
        migrations.RunPython(new_questionsheettype, lambda x, y: None),
    ]
