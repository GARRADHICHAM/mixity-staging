from django.db import migrations
from django.utils.translation import ugettext_lazy as _


def migrate_data(apps, schemaeditor):
    # Preparing models to not be imported in migrations
    BestPracticePublic = apps.get_model("act", "BestPracticePublic")
    BestPracticeType = apps.get_model("act", "BestPracticeType")
    BestPracticeKeyword = apps.get_model("act", "BestPracticeKeyword")
    BestPracticeSize = apps.get_model("act", "BestPracticeSize")
    BestPracticeOrganizationType = apps.get_model("act", "BestPracticeOrganizationType")

    # Lists of values
    ORGANIZATION_TYPE_CHOICES = (
        ("community", _("Collectivité")),
        ("association", _("Association")),
        ("sme", _("PME")),
        ("midcaps", _("ETI")),
        ("large-company", _("Grande entreprise")),
        ("school", _("École")),
    )

    BEST_PRACTICES_PUBLIC_CHOICES = (
        ("employees", _("Collaborateurs")),
        ("managers", _("Managers (f/h/nb)")),
        ("steering", _("Direction")),
        ("newcomers", _("Nouveaux arrivants (f/h/nb)")),
        ("supplier", _("Fournisseur")),
        ("customer", _("Client")),
        ("intern", _("Stagiaire")),
        ("apprenticeship-student", _("Alternant (f/h/nb)")),
        ("multiple-option", _("Options multiples")),
    )

    BEST_PRACTICES_TYPE_CHOICES = (
        ("action", _("Action")),
        ("process", _("Process")),
        ("event", _("Évènement")),
        ("partnership", _("Partenariat")),
        ("program", _("Programme")),
    )

    BEST_PRACTICES_SIZE_CHOICES = (
        ("less-than-500", _("-500 personnes")),
        ("more-than-500", _("+500 personnes")),
    )

    BEST_PRACTICES_KEYWORD_CHOICES = (
        ("refugees", _("Réfugiés (f/h/nb)")),
        ("neurodiversity", _("Neurodiversité")),
        ("caregiver", _("aidant (f/h/nb)")),
        ("employer-brand", _("Marque employeur")),
        ("religious-fact", _("Fait religieux")),
        ("older-people", _("Seniors")),
        ("mental-health", _("Santé mentale")),
        ("parenting", _("Parentalité")),
        ("chronic-disease", _("Maladie Chronique")),
        ("young-people", _("Jeunes")),
    )

    # Filling Public
    for public in BEST_PRACTICES_PUBLIC_CHOICES:
        public_slug, public_label = public
        BestPracticePublic.objects.create(
            slug=public_slug,
            label=public_label,
        )

    # Filling Type
    for type_ in BEST_PRACTICES_TYPE_CHOICES:
        type_slug, type_label = type_
        BestPracticeType.objects.create(
            slug=type_slug,
            label=type_label,
        )

    # Filling Keyword
    for keyword in BEST_PRACTICES_KEYWORD_CHOICES:
        keyword_slug, keyword_label = keyword
        BestPracticeKeyword.objects.create(
            slug=keyword_slug,
            label=keyword_label,
        )

    # Filling Organization Type
    for organization_type in ORGANIZATION_TYPE_CHOICES:
        organization_type_slug, organization_type_label = organization_type
        BestPracticeOrganizationType.objects.create(
            slug=organization_type_slug,
            label=organization_type_label,
        )

    # Filling Size
    for size in BEST_PRACTICES_SIZE_CHOICES:
        size_slug, size_label = size
        BestPracticeSize.objects.create(
            slug=size_slug,
            label=size_label,
        )


class Migration(migrations.Migration):
    dependencies = [
        (
            "act",
            "0021_merge_0020_auto_20230525_1131_0020_auto_20230530_1501",
        ),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
