from django.db import migrations, models
import django.db.models.deletion


def set_collaborator_evaluation(apps, schemaeditor):
    Collaborator = apps.get_model("scoring", "Collaborator")
    collaborators = Collaborator.objects.all()
    for col in collaborators:
        if (
            not col.answers
            or not col.answers.first()
            or not col.answers.first().evaluation_id
        ):
            col.delete()
        else:
            col.evaluation = col.answers.first().evaluation
            col.save()


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0257_collaborator_evaluation"),
    ]

    operations = [
        migrations.RunPython(set_collaborator_evaluation, lambda x, y: None),
    ]
