from django.db import migrations
from django.conf import settings


def nestle_actions_migrations(apps, schema_editor):
    Evaluation = apps.get_model("scoring", "Evaluation")
    ScoreCategory = apps.get_model("scoring", "ScoreCategory")
    Action = apps.get_model("scoring", "Action")

    if settings.ENVIRONMENT_NAME.lower() == "prod":
        old_eval = Evaluation.objects.get(pk=878)
        new_eval = Evaluation.objects.get(pk=903)
        old_scores_categories = ScoreCategory.objects.filter(evaluation=old_eval)
        new_scores_categories = ScoreCategory.objects.filter(evaluation=new_eval)
        for score_category in new_scores_categories:
            actions = Action.objects.filter(scorecategory=old_scores_categories.get(category=score_category.category))
            for action in actions:
                Action.objects.create(
                    scorecategory=score_category,
                    intitules_detail=action.intitules_detail,
                    descriptif_detail=action.descriptif_detail,
                    intitules_aim=action.intitules_aim,
                    descriptif_aim=action.descriptif_aim,
                )


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0455_merge_20241009_1221"),
    ]

    operations = [
        migrations.RunPython(nestle_actions_migrations, lambda x, y: None),
    ]
