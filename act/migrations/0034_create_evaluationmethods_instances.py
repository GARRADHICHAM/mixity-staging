from django.db import migrations, models


def injectElearningEvaluationMethods(apps, schema_editor):
    ElearningEvaluationMethod = apps.get_model("act", "ElearningEvaluationMethod")
    ElearningEvaluationMethod.objects.create(
        label="Test de connaissances", slug="knowledge_assessment"
    )
    ElearningEvaluationMethod.objects.create(label="Cas pratique", slug="case_studies")
    ElearningEvaluationMethod.objects.create(label="Quiz", slug="quiz")


class Migration(migrations.Migration):

    dependencies = [
        ("act", "0033_auto_20240930_1111"),
    ]

    operations = [migrations.RunPython(injectElearningEvaluationMethods)]
