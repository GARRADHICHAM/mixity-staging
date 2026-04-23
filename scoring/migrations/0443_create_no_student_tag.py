from django.db import migrations


def migrate_data(apps, schemaeditor):
    QuestionTag = apps.get_model("scoring", "QuestionTag")

    tags = ["campus_no_student"]

    for tag in tags:
        new_tag = QuestionTag.objects.create(
            name=tag,
        )
        new_tag.save()


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0442_create_campus_tags"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
