from django.db import migrations
from django_countries import countries


def import_entity_countryfield_from_tags(apps, schema_editor):
    Entity = apps.get_model("accounts", "Entity")

    for entity in Entity.objects.all():
        tags = entity.tags.all()
        for tag in tags:
            for country in countries:
                if tag.name == country.code.lower():
                    entity.country = country
                    entity.save()
                    pass


def import_structure_countryfield_from_tags(apps, schema_editor):
    Structure = apps.get_model("accounts", "Structure")
    for structure in Structure.objects.all():
        tags = structure.tags.all()
        for tag in tags:
            for country in countries:
                if tag.name == country.code.lower():
                    structure.country = country
                    structure.save()
                    pass


def update_structure_countryfield(apps, schema_editor):
    Structure = apps.get_model("accounts", "Structure")

    for structure in Structure.objects.all():
        try:
            country_address = structure.address.locality.state.country
            structure.country = country_address
            structure.save()
        except AttributeError:
            print(
                f"Adresse mal formatée pour la structure {structure.juridic_name} {structure.address} "
            )
        except Exception as e:
            print(
                f"Erreur lors de la mise à jour de la structure avec ID {structure.juridic_name}: {e}"
            )


def update_entity_countryfield(apps, schema_editor):
    Entity = apps.get_model("accounts", "Entity")

    for entity in Entity.objects.all():
        try:
            country_address = entity.address.locality.state.country
            entity.country = country_address
            entity.save()
        except AttributeError:
            print(
                f"Adresse mal formatée pour l'entité avec ID {entity.name} {entity.address}"
            )
        except Exception as e:
            print(
                f"Erreur lors de la mise à jour de l'entité avec ID {entity.name} {entity.address}: {e}"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0134_auto_20240723_1011"),
    ]

    operations = [
        migrations.RunPython(update_structure_countryfield),
        migrations.RunPython(update_entity_countryfield),
        migrations.RunPython(import_entity_countryfield_from_tags),
        migrations.RunPython(import_structure_countryfield_from_tags),
    ]
