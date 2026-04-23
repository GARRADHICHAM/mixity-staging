from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def injectSubscriptionPack(apps, schema_editor):
    Subscription = apps.get_model("subscriptions", "Subscription")
    SubscriptionPack = apps.get_model("subscriptions", "SubscriptionPack")
    today = timezone.now()
    subscriptions = Subscription.objects.all()

    for subscription in subscriptions.order_by("structure").distinct("structure"):
        # Création d'une instance de SubscriptionPack sans définir les tags
        subscription_pack_instance = SubscriptionPack(
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            is_active=subscription.is_active,
            structure=subscription.structure,
        )

        #  Parmi les abonnements actifs existants pour la même structure, on vérifie les dates à conserver.
        for doublons in subscriptions.filter(structure=subscription.structure):
            if (
                doublons.start_date
                and doublons.start_date < subscription_pack_instance.start_date
            ):
                subscription_pack_instance.start_date = doublons.start_date
            if doublons.end_date:
                if (
                    subscription_pack_instance.end_date is None
                    or doublons.end_date > subscription_pack_instance.end_date
                ):
                    subscription_pack_instance.end_date = doublons.end_date
            else:
                subscription_pack_instance.end_date = None

        # On s'assure qu'on n'a pas de doublon avec ces dates et cette structure :
        if not SubscriptionPack.objects.filter(
            structure=subscription_pack_instance.structure
        ).exists():
            subscription_pack_instance.save()


def injectProducts(apps, schema_editor):
    Product = apps.get_model("subscriptions", "Product")
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    diag = Product(
        is_active=True,
        label="Mixity Diag",
        slug="diag",
        question_sheet_type=QuestionSheetType.objects.get(
            slug="mixity_evaluation_diag"
        ),
    )
    diag.save()
    human = Product(
        is_active=True,
        label="Mixity Human",
        slug="human",
        question_sheet_type=QuestionSheetType.objects.get(
            slug="evaluation_collaborateurs_360"
        ),
    )
    human.save()


def linkToSubscriptionPack(instance):
    # Recherche du bon SubscriptionPack en fonction de la structure
    SubscriptionPack = apps.get_model("subscriptions", "SubscriptionPack")
    subscription_pack = SubscriptionPack.active_objects.get(
        structure=instance.structure
    )
    if subscription_pack:
        return subscription_pack
    else:
        return None


def linkToProduct(instance):
    Product = apps.get_model("subscriptions", "Product")
    try:
        product = Product.objects.get(slug=instance.subscription_type.slug)
    except Product.DoesNotExist:
        # Si le produit spécifié n'existe pas, on récupère le produit "diag" par défaut
        product = Product.objects.get(slug="diag")
    return product


def injectSubscriptionOption(apps, schema_editor):
    SubscriptionPack = apps.get_model("subscriptions", "SubscriptionPack")
    SubscriptionOption = apps.get_model("subscriptions", "SubscriptionOption")
    Product = apps.get_model("subscriptions", "Product")
    Subscription = apps.get_model("subscriptions", "Subscription")
    today = timezone.now()
    subscriptions = Subscription.objects.filter(
        is_active=True,
        subscription_type__is_active=True,
        start_date__lte=today,
    ).order_by("-start_date")

    for pack in SubscriptionPack.objects.all():
        old_subscriptions = subscriptions.filter(structure=pack.structure)
        for old_sub in old_subscriptions:
            if old_sub.subscription_type.slug == "human":
                product_slug = "human"
            else:
                product_slug = "diag"
            product = Product.objects.get(slug=product_slug)
            opt = SubscriptionOption(
                is_active=old_sub.is_active,
                start_date=old_sub.start_date,
                end_date=old_sub.end_date,
                product=product,
                subscriptionPack=pack,
            )
            opt.save()


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0403_subscriptionoption_evaluation"),
        ("subscriptions", "0045_auto_20240301_1438"),
    ]
    operations = [
        migrations.RunPython(injectSubscriptionPack, lambda x, y: None),
        migrations.RunPython(injectProducts),
        migrations.RunPython(injectSubscriptionOption),
    ]
