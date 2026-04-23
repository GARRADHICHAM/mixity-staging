from django.db import migrations, models
from django.conf import settings


# Redirect evaluations subscription to new main structure subscriptions
def redirect_subscriptions(structure, evaluations, Subscription):
    for evaluation in evaluations:
        subscription = (
            Subscription.objects.filter(
                structure=structure,
                subscription_type__slug=evaluation.subscription.subscription_type,
            )
            .order_by("-start_date")
            .first()
        )
        if subscription:
            evaluation.subscription = subscription
            evaluation.save()
        else:
            evaluation.subscription.structure = structure
            evaluation.subscription.save()


# Function to move every entites to the same strutures and all on the same level
def create_only_one_new_level(
    label, structure, structure_ids, Subscription, Structure, EntityLevel, Entity
):
    entity_level = EntityLevel.objects.create(
        label=label,
        structure=structure,
        level=1,
    )
    parent = Entity.objects.get(entity_level__structure=structure)
    for structure_id in structure_ids:
        entity = Entity.objects.get(entity_level__structure=structure_id)
        if entity:
            entity.entity_level = entity_level
            entity.parent_entity = parent
            redirect_subscriptions(structure, entity.evaluations.all(), Subscription)
            for objective in Structure.objects.get(pk=structure_id).objectives.all():
                objective.structure = structure
                objective.save()
            entity.save()
            Structure.objects.get(pk=structure_id).delete()


# Recursive function to move every chloe's entities to main structure
def move_chloes_entities(
    level,
    level_2,
    main_structure,
    structure_id,
    parent,
    Subscription,
    Structure,
    Entity,
):
    entity = Entity.objects.get(entity_level__structure=structure_id)
    if entity:
        entity.entity_level = level
        entity.parent_entity = parent
        redirect_subscriptions(main_structure, entity.evaluations.all(), Subscription)
        entity.save()
        if structure_id == 520:
            for secondary_structure_id in [509, 508]:
                move_chloes_entities(
                    level_2,
                    level_2,
                    main_structure,
                    secondary_structure_id,
                    entity,
                    Subscription,
                    Structure,
                    Entity,
                )
        elif structure_id == 505:
            for secondary_structure_id in [502, 503, 504, 499]:
                move_chloes_entities(
                    level_2,
                    level_2,
                    main_structure,
                    secondary_structure_id,
                    entity,
                    Subscription,
                    Structure,
                    Entity,
                )
        Structure.objects.get(pk=structure_id).delete()


# Moving entities to structures that already need to work as multi-structures
def move_existing_entities(apps, schemaeditor):
    if settings.ENVIRONMENT_NAME.lower() != "production":
        return
    Structure = apps.get_model("accounts", "Structure")
    EntityLevel = apps.get_model("accounts", "EntityLevel")
    Entity = apps.get_model("accounts", "Entity")
    Subscription = apps.get_model("subscriptions", "Subscription")

    # SMCP
    create_only_one_new_level(
        "Région",
        Structure.objects.get(pk=412),
        [351, 349, 350],
        Subscription,
        Structure,
        EntityLevel,
        Entity,
    )
    # H&H
    create_only_one_new_level(
        "Région",
        Structure.objects.get(pk=413),
        [403, 404, 405, 406, 407],
        Subscription,
        Structure,
        EntityLevel,
        Entity,
    )
    # Labeyrie
    create_only_one_new_level(
        "Société",
        Structure.objects.get(pk=396),
        [326, 250, 242, 245, 246],
        Subscription,
        Structure,
        EntityLevel,
        Entity,
    )
    # Axens
    create_only_one_new_level(
        "Société",
        Structure.objects.get(pk=534),
        [435, 434],
        Subscription,
        Structure,
        EntityLevel,
        Entity,
    )
    # Vivendi
    create_only_one_new_level(
        "Société",
        Structure.objects.get(pk=193),
        [195, 186, 149, 148, 145],
        Subscription,
        Structure,
        EntityLevel,
        Entity,
    )

    # Chloe
    structure = Structure.objects.get(pk=526)
    level_1 = EntityLevel.objects.create(
        label="Région",
        structure=structure,
        level=1,
    )
    level_2 = EntityLevel.objects.create(
        label="Pays",
        structure=structure,
        level=2,
    )
    parent = Entity.objects.get(entity_level__structure=structure)
    for structure_id in [520, 505, 427, 425, 422, 415]:
        move_chloes_entities(
            level_1,
            level_2,
            structure,
            structure_id,
            parent,
            Subscription,
            Structure,
            Entity,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0124_alter_entity_parent_entity"),
    ]

    operations = [
        migrations.RunPython(move_existing_entities, lambda x, y: None),
    ]
