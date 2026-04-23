import logging

from django.core.management import BaseCommand
from django.core.mail import EmailMessage
from django.utils import timezone
from django.conf import settings
from subscriptions.models import Subscription
from accounts.models import MixityUser

test_log = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.new_user_alert()
        self.subscription_soon_over_alert()

    def new_user_alert(self):
        one_day_ago = timezone.now() - timezone.timedelta(hours=24)  # TODO change
        new_users = MixityUser.objects.filter(date_joined__gte=one_day_ago)
        if not new_users.exists():
            return

        subject = f"[Mixity] : {new_users.count()} Nouveaux utilisateurs inscrits dans les 24 dernières heures"
        new_users = [
            f"{new_user.email} {new_user.first_name} {new_user.last_name} {new_user.date_joined.strftime('%d-%m-%Y %H:%M:%S')}"
            for new_user in new_users
        ]
        body = "\n".join(new_users)
        print(body)

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.MIXITY_EMAIL_FROM,
            to=["dev@griselle.io"],
        )
        email.send()

    def subscription_soon_over_alert(self):

        three_days_from_now = timezone.now() + timezone.timedelta(days=3)  # TODO change
        subscriptions_to_remind = Subscription.objects.filter(
            is_active=True,
            end_date__lte=three_days_from_now,
            end_date__gte=timezone.now(),
        )

        if not subscriptions_to_remind.exists():
            return

        subject = f"[Mixity] : {subscriptions_to_remind.count()} Comptes expirants dans moins de 3 jours"
        subscriptions_to_remind = [
            f"{subscription.user.email} {subscription.user.first_name} {subscription.user.last_name} {subscription.user.date_joined.strftime('%d-%m-%Y %H:%M:%S')}"
            for subscription in subscriptions_to_remind
        ]
        body = "\n".join(subscriptions_to_remind)
        print(body)

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.MIXITY_EMAIL_FROM,
            to=["dev@griselle.io"],
        )
        email.send()
