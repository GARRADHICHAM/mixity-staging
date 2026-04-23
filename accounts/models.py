import sys
from datetime import date
import datetime
from django.utils import timezone

import address
import uuid as uuid
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from multiselectfield import MultiSelectField
from address.models import AddressField, Country, _to_python
from address.admin import AddressAdmin
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models import JSONField
from django.templatetags.static import static
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Subquery, OuterRef, Min
from django.db.models.functions import RowNumber
from django.utils.text import slugify
from django.utils.translation import activate, get_language
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
from django_countries import countries
from django_countries.fields import CountryField
from simple_email_confirmation.models import SimpleEmailConfirmationUserMixin

from accounts.vocabularies import (
    CATEGORY_CHOICES,
    CURRENCY_CHOICES,
    EURO_CODE,
    LANGUAGE_CHOICES,
    TURNOVER_CHOICES,
    EVALUATION_STATUS,
)
from act.models import Solver
from mixity.validators import year_validator
from payments.models import CheckoutSession
from subscriptions.models import (
    SubscriptionPack,
    SubscriptionOption,
    Product,
    Subscription,
)
from django.urls import reverse

# Monkey patch Country model of Django-address
# Du to duplicate country in Country table
# https://github.com/furious-luke/django-address/issues/67
# Country Model -> https://github.com/furious-luke/django-address/blob/50b3033b84f9f9e0676f2e49b6db156356abfa59/address/models.py#L184


def save_country(self, *args, **kwargs):
    # Country name translated in French
    current_language = get_language()
    activate("fr")
    countries_dict = dict(countries)
    self.name = countries_dict[self.code]
    activate(current_language)
    # Once country name is translated, save it
    super(Country, self).save(self)


def country_str(self):
    # Country name translated in current language
    countries_dict = dict(countries)
    try:
        return "%s" % (countries_dict[self.code])
    except KeyError:
        return "%s" % (self.name)


def mixity_to_python(value):
    country_code = value.get("country_code", "")

    if country_code:
        # Country name translated in French
        current_language = get_language()
        activate("fr")
        countries_dict = dict(countries)
        value["country"] = countries_dict[country_code]
        activate(current_language)

    return _to_python(value)


Country.save = save_country
Country.__str__ = country_str
address.models._to_python = mixity_to_python
# End Monkey patch Country model of Django-address

# Monkey patch AddressAdmin of Django-address
# https://gitlab.com/dantooin_devs/mixity/-/issues/1349
AddressAdmin.search_fields = ("raw",)
# End of Monkey patch AddressAdmin of Django-address


def structure_booleans_default_value():
    return dict(lgbt_allowed=False, ethnicity_allowed=False)


