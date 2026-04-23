from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def injectTagsOptions(apps, schema_editor):
    Subscription = apps.get_model("subscriptions", "Subscription")
    SubscriptionOption = apps.get_model("subscriptions", "SubscriptionOption")
    options = SubscriptionOption.objects.all()

    for option in options:
        if option.product.slug == "human":
            old_subscription = Subscription.objects.get(
                start_date=option.start_date,
                end_date=option.end_date,
                structure=option.subscriptionPack.structure,
                subscription_type__slug=option.product.slug,
            )
        else:
            old_subscription = (
                Subscription.objects.filter(
                    start_date=option.start_date,
                    end_date=option.end_date,
                    structure=option.subscriptionPack.structure,
                )
                .exclude(subscription_type__slug="human")
                .first()
            )
        old_tags = old_subscription.tags.all()
        for tag in old_tags:
            option.tags.add(tag)


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0052_delete_price"),
    ]
    operations = [migrations.RunPython(injectTagsOptions)]
