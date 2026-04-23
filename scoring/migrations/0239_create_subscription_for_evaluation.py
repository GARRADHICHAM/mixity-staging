from django.db import migrations, models
import django.db.models.deletion
import datetime


def create_subscription(apps, schema_editor):
    evaluation = apps.get_model("scoring", "Evaluation")
    subscription = apps.get_model("subscriptions", "Subscription")
    subscription_type = apps.get_model("subscriptions", "SubscriptionType")
    sub = subscription_type.objects.get(slug="global")
    for evaluation in evaluation.objects.filter(subscription=None):
        new_subscription = subscription.objects.create(
            is_active=True,
            start_date=datetime.datetime.now(),
            structure=evaluation.structure,
            subscription_type=sub,
        )
        evaluation.subscription = new_subscription
        evaluation.save()


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0238_evaluation_answers_rate_cache"),
    ]

    operations = [
        migrations.RunPython(create_subscription, lambda x, y: None),
    ]