class MixityUser(SimpleEmailConfirmationUserMixin, AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    email = models.EmailField(_("Adresse email"), unique=True)

    foto = models.ImageField(
        null=True,
        blank=True,
        upload_to="fotos/",
        verbose_name=_("Photo"),
    )

    GENDER_CHOICES = (
        ("F", _("Madame")),
        ("H", _("Monsieur")),
        ("N", _("Non-binaire")),
    )
    gender = models.CharField(
        null=True,
        blank=True,
        verbose_name=_("Civilité"),
        choices=GENDER_CHOICES,
        max_length=1,
    )
    first_name = models.CharField(_("first name"), max_length=30)
    last_name = models.CharField(
        _("last name"),
        max_length=150,
    )
    job = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_("Fonction"),
    )
    business_line = models.ForeignKey(
        "BusinessLine",
        related_name="users",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Secteur d'activité"),
    )
    phone = models.CharField(
        null=True,
        blank=True,
        max_length=22,
        verbose_name=_("Mobile"),
    )
    is_newsletter = models.BooleanField(
        default=False,
        verbose_name=_("Inscription à la newsletter"),
    )
    is_qualified = models.BooleanField(
        default=False,
        verbose_name=_("Abonné Qualifié"),
    )

    language = models.CharField(
        choices=LANGUAGE_CHOICES,
        default="fr",
        max_length=10,
        verbose_name=_("Langue"),
    )
    currency = models.CharField(
        choices=CURRENCY_CHOICES,
        default=EURO_CODE,
        max_length=3,
        verbose_name=_("Devise"),
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    last_segment_identify = models.DateTimeField(
        default=None,
        verbose_name=_("Dernière identification sur Segment"),
        null=True,
        blank=True,
    )

    # TODO delete if not used
    def allow_evaluation(self, subscriptionPack):
        if (
            subscriptionPack
            and subscriptionPack.structure
            and subscriptionPack.structure not in self.readonly_structures
            and subscriptionPack.is_active
        ):
            return True
        return False

    def get_rights(self, entity):
        membership = self.memberships.filter(
            Q(structure=entity.entity_level.structure)
        ).first()
        if membership:
            return membership
        membership = self.memberships.filter(Q(entity=entity)).first()
        if membership:
            return membership
        parent = entity.get_first_parent(self.id)
        membership = self.memberships.filter(
            Q(entity=parent) & Q(is_owner=True)
        ).first()
        if membership:
            return membership

    def test_func_rights(self, entity):
        parent = entity.get_first_parent(self.id)

        membership_exists = self.memberships.filter(
            Q(entity=entity)
            | Q(structure=entity.entity_level.structure)
            | (Q(entity=parent) & Q(is_owner=True) if parent else Q())
        ).exists()

        return membership_exists

    @property
    def owned_structures(self):
        return Structure.objects.filter(memberships__is_owner=True, members=self)

    @property
    def readonly_structures(self):
        return Structure.objects.filter(memberships__is_reader=True, members=self)

    @property
    def structures(self):
        return Structure.objects.filter(members=self)

    @property
    def entities(self):
        return Entity.objects.filter(members=self)

    @property
    def accessible_structures(self):
        filtered_structures = (
            Entity.objects.filter(
                Q(members=self) | Q(entity_level__structure__members=self)
            )
            .select_related("entity_level__structure")
            .distinct("entity_level__structure")
        )
        return filtered_structures

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.check_is_qualified()
        kwargs["force_insert"] = False
        super().save(*args, **kwargs)

    def __str__(self):
        if self.first_name and self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        return self.email

    qualified_fields = (
        "first_name",
        "last_name",
    )

    def check_is_qualified(self):
        for field in self.qualified_fields:
            if not getattr(self, field, None):
                self.is_qualified = False
                break
        else:
            self.is_qualified = True

    def get_foto_url(self):
        if not self.foto:
            return ""
        return self.foto.url


class Structure(models.Model):
    logo = models.ImageField(
        null=True,
        blank=True,
        upload_to="logos/",
        verbose_name=_("Logo (PNG avec fond transparent recommandé)"),
    )
    juridic_name = models.CharField(
        max_length=100,
        verbose_name=_("Dénomination sociale"),
    )
    commercial_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_("Libellé commercial"),
    )
    slug = models.SlugField(max_length=100, unique=True)
    siret = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Numéro SIRET"),
    )
    duns = models.CharField(
        max_length=9,
        unique=True,
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Numéro DUNS"),
    )
    num_tva_intracom = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        unique=True,
        default=None,
        verbose_name=_("Numéro de TVA intracommunautaire"),
    )
    description = models.TextField(
        max_length=800,  # CDC : max 600 caractères
        null=True,
        blank=True,
        verbose_name=_("Description de l'activité"),
    )
    human_description = models.TextField(
        max_length=1200,
        null=True,
        blank=True,
        verbose_name=_("Description Mixity Human"),
    )
    commitment = models.TextField(
        max_length=800,  # CDC : max 600 caractères
        null=True,
        blank=True,
        verbose_name=_("Témoignage diversité"),
    )
    workforce = models.PositiveIntegerField(verbose_name=_("Effectifs"), default=0)
    turnover_value = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Chiffre d'Affaires"),
    )
    turnover_currency = models.CharField(
        choices=CURRENCY_CHOICES,
        default=EURO_CODE,
        max_length=3,
        null=False,
        verbose_name=_("Devise du Chiffre d'Affaires"),
    )
    turnover_date = models.DateField(
        default=date.today, null=False, verbose_name=_("Date du Chiffre d'Affaires")
    )
    category = models.CharField(
        choices=CATEGORY_CHOICES,
        max_length=25,
        db_index=True,
        verbose_name=_("Catégorie"),
    )
    business_line = models.ForeignKey(
        "BusinessLine",
        related_name="structures",
        on_delete=models.PROTECT,
        verbose_name=_("Secteur d'activité"),
    )
    secondary_business_lines = models.ManyToManyField(
        "BusinessLine",
        related_name="secondary_structures",
        blank=True,
        verbose_name=_("Secteurs d'activité secondaire"),
    )
    creation_year = models.PositiveIntegerField(
        _("Année de création"), validators=[year_validator], null=True, blank=True
    )
    address = AddressField(
        verbose_name=_("Adresse"), blank=True, null=True, on_delete=models.SET_NULL
    )
    country = CountryField(verbose_name=_("Pays"), blank=True, null=True)
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Site Web"),
    )
    phone1 = models.CharField(
        null=True,
        blank=True,
        max_length=22,
        verbose_name=_("Téléphone fixe"),
    )
    phone2 = models.CharField(
        null=True,
        blank=True,
        max_length=22,
        verbose_name=_("Mobile"),
    )
    phone3 = models.CharField(
        null=True,
        blank=True,
        max_length=22,
        verbose_name="Téléphone3",
    )
    stripe_customer_id = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name="ID Client Stripe",
    )

    members = models.ManyToManyField(
        "accounts.MixityUser",
        blank=True,
        related_name="members",
        through="accounts.Membership",
        verbose_name=_("Employés"),
    )
    labels = models.ManyToManyField(
        "DiversityLabel",
        blank=True,
        verbose_name=_("Labels et certifications"),
    )

    display_on_website = models.BooleanField(
        default=True, verbose_name="Afficher le logo sur le site"
    )
    creation_structure_fields = (  # TODO: utilisation quelque part ?
        "logo",
        "juridic_name",
        "commercial_name",
        "address",
        "phone1",
        "phone2",
        "category",
        "workforce",
        "siret",
        "duns",
        "num_tva_intracom",
        "creation_year",
        "turnover_value",
        "business_line",
        "website",
        "description",
    )
    booleans = JSONField(
        verbose_name="Booléens",
        default=structure_booleans_default_value,
    )
    tags = models.ManyToManyField(
        "scoring.QuestionTag",
        blank=True,
        related_name="structures",
        verbose_name="Tags",
    )
    is_partial = models.BooleanField(
        default=False,
        verbose_name=_("A le profil partiellement complété ?"),
    )
    # Structure customer favorite solutions list
    favorite_solutions = models.ManyToManyField(
        to="act.Solution",
        blank=True,
        related_name="structures",
        verbose_name="Solutions favoris",
    )
    adp_software = models.ForeignKey(
        "sirh.ADPSoftware", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Structure")

    def __str__(self):
        return "{}".format(self.commercial_name or self.juridic_name)

    @cached_property
    def get_solver(self):
        try:
            return self.solver
        except:
            return None

    @cached_property
    def is_solver(self):
        return self.get_solver is not None

    @cached_property
    def is_campus(self):
        return self.tags.filter(name="campus").exists()

    def save(self, **kwargs):
        slug_name = slugify(self.juridic_name) + "-structure"
        tmp_slug_name = slug_name
        i = 1
        while Structure.objects.filter(slug=tmp_slug_name).exclude(pk=self.pk).exists():
            tmp_slug_name = f"{slug_name}-{i}"
            i += 1
        self.slug = tmp_slug_name

        if self.siret == "":
            self.siret = None

        if self.num_tva_intracom == "":
            self.num_tva_intracom = None

        if self.duns == "":
            self.duns = None

        super().save(**kwargs)

    def create_subscriptionPack(self):
        if not SubscriptionPack.active_objects.filter(
            structure=self, is_active=True
        ).exists():
            new_subscription_pack = SubscriptionPack.objects.create(
                is_active=True,
                start_date=now(),
                end_date=now() + relativedelta(years=1),
                structure=self,
            )
            new_subscription_pack.save()
            return new_subscription_pack
        else:
            existing_subscription_pack = SubscriptionPack.active_objects.get(
                structure=self, is_active=True
            )
            return existing_subscription_pack

    def get_mail_display(self):
        return self.owners.first().email

    def get_boolean(self, key):
        if key in self.booleans:
            return self.booleans[key]
        return False

    def get_website_display(self):
        if not self.website:
            return ""
        return self.website.replace("https://", "").replace("http://", "")

    def get_phone_display(self):
        if not (self.phone1 or self.phone2 or self.phone3):
            return "Non renseigné"
        return next(phone for phone in [self.phone1, self.phone2, self.phone3] if phone)

    def get_business_line_display(self):
        if not self.business_line:
            return ""
        return self.business_line.name

    def get_logo_url(self):
        if not self.logo:
            return static("img/structure.svg")
        return self.logo.url

    def has_logo(self):
        return bool(self.logo)

    @property
    def get_first_owner(self):
        return self.owners.first()

    @property
    def owners(self):
        return MixityUser.objects.filter(memberships__is_owner=True, members=self)

    @property
    def readers(self):
        return MixityUser.objects.filter(memberships__is_reader=True, members=self)

    @property
    def active_subscription_pack(self):
        return (
            SubscriptionPack.active_objects.filter(structure=self)
            .order_by("-start_date")
            .first()
        )

    @property
    def active_human_subscription(self):
        # Utilisé pour les migrations
        return (
            SubscriptionOption.active_objects.filter(
                subscriptionPack__structure=self, product__slug="human"
            )
            .order_by("-start_date")
            .first()
        )

    @property
    def active_global_subscription(self):
        # Utilisé pour les migrations
        return (
            SubscriptionOption.active_objects.filter(subscriptionPack__structure=self)
            .exclude(product__slug="human")
            .order_by("-start_date")
            .first()
        )

    @cached_property
    def active_diag_product(self):
        return (
            SubscriptionOption.objects.filter(
                subscriptionPack__structure=self,
                product__slug="diag",
                end_date__gte=now().date(),
            )
            .order_by("-start_date")
            .first()
        )

    @cached_property
    def has_active_diag(self):
        return (
            SubscriptionOption.active_objects.filter(
                subscriptionPack__structure=self, product__slug="diag"
            ).count()
            > 0
        )

    @cached_property
    def active_human_product(self):
        return (
            SubscriptionOption.objects.filter(
                subscriptionPack__structure=self,
                product__slug="human",
                end_date__gte=now().date(),
            )
            .order_by("-start_date")
            .first()
        )

    @cached_property
    def has_active_human(self):
        return (
            SubscriptionOption.active_objects.filter(
                subscriptionPack__structure=self, product__slug="human"
            ).count()
            > 0
        )

    @cached_property
    def active_scan_product(self):
        return (
            SubscriptionOption.active_objects.filter(
                subscriptionPack__structure=self, product__slug="scan"
            )
            .order_by("-start_date")
            .first()
        )

    @cached_property
    def has_active_scan(self):
        return (
            SubscriptionOption.active_objects.filter(
                subscriptionPack__structure=self, product__slug="scan"
            ).count()
            > 0
        )

    @property
    def first_subscriptionOption(self):
        return SubscriptionOption.objects.filter(
            subscriptionPack__structure=self
        ).first()

    @property
    def can_pay_by_card(self):
        option = self.first_subscriptionOption
        return (
            option
            and option.tags.filter(name="mixity_start").exists()
            and not option.tags.filter(name="trial").exists()
            and not self.is_awaiting_payment
        )

    @property
    def is_awaiting_payment(self):
        s = self.first_subscriptionOption
        c = CheckoutSession.objects.filter(subscriptionOption=s).first()
        return c and c.payment_status == "unpaid"

    @property
    def last_payment_failed(self):
        s = self.first_subscriptionOption
        c = CheckoutSession.objects.filter(subscriptionOption=s).first()
        return c and c.payment_status == "unpaid_failed"

    @property
    def active_subscriptionOptions(self):
        return SubscriptionOption.active_objects.filter(
            subscriptionPack__structure=self
        )

    @property
    def inactive_subscriptionOptions(self):
        return SubscriptionOption.objects.filter(
            is_active=False, subscriptionPack__structure=self
        )

    @property
    def has_public_page(self):
        subscriptionOptions = self.active_subscriptionOptions
        return subscriptionOptions.count() > 0

    @property
    def display_name(self):
        return self.commercial_name or self.juridic_name

    @cached_property
    def get_main_entity(self):
        return self.entity_level.get(level=0).entities.first()


class EntityLevel(models.Model):
    label = models.CharField(
        max_length=120,
        verbose_name=_("Label"),
    )
    structure = models.ForeignKey(
        Structure, on_delete=models.CASCADE, related_name="entity_level"
    )
    level = models.PositiveIntegerField(verbose_name=_("Niveau d'entité"))

    def __str__(self):
        return "Niveau {}".format(self.level)

    class Meta:
        verbose_name = _("Niveau d'entité")
        verbose_name_plural = _("Niveaux d'entité")
        ordering = ("structure", "level")


class Entity(models.Model):
    name = models.CharField(
        max_length=120,
        verbose_name=_("Dénomination sociale"),
    )
    slug = models.SlugField(max_length=100, unique=True)
    entity_level = models.ForeignKey(
        EntityLevel,
        on_delete=models.CASCADE,
        related_name="entities",
        verbose_name=_("Niveau d'entité"),
    )
    parent_entity = models.ForeignKey(
        "accounts.Entity",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children_entities",
        verbose_name=_("Entité parente"),
    )
    creation_year = models.PositiveIntegerField(
        _("Année de création"), validators=[year_validator], null=True, blank=True
    )
    workforce = models.PositiveIntegerField(verbose_name=_("Effectifs"), default=0)
    address = AddressField(
        verbose_name=_("Adresse"), blank=True, null=True, on_delete=models.SET_NULL
    )
    country = CountryField(verbose_name=_("Pays"), blank=True, null=True)
    phone = models.CharField(
        null=True,
        blank=True,
        max_length=22,
        verbose_name=_("Téléphone"),
    )
    members = models.ManyToManyField(
        "accounts.MixityUser",
        blank=True,
        related_name="entity_members",
        through="accounts.Membership",
        verbose_name=_("Employés"),
    )
    # Structure customer favorite solutions list
    favorite_solutions = models.ManyToManyField(
        to="act.Solution",
        blank=True,
        related_name="entities",
        verbose_name="Solutions favorites",
    )
    favorite_best_practices = models.ManyToManyField(
        to="act.BestPractice",
        blank=True,
        related_name="entities",
        verbose_name="Bonnes pratiques favorites",
    )
    # A voir si ça reste dans Structure aussi ou non
    tags = models.ManyToManyField(
        "scoring.QuestionTag",
        blank=True,
        related_name="entities",
        verbose_name="Tags",
    )

    adp_software = models.ForeignKey(
        "sirh.ADPSoftware", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Entité")
        ordering = ("entity_level",)

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        slug_name = slugify(self.name)
        tmp_slug_name = slug_name
        i = 1
        while True:
            try:
                Entity.objects.exclude(pk=self.pk).get(slug=tmp_slug_name)
                tmp_slug_name = f"{slug_name}-{i}"
                i += 1
            except Entity.DoesNotExist:
                break
        self.slug = tmp_slug_name

        super().save(**kwargs)

    @property
    def get_first_owner(self):
        return self.owners.first()

    def get_first_parent(self, user_id):
        i = self.entity_level.level
        filters = Q(**{"pk": self.pk})
        while i != 0:
            filters |= Q(**{"__".join(i * ["children_entities"]): self})
            i -= 1
        parent = (
            Entity.objects.filter(
                filters,
                members=user_id,
            )
            .exclude(pk=self.pk)
            .order_by("entity_level")
            .first()
        )
        if parent:
            return parent

    # Used for lead, we get every entities upper and under the current entity
    @cached_property
    def get_own_entire_tree(self):
        i = self.entity_level.level
        filters = Q(**{"pk": self.pk})
        while i != 0:
            filters |= Q(**{"__".join(i * ["children_entities"]): self})
            i -= 1
        max_level = self.entity_level.structure.entity_level.count() - 1
        for i in range(max_level - self.entity_level.level, 0, -1):
            filters |= Q(**{"__".join(i * ["parent_entity"]): self})
        return (
            Entity.objects.filter(filters)
            .prefetch_related("children_entities")
            .distinct()
        )

    @cached_property
    def get_all_children_entities(self):
        max_level = self.entity_level.structure.entity_level.count()
        filters = Q(**{"pk": self.pk})
        for i in range(1, max_level):
            filters |= Q(**{"__".join(i * ["parent_entity"]): self})
        children_entities = (
            Entity.objects.filter(filters)
            .select_related("parent_entity__entity_level", "entity_level")
            .prefetch_related("children_entities")
        )
        return children_entities

    @property
    def last_public_evaluation(self):
        return self.evaluations.filter(public_display=True).last()

    @property
    def last_private_evaluation(self):
        return self.evaluations.filter(private_display=True).last()

    @cached_property
    def last_human_evaluation(self):
        try:
            if self.evaluations.filter(
                sheet__type__slug="evaluation_collaborateurs_360",
                display_version="en-cours",
            ).exists():
                return self.evaluations.get(
                    sheet__type__slug="evaluation_collaborateurs_360",
                    display_version="en-cours",
                )
            return (
                self.evaluations.filter(
                    sheet__type__slug="evaluation_collaborateurs_360"
                )
                .order_by("-version")
                .first()
            )
        except Exception as e:
            print(e)
            return None

    @cached_property
    def last_scan_evaluation(self):
        try:
            if self.evaluations.filter(
                sheet__type__slug="mixity_evaluation_scan",
                display_version="en-cours",
            ).exists():
                return self.evaluations.get(
                    sheet__type__slug="mixity_evaluation_scan",
                    display_version="en-cours",
                )
            return (
                self.evaluations.filter(sheet__type__slug="mixity_evaluation_scan")
                .order_by("-version")
                .first()
            )
        except Exception as e:
            print(e)
            return None

    @cached_property
    def en_cours_global_evaluation(self):
        try:
            if (
                self.evaluations.filter(display_version="en-cours")
                .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .exists()
            ):
                return (
                    self.evaluations.filter(display_version="en-cours")
                    .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                    .exclude(sheet__type__slug="mixity_evaluation_scan")
                    .first()
                )
            return None
        except Exception as e:
            print(e)
            return None

    @cached_property
    def en_cours_human_evaluation(self):
        try:
            if self.evaluations.filter(
                display_version="en-cours",
                sheet__type__slug="evaluation_collaborateurs_360",
            ).exists():
                return self.evaluations.filter(
                    display_version="en-cours",
                    sheet__type__slug="evaluation_collaborateurs_360",
                ).first()
            return None
        except Exception as e:
            print(e)
            return None

    @cached_property
    def last_global_evaluation(self):
        try:
            if (
                self.evaluations.filter(display_version="en-cours")
                .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .exists()
            ):
                return (
                    self.evaluations.filter(display_version="en-cours")
                    .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                    .exclude(sheet__type__slug="mixity_evaluation_scan")
                    .first()
                )
            return (
                self.evaluations.exclude(
                    sheet__type__slug="evaluation_collaborateurs_360"
                )
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .order_by("-version")
                .first()
            )
        except Exception as e:
            print(e)
            return None

    @cached_property
    def last_validated_by_user_global_evaluation(self):
        return (
            self.evaluations.filter(is_validated_by_user=True)
            .exclude(version=None, sheet__type__slug="evaluation_collaborateurs_360")
            .exclude(sheet__type__slug="mixity_evaluation_scan")
            .order_by("-version")
            .first()
        )

    @cached_property
    def last_validated_by_user_human_evaluation(self):
        return (
            self.evaluations.filter(
                sheet__type__slug="evaluation_collaborateurs_360",
                is_validated_by_user=True,
            )
            .exclude(version=None)
            .order_by("-version")
            .first()
        )

    @cached_property
    def last_validated_by_user_scan_evaluation(self):
        return (
            self.evaluations.filter(
                sheet__type__slug="mixity_evaluation_scan",
                is_validated_by_user=True,
            )
            .exclude(version=None)
            .order_by("-version")
            .first()
        )

    @cached_property
    def last_validated_by_admin_global_evaluation(self):
        return (
            self.evaluations.exclude(
                sheet__type__slug="evaluation_collaborateurs_360",
            )
            .exclude(sheet__type__slug="mixity_evaluation_scan")
            .filter(is_validated_by_admin=True)
            .order_by("-version")
            .first()
        )

    @cached_property
    def last_validated_by_admin_human_evaluation(self):
        return (
            self.evaluations.filter(
                sheet__type__slug="evaluation_collaborateurs_360",
                is_validated_by_admin=True,
            )
            .exclude(version=None)
            .order_by("-version")
            .first()
        )

    @cached_property
    def last_validated_by_admin_scan_evaluation(self):
        return (
            self.evaluations.filter(
                sheet__type__slug="mixity_evaluation_scan",
                is_validated_by_admin=True,
            )
            .exclude(version=None)
            .order_by("-version")
            .first()
        )

    @cached_property
    def get_global_status(self):
        return self._get_status("diag")

    @cached_property
    def get_human_status(self):
        return self._get_status("human")

    @cached_property
    def get_scan_status(self):
        return self._get_status("scan")

    def _get_status(self, product_slug):
        if product_slug == "diag":
            evaluations = (
                self.evaluations.exclude(
                    sheet__type__slug="evaluation_collaborateurs_360"
                )
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .order_by("-created_date")
            )
        elif product_slug == "human":
            evaluations = self.evaluations.filter(
                sheet__type__slug="evaluation_collaborateurs_360"
            ).order_by("-created_date")

        else:
            evaluations = self.evaluations.filter(
                sheet__type__slug="mixity_evaluation_scan"
            ).order_by("-created_date")

        # On s'assure qu'au moins une évaluation existe
        if not evaluations.exists():
            return EVALUATION_STATUS[0]

        # On récupère l'évaluation la plus récente sans version ou la plus ancienne
        evaluation = (
            evaluations.filter(version__isnull=True).first() or evaluations.first()
        )

        # Détermine le statut de l'évaluation
        if not evaluation.is_started:
            return EVALUATION_STATUS[0]
        elif not evaluation.is_validated_by_user:
            return EVALUATION_STATUS[1]
        elif not evaluation.is_validated_by_admin:
            return EVALUATION_STATUS[2]
        else:
            return EVALUATION_STATUS[3]

    @property
    def owners(self):
        return MixityUser.objects.filter(
            memberships__is_owner=True, entity_members=self
        )

    @property
    def readers(self):
        return MixityUser.objects.filter(
            memberships__is_reader=True, entity_members=self
        )


class Membership(models.Model):
    user = models.ForeignKey(
        "accounts.MixityUser", on_delete=models.CASCADE, related_name="memberships"
    )
    structure = models.ForeignKey(
        "accounts.Structure",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    entity = models.ForeignKey(
        "accounts.Entity",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    date_joined = models.DateField(auto_now_add=True)
    is_owner = models.BooleanField(default=False)
    is_reader = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "structure")
        verbose_name = _("Appartenance")


def upload_location(instance, filename):
    base_path = "img/certifications/"
    file_name, extension = filename.split(".")
    return base_path + slugify(instance.name)[:60] + "." + extension


class DiversityLabel(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name=_("Nom"),
    )
    image = models.ImageField(upload_to=upload_location, blank=True)

    class Meta:
        verbose_name = _("Label de diversité")
        verbose_name_plural = _("Labels de diversité")
        ordering = ("name",)

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        if self.image and hasattr(self.image, "url"):
            return self.image.url


class BusinessLine(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name=_("Nom"),
    )
    slug = models.SlugField(max_length=256, unique=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class HumanCriteria(models.Model):
    label = models.CharField(max_length=128, verbose_name=_("Label"))
    order = models.IntegerField(verbose_name="Ordering priority", default=0)
    evaluation = models.ForeignKey(
        "scoring.Evaluation", on_delete=models.CASCADE, related_name="human_criteria"
    )

    is_csv_imported = models.BooleanField(
        default=False,
        verbose_name=_("Provient d'un fichier CSV"),
    )

    mandatory_tags = models.ManyToManyField(
        "scoring.QuestionTag",
        blank=True,
        related_name="mandatory_human_criterias",
        help_text="Tags needed to display this criteria",
    )

    forbidden_tags = models.ManyToManyField(
        "scoring.QuestionTag",
        blank=True,
        related_name="forbidden_human_criterias",
        help_text="Tags forbidden to display this criteria",
    )

    allow_multiple = models.BooleanField(
        default=False,
        verbose_name=_("Autoriser les choix multiples"),
    )

    class Meta:
        ordering = ("order", "pk")

    def __str__(self):
        return self.label


class HumanCriteriaChoice(models.Model):
    label = models.CharField(max_length=128, verbose_name=_("Label"))
    criteria = models.ForeignKey(
        "accounts.HumanCriteria",
        on_delete=models.CASCADE,
        related_name="choices",
        null=True,
    )

    order = models.IntegerField(verbose_name="Ordering priority", default=0)

    tags = models.ManyToManyField(
        "scoring.QuestionTag",
        blank=True,
        related_name="human_criteria_choices",
        help_text="Tags affected if this criteria choice is selected",
    )

    mandatory_questions = models.ManyToManyField(
        "scoring.Question",
        blank=True,
        related_name="mandatory_human_criteria_choices",
        help_text="Custom questions to display if this criteria choice is selected",
    )

    forbidden_questions = models.ManyToManyField(
        "scoring.Question",
        blank=True,
        related_name="forbidden_human_criteria_choices",
        help_text="Custom questions to hide if this criteria choice is selected",
    )

    def __str__(self):
        return self.label
