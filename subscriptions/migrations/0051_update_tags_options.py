from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone
from django.db.models import Q


def createTrialTag(apps, schema_editor):
    QuestionTag = apps.get_model("scoring", "QuestionTag")
    trial = QuestionTag(name="trial")
    trial.save()


def injectTagsSubOption(apps, schema_editor):
    Subscription = apps.get_model("subscriptions", "Subscription")
    SubscriptionPack = apps.get_model("subscriptions", "SubscriptionPack")
    SubscriptionOption = apps.get_model("subscriptions", "SubscriptionOption")
    QuestionTag = apps.get_model("scoring", "QuestionTag")
    today = timezone.now().date()

    for pack in SubscriptionPack.objects.all():
        options = (
            SubscriptionOption.objects.filter(subscriptionPack=pack)
            .exclude(product__slug="human")
            .order_by("-start_date")
        )
        for option in options:
            subscription = (
                Subscription.objects.filter(
                    is_active=option.is_active,
                    start_date=option.start_date,
                    end_date=option.end_date,
                    structure=pack.structure,
                )
                .exclude(subscription_type__slug="human")
                .order_by("start_date")
                .first()
            )
            evaluations = subscription.evaluations.all()
            if subscription.tags.exists():
                tag = QuestionTag.objects.get(name="trial")
                option.tags.add(tag)
                for evaluation in evaluations:
                    evaluation.tags.add(tag)
            if subscription.subscription_type.slug == "mixity_start":
                tag = QuestionTag.objects.get(name="mixity_start")
                option.tags.add(tag)
                for evaluation in evaluations:
                    evaluation.tags.add(tag)


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0050_auto_20240516_1051"),
    ]
    operations = [
        migrations.RunPython(createTrialTag),
        migrations.RunPython(injectTagsSubOption),
    ]
