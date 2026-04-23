import datetime

from django.db import models


# Create your models here.
from django.utils import timezone


class CheckoutSession(models.Model):
    checkout_id = models.CharField(
        verbose_name="Stripe Checkout Session ID", max_length=256
    )
    expires_at = models.DateTimeField(verbose_name="Expiration de la session")
    subscription = models.OneToOneField(
        "subscriptions.Subscription",
        models.CASCADE,
        verbose_name="Abonnement",
        null=True,
    )
    subscriptionOption = models.OneToOneField(
        "subscriptions.SubscriptionOption",
        models.CASCADE,
        verbose_name="option",
        null=True,
    )
    payment_intent = models.CharField(
        verbose_name="Stripe Payment Intent", max_length=256
    )
    payment_status = models.CharField(verbose_name="payment_status", max_length=256)

    class Meta:
        verbose_name = "Stripe Checkout Session"
        ordering = ("-expires_at",)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at
