from django.db import migrations


def injectProducts(apps, schema_editor):
    Product = apps.get_model("subscriptions", "Product")
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    scan = Product(
        is_active=True,
        label="Mixity Scan",
        slug="scan",
        question_sheet_type=QuestionSheetType.objects.get(
            slug="mixity_evaluation_scan"
        ),
    )
    scan.save()


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0055_alter_subscriptionpack_structure"),
    ]
    operations = [
        migrations.RunPython(injectProducts, lambda x, y: None),
    ]
