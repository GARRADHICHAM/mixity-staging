from django.db import migrations


def diag_not_collaborator(apps, schema_editor):
    # Le Diag est rempli par l'entreprise (comme à sa création en 0360) : avec
    # is_collaborator=True, generate_answers() ne crée aucune question.
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    QuestionSheetType.objects.filter(slug="mixity_evaluation_diag").update(
        is_collaborator=False
    )


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0473_merge_0470_import_diag_v18_0472_auto_20241219_1653"),
    ]

    operations = [
        migrations.RunPython(diag_not_collaborator, migrations.RunPython.noop),
    ]
