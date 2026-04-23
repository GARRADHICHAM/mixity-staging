from datetime import datetime, date

from django.core.management import BaseCommand
from django.db.models import Q
from django.template.context_processors import request
from django.utils import timezone, translation
from jours_feries_france import JoursFeries

from scoring.mails import alert_evaluation_reminder
from scoring.models import Evaluation


class Command(BaseCommand):
    def handle(self, *args, **options):
        min_date = date(2020, 10, 30)
        evaluations = Evaluation.objects.filter(
            is_validated_by_user=False, subscription__is_active=True
        ).exclude(
            Q(subscription=None)
            | Q(subscription__subscription_type__slug="human")
            | Q(subscription__start_date__lt=min_date)
        )
        durations = [
            10,
            10,
            10,
            15,
            15,
            30,
        ]  # Intervalles en jours entre chaque relance
        current_date = timezone.now()
        for evaluation in evaluations:
            if (
                not JoursFeries.is_bank_holiday(current_date.date())
                and 0 <= current_date.weekday() <= 4
                and evaluation.reminder_count < 6
                and (
                    not evaluation.last_reminder_date
                    or (current_date.date() - evaluation.last_reminder_date.date()).days
                    >= durations[evaluation.reminder_count]
                )
            ):
                evaluation.last_reminder_date = current_date
                evaluation.reminder_count += 1
                print(
                    "Evaluation : "
                    + str(evaluation.id)
                    + " - Relance n°"
                    + str(evaluation.reminder_count)
                )
                evaluation.save()
                first_owner = evaluation.entity.entity_level.structure.get_first_owner
                if first_owner:
                    translation.activate(first_owner.language)
                    alert_evaluation_reminder(
                        evaluation.entity.entity_level.structure.get_mail_display(),
                        evaluation,
                    )
