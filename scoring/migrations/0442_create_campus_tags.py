from django.db import migrations


def migrate_data(apps, schemaeditor):
    QuestionTag = apps.get_model("scoring", "QuestionTag")

    tags = ["campus_teacher__no_cadre", "campus_teacher__cadre", "campus_collaborator__no_cadre", "campus_collaborator__cadre"]

    for tag in tags:
        new_tag = QuestionTag.objects.create(
            name=tag,
        )
        new_tag.save()


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0441_import_diag_with_csrd_indicators"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
