from django.db import migrations, models


def email_to_lowercase(apps, schemaeditor):
    MixityUser = apps.get_model("accounts", "MixityUser")

    for user in MixityUser.objects.all():
        if not user.email.islower():
            user.email = user.email.lower()
            user.username = user.username.lower()
            user.save()


class Migration(migrations.Migration):

    dependencies = [("accounts", "0112_alter_humancriteria_options")]

    operations = [migrations.RunPython(email_to_lowercase, lambda x, y: None)]
