from scoring.importsheets.import_20210701_1141 import import_questions
from django.db import migrations
import os
from django.conf import settings


def migrate_data(apps, schemaeditor):
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    SubscriptionType = apps.get_model("subscriptions", "SubscriptionType")

    q = QuestionSheetType.objects.create(slug="mixity_start", name="Mixity Start")
    s = SubscriptionType.objects.create(
        label="Mixity Start",
        pme_label="Mixity Start",
        slug="mixity_start",
        order=4,
        description="L'évaluation instantanée pour débuter votre politique de diversité et inclusion",
        is_active=False,
        allow_structure_evaluation=True,
        allow_public_display=True,
        allow_add_structure_members=True,
    )
    s.question_sheet_types.add(q)
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        "csv/startflash/questionnaire_startflash_20210831_0958.csv",
    )
    import_questions(apps, file, "mixity_start")


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0220_question_priority_order"),
    ]

    operations = [migrations.RunPython(migrate_data)]
