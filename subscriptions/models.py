import datetime
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from invoices.models import Invoice


class SubscriptionType(models.Model):
    label = models.CharField(
        max_length=100,
        verbose_name="Intitulé",
    )
    pme_label = models.CharField(
        max_length=100,
        verbose_name="Intitulé pour les PME",
    )
    slug = models.SlugField(unique=True, verbose_name="Slug")
    order = models.IntegerField(default=0)
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
    )
    allow_structure_evaluation = models.BooleanField(
        default=False,
        verbose_name="Permet l'évaluation de la Structure par les adminsitrateurs",
    )
    allow_collaborator_evaluation = models.BooleanField(
        default=False,
        verbose_name="Permet l'évaluation de la Structure par des collaborateurs",
    )
    allow_public_display = models.BooleanField(
        default=False,
        verbose_name="Permet de rendre publique la Structure",
    )
    allow_add_structure_members = models.BooleanField(
        default=False,
        verbose_name="Permet d'ajouter des Abonnés de la même Structure",
    )
    allow_evaluation_opinions = models.BooleanField(
        default=False,
        verbose_name="Permet d'émettre des Avis sur les évaluations",
    )
    allow_opinion_activation = models.BooleanField(
        default=False,
        verbose_name="Permet d'activer les Avis",
    )
    allow_advanced_search = models.BooleanField(
        default=False, verbose_name="Permet la recherche avancée"
    )
    search_criteria_number = models.IntegerField(
        default=1,
        verbose_name="Nombre de critères de recherche permis",
    )
    allow_kitcom_purchasing = models.BooleanField(
        default=False,
        verbose_name="Permet d'acheter des KIT de Communication",
    )
    allow_card_payment = models.BooleanField(
        default=False,
        verbose_name="Permet de payer l'abonnement par carte",
    )
    duration = models.DurationField(
        default=timezone.timedelta(days=360), verbose_name="Durée de l'abonnement"
    )
    question_sheet_types = models.ManyToManyField(
        "scoring.QuestionSheetType",
        verbose_name="Type de questionnaire autorisés",
        related_name="subscription_types",
        blank=True,
    )
    display_on_offer_page = models.BooleanField(
        default=True, verbose_name="Affiche l'offre sur les pages publiques"
    )

    class Meta:
        verbose_name = "Type d'abonnement"
        verbose_name_plural = "Types d'abonnement"
        ordering = ("order",)

    def __str__(self):
        return "{}".format(
            self.label,
        )

    @property
    def get_pme_tax_free_price(self):
        price = self.prices.exclude(workforce_limit=None).first()
        return price.tax_free_price

    @property
    def get_eti_tax_free_price(self):
        price = self.prices.filter(
            workforce_limit__gte=500
        ).first()  # TODO 500 not hard coded

        return price.tax_free_price

    @property
    def get_max_size_tax_free_price(self):
        price = self.prices.filter(workforce_limit=None).first()
        return price.tax_free_price

    def get_tax_free_price(self, workforce):
        price = self.prices.filter(
            Q(workforce_limit__gte=workforce) | Q(workforce_limit__isnull=True)
        ).first()

        # In case of no price set without workforce for the last range of price,
        # take last with workforce
        if not price:
            price = self.prices.last()

        return price.tax_free_price


class ActiveObjectsManager(models.Manager):
    def get_queryset(self):
        today = datetime.date.today()
        return (
            super()
            .get_queryset()
            .filter(
                is_active=True,
                subscription_type__is_active=True,
                start_date__lte=today,
            )
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
            .order_by("-start_date")
        )


class NewActiveObjectsManager(models.Manager):
    # utilisé pour product, subscriptionOption et subscriptionPack
    def get_queryset(self):
        today = datetime.date.today()
        return (
            super()
            .get_queryset()
            .filter(
                is_active=True,
                start_date__lte=today,
            )
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
            .order_by("-start_date")
        )


