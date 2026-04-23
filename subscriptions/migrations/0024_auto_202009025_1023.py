from django.db import migrations


def migrate_data(apps, schemaeditor):
    SubscriptionType = apps.get_model('subscriptions', 'SubscriptionType')
    for sub in SubscriptionType.objects.all():
        sub.pme_label = sub.pme_label.replace('Evaluation', 'Évaluation')
        sub.label = sub.label.replace('Evaluation', 'Évaluation')
        sub.save()


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0023_auto_20200904_1033'),
    ]

    operations = [
        migrations.RunPython(migrate_data, lambda x, y: None)
    ]
