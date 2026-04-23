from django.db import models
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _


class Invoice(models.Model):
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
    )
    tax_free_price = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        default=0,
        verbose_name=_("Prix HT"),
    )
    tax_included_price = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        default=0,
        verbose_name=_("Prix TTC"),
    )
    tax = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        default=0,
        verbose_name=_("TVA"),
    )
    discount = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        default=0,
        verbose_name=_("Bon de réduction"),
    )
    subscriptionPack = models.ForeignKey(
        "subscriptions.SubscriptionPack",
        on_delete=models.PROTECT,
        verbose_name=_("Pack d'Abonnement"),
        null=True,
        blank=True,
    )

    paid = models.BooleanField(verbose_name=_("Facture payée"), default=False)
    paid_at = models.DateTimeField(_("Date de paiement"), null=True)

    class Meta:
        verbose_name = _("Facture")

    def __str__(self):
        return "{} HT ({})".format(
            self.tax_free_price,
            self.created_date.date(),
        )
