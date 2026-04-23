from django.db import migrations
from subscriptions.models import SubscriptionPack, Product, SubscriptionOption
from payments.models import CheckoutSession


def injectCheckoutSession(apps, schema_editor):
    for checkoutsession in CheckoutSession.objects.all():
        for option in SubscriptionOption.objects.filter(tags__name="mixity_start"):
            if (
                checkoutsession.subscription.structure
                == option.subscriptionPack.structure
            ):
                checkoutsession.subscriptionOption = option
                checkoutsession.save()


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0003_checkoutsession_subscriptionoption"),
        ("subscriptions", "0051_update_tags_options"),
    ]
    operations = [
        migrations.RunPython(injectCheckoutSession),
    ]
