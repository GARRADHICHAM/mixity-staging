import csv
from datetime import datetime

from django.core.files.temp import NamedTemporaryFile
from django.core.management import BaseCommand
from django.db.models import F, Q, When, Case
from accounts.mails import send_users_export
from accounts.models import MixityUser


class Command(BaseCommand):
    """
    Send an email of all users present in the database
    """

    def handle(self, *args, **options):
        def get_case_entity_or_structure(field):
            return Case(
                When(
                    Q(memberships__entity=None),
                    then=F(f"memberships__structure__subscriptions__{field}"),
                ),
                default=F(f"memberships__entity__evaluations__subscription__{field}"),
            )

        def get_case(then, default):
            return Case(
                When(
                    Q(
                        memberships__entity__evaluations__subscription__end_date__gte=datetime.now()
                    ),
                    then=then,
                ),
                default=default,
            )

        users = (
            MixityUser.objects.exclude(memberships=None)
            .annotate(
                active=get_case(True, False),
                subscription_type=get_case(
                    F(
                        "memberships__entity__evaluations__subscription__subscription_type__slug"
                    ),
                    get_case_entity_or_structure("subscription_type__slug"),
                ),
                subscription_end_date=get_case(
                    F("memberships__entity__evaluations__subscription__end_date"),
                    get_case_entity_or_structure("end_date"),
                ),
                main_structure=get_case(
                    F("memberships__entity__name"),
                    Case(
                        When(
                            Q(memberships__entity=None),
                            then=F("memberships__structure__juridic_name"),
                        ),
                        default=F("memberships__entity__name"),
                    ),
                ),
                solution=Case(
                    When(
                        memberships__structure__solver__isnull=False,
                        then=F("memberships__structure__solver__id"),
                    ),
                    default=F("memberships__structure__solver__id"),
                ),
            )
            .distinct("email")
        )
        header = [
            [
                "Prénom",
                "Nom",
                "Email",
                "Langue",
                "Structure",
                "Est une solution",
                "Abonnement actif",
                "Type d'abonnement",
                "Date d'expiration",
            ]
        ]
        array = [
            [
                user.first_name,
                user.last_name,
                user.email,
                user.language,
                user.main_structure,
                user.solution is not None,
                user.active,
                user.subscription_type,
                user.subscription_end_date,
            ]
            for user in users
        ]
        result = header + array

        email = input("Email du destinataire du fichier exporté ?\n")
        with NamedTemporaryFile(
            mode="w", delete=False, prefix="export users_", suffix=".csv"
        ) as fd:
            self.writer = csv.writer(fd, delimiter=";", quoting=csv.QUOTE_NONNUMERIC)
            self.writer.writerows(result)
            send_users_export(email, "export_users.csv", fd.name)
