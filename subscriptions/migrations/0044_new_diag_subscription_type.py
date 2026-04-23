from django.db import migrations, models


def new_subscriptiontype(apps, schema_editor):
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    SubscriptionType = apps.get_model("subscriptions", "SubscriptionType")

    subscription = SubscriptionType.objects.create(
        slug="diag",
        label="Mixity Diag",
        pme_label="Mixity Diag",
        order=1,
        description_fr="L'évaluation de votre politique de diversité et inclusion",
        description_en="The assessment of your Diversity and Inclusion policy",
        allow_structure_evaluation=True,
        allow_public_display=True,
        allow_add_structure_members=True,
    )
    questionsheettype = QuestionSheetType.objects.get(slug="mixity_evaluation_diag")
    subscription.question_sheet_types.add(questionsheettype)
    global_prices = SubscriptionType.objects.get(slug="global").prices.all()
    subscription.prices.set(global_prices)
    subscription.save()


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0360_ref_2023_new_questionsheet_type"),
        ("subscriptions", "0043_auto_20230223_1116"),
    ]

    operations = [
        migrations.RunPython(new_subscriptiontype, lambda x, y: None),
    ]
