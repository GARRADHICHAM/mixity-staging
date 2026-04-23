from django.db import migrations, models
import django.db.models.deletion

def create_new_tag(apps, schema_editor):
    QuestionTag = apps.get_model("scoring", "QuestionTag")
    QuestionTag.objects.get_or_create(name="gender_only")

class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0278_create_2021002_missing_answers'),
    ]

    operations = [
        migrations.RunPython(create_new_tag, lambda x, y: None),
    ]
