from django.db import migrations

from act.models import SolutionKeyword


def migrate_data(apps, schemaeditor):

    # Keywords choices
    keywords_choices = (
        ("accessibility", "Accessibilité"),
        ("purchases", "Achats"),
        ("caregivers", "Aidants"),
        ("cognitive-biases", "Biais Cognitifs"),
        ("gender-equality-index", "Index égalité"),
        ("young-people", "Jeunes"),
        ("label-and-certification", "Label et certification"),
        ("chronic-condition", "Maladie chronique"),
        ("neurodiversity", "Neurodiversité"),
        ("parenthood", "Parentalité"),
        ("mental-health", "Santé mentale"),
        ("older-people", "Seniors"),
    )

    # Filling languages
    for keyword in keywords_choices:
        kw_slug, kw_label = keyword
        SolutionKeyword.objects.create(slug=kw_slug, label=kw_label)


class Migration(migrations.Migration):

    dependencies = [
        ("act", "0002_solutionkeyword"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
