from django.db import migrations, models
import django.db.models.deletion


def create_campus_questionsheet_type(apps, schema_editor):
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    QuestionSheetType.objects.update_or_create(
        slug="mixity_evaluation_campus",
        defaults={
            "name": "Evaluation Mixity Campus",
            "suffix_company_sheet": "_campus",
            "tag": "campus",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0283_question_target"),
    ]

    operations = [
        migrations.RunPython(create_campus_questionsheet_type, lambda x, y: None),
    ]
