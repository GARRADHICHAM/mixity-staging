from django.db import migrations, models


def add_entity_to_structures(apps, schemaeditor):
    Structure = apps.get_model("accounts", "Structure")
    EntityLevel = apps.get_model("accounts", "EntityLevel")
    Entity = apps.get_model("accounts", "Entity")
    Membership = apps.get_model("accounts", "Membership")

    for structure in Structure.objects.all():
        entity_level = EntityLevel.objects.create(
            label="Groupe",
            structure=structure,
            level=0,
        )
        entity = Entity.objects.create(
            name=structure.juridic_name,
            slug=structure.slug,
            entity_level=entity_level,
            creation_year=structure.creation_year,
            workforce=structure.workforce,
            phone=structure.phone1,
        )
        entity.tags.set(structure.tags.all())
        for member in structure.memberships.all():
            Membership.objects.create(
                user=member.user,
                date_joined=member.date_joined,
                entity=entity,
                is_owner=member.is_owner,
                is_reader=member.is_reader,
            )
        for evaluation in structure.evaluations.all():
            evaluation.entity = entity
            evaluation.save()
        structure.slug = structure.slug + "-structure"
        structure.save()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0118_auto_20230227_1555"),
        ("scoring", "0330_evaluation_entity"),
    ]

    operations = [migrations.RunPython(add_entity_to_structures, lambda x, y: None)]
