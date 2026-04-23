from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0402_import_collaborateurs360_v47"),
    ]

    operations = [
        # migrations.AddField(
        #     model_name='evaluation',
        #     name='subscription_option',
        #     field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evaluations', to='subscriptions.subscriptionoption'),
        # ),
        migrations.AddField(
            model_name="evaluation",
            name="version",
            field=models.DateTimeField(
                null=True, verbose_name="Date de validation par l'utilisateur"
            ),
        )
    ]
