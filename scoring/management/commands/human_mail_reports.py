from datetime import datetime, date

from django.core.management import BaseCommand
from django.template.context_processors import request
from django.utils import timezone

from scoring.mails import send_human_statistics
from scoring.models import Evaluation


class Command(BaseCommand):
    """
    Send an email to human evaluation structure owner, with statistics regarding number of respondants to human evaluation.

    Frenquency: 1 reminder per week during 4 weeks
    """

    def handle(self, *args, **options):
        evaluations = Evaluation.objects.filter(
            is_validated_by_user=False,
            subscription__is_active=True,
            subscription__subscription_type__slug="human",
        ).exclude(subscription=None)

        current_date = timezone.now()
        for evaluation in evaluations:
            if (
                evaluation.reminder_count == 0
            ):  # first reminder skipped bcs it's the first day
                evaluation.reminder_count = 1
                evaluation.last_reminder_date = current_date
                evaluation.save()
            elif (
                current_date.date() - evaluation.last_reminder_date.date()
            ).days >= 7 and evaluation.reminder_count < 5:  # 1 reminder per week during 4 weeks
                evaluation.last_reminder_date = current_date
                evaluation.reminder_count += 1
                evaluation.save()
                send_human_statistics(evaluation)