class Subscription(models.Model):
    is_active = models.BooleanField(
        default=False,
        verbose_name=_("Actif"),
    )
    start_date = models.DateField(
        verbose_name=_("Date de début"),
    )
    end_date = models.DateField(
        verbose_name=_("Date de fin"),
        null=True,
        blank=True,
    )
    structure = models.ForeignKey(
        "accounts.Structure",
        models.CASCADE,
        related_name="subscriptions",
        verbose_name=_("Structure Abonnée"),
    )
    subscription_type = models.ForeignKey(
        SubscriptionType,
        models.PROTECT,
        related_name="subscriptions",
        verbose_name=_("Types d'abonnement"),
    )
    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="subscription",
        verbose_name=_("Facture"),
    )
    question_sheet_type = models.ForeignKey(
        "scoring.QuestionSheetType",
        verbose_name=_("Type de questionnaire"),
        related_name="subscriptions",
        blank=True,
        null=True,  # TODO remove
        on_delete=models.PROTECT,
    )

    tags = models.ManyToManyField(
        "scoring.QuestionTag",
        blank=True,
        related_name="subscriptions",
        verbose_name="Tags",
    )

    objects = models.Manager()
    active_objects = ActiveObjectsManager()

    # first version quick and dirty for coupon
    coupon = models.ForeignKey(
        "subscriptions.Coupon",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    class Meta:
        verbose_name = _("Abonnement")
        ordering = ("-start_date",)

    @cached_property
    def is_trial(self):
        return self.tags.exists()

    def __str__(self):
        return "{} pour {} (Date de début: {} - Date de fin: {})".format(
            self.subscription_type or "",
            self.structure or "",
            self.start_date,
            self.end_date,
        )


class Coupon(models.Model):
    code = models.CharField(max_length=32, unique=True, db_index=True)
    quantity = models.PositiveIntegerField()
    used = models.PositiveIntegerField()

    @cached_property
    @admin.display(boolean=True)
    def is_valid(self):
        return self.subscriptions.count() < self.quantity

    def __str__(self):
        return self.code


class Product(models.Model):
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
    )
    label = models.CharField(
        max_length=100,
        verbose_name=_("Intitulé"),
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=_("Slug"),
    )
    question_sheet_type = models.OneToOneField(
        "scoring.QuestionSheetType",
        verbose_name=_("Questionnaire"),
        related_name="questionary",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    objects = models.Manager()
    active_objects = NewActiveObjectsManager()

    search_criteria_number = models.IntegerField(
        default=1,
        verbose_name="Nombre de critères de recherche permis",
    )

    def __str__(self):
        return "{}".format(
            self.label,
        )


class SubscriptionOption(models.Model):
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
    )
    start_date = models.DateField(
        verbose_name=_("Date de début"),
    )
    end_date = models.DateField(
        verbose_name=_("Date de fin"),
        null=True,
        blank=True,
    )
    subscriptionPack = models.ForeignKey(
        "subscriptions.SubscriptionPack",
        on_delete=models.PROTECT,
        related_name="options",
        verbose_name=_("Pack d'Abonnement"),
    )
    product = models.ForeignKey(
        "subscriptions.Product",
        on_delete=models.PROTECT,
        related_name="option",
        verbose_name=_("Liste des produits"),
    )
    tags = models.ManyToManyField(
        "scoring.QuestionTag",
        blank=True,
        related_name="subscriptionPacks",
        verbose_name="Tags",
    )
    objects = models.Manager()
    active_objects = NewActiveObjectsManager()

    @property
    def stripe_price_id(self):
        if self.subscriptionPack.structure.workforce < 50:
            return settings.STRIPE_PRICE_ID_UNDER_50
        else:
            return settings.STRIPE_PRICE_ID_OVER_50

    @property
    def is_current(self):
        if self.end_date:
            return self.start_date <= now().date() <= self.end_date and self.is_active
        else:
            return self.start_date <= now().date() and self.is_active

    @cached_property
    def is_trial(self):
        return self.tags.filter(name="trial").exists()


class SubscriptionPack(models.Model):
    is_active = models.BooleanField(
        default=False,
        verbose_name=_("Actif"),
    )
    start_date = models.DateField(
        verbose_name=_("Date de début"),
    )
    end_date = models.DateField(
        verbose_name=_("Date de fin"),
        null=True,
        blank=True,
    )
    structure = models.ForeignKey(
        "accounts.Structure",
        models.CASCADE,
        related_name="subscription_pack",
        verbose_name=_("Pack"),
    )
    objects = models.Manager()
    active_objects = NewActiveObjectsManager()

    @property
    def is_current(self):
        if self.end_date:
            return (
                self.start_date <= datetime.date.today() <= self.end_date
                and self.is_active
            )
        else:
            return self.start_date <= datetime.date.today() and self.is_active

    def add_new_option(self, product):
        if not SubscriptionOption.objects.filter(
            end_date__gte=now(),
            product__slug=product,
            subscriptionPack__structure=self.structure,
        ).exists():
            new_option = SubscriptionOption.objects.create(
                is_active=False,
                start_date=now(),
                end_date=now() + relativedelta(years=1),
                subscriptionPack=self,
                product=Product.objects.get(slug=product),
            )
            return new_option

    @property
    def subscriptionOptions(self):
        return SubscriptionOption.objects.filter(subscriptionPack=self)

    @property
    def lastsubscriptionOption(self):
        return (
            SubscriptionOption.objects.filter(subscriptionPack=self)
            .order_by("-start_date")
            .first()
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    class Meta:
        unique_together = ("structure", "start_date", "end_date")
