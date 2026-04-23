from django.db import models
from django.utils.translation import ugettext_lazy as _

from scoring.models import (
    Category,
    SubCategory,
)
from accounts.models import Structure, Entity
from accounts.vocabularies import ACTION_STATUS, UNIT_CHOICE


class Objective(models.Model):
    label = models.CharField(
        max_length=512,
        verbose_name=_("Titre"),
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_("Catégorie"),
        on_delete=models.PROTECT,
        related_name="objectives",
    )
    subcategory = models.ForeignKey(
        SubCategory,
        verbose_name=_("Sous-catégorie"),
        on_delete=models.PROTECT,
        related_name="objectives",
    )
    structure = models.ForeignKey(
        Structure,
        verbose_name=_("Structure"),
        on_delete=models.CASCADE,
        related_name="objectives",
    )
    entity = models.ForeignKey(
        Entity,
        verbose_name=_("Entité"),
        on_delete=models.CASCADE,
        related_name="objectives",
        null=True,
    )
    creation_date = models.DateField(
        verbose_name=_("Date de création"),
        auto_now_add=True,
        null=True,
    )
    creation_user = models.ForeignKey(
        "accounts.MixityUser",
        on_delete=models.SET_NULL,
        related_name="objectives_creator",
        null=True,
    )
    last_modification_date = models.DateField(
        verbose_name=_("Date de modification"),
        auto_now=True,
    )
    last_modification_user = models.ForeignKey(
        "accounts.MixityUser",
        on_delete=models.SET_NULL,
        related_name="objectives_modifier",
        null=True,
    )
    height = models.CharField(
        max_length=125,
        verbose_name=_("Height"),
    )

    class Meta:
        verbose_name = _("Objectif")

    def __str__(self):
        return self.label

    @property
    def progress_bar(self):
        actions_count = self.actions.exclude(status="reflection").count()
        if actions_count:
            return int(
                self.actions.filter(status="deployed").count() / actions_count * 100
            )
        return 0

    @property
    def total_budget(self):
        budget = self.actions.all().aggregate(models.Sum("budget"))["budget__sum"]
        if budget:
            return budget
        return 0


class LeadAction(models.Model):
    label = models.CharField(
        max_length=512,
        verbose_name=_("Titre"),
    )
    status = models.CharField(
        max_length=125,
        choices=ACTION_STATUS,
        verbose_name=_("Status"),
    )
    creation_date = models.DateField(
        verbose_name=_("Date de création"),
        auto_now_add=True,
    )
    creation_user = models.ForeignKey(
        "accounts.MixityUser",
        on_delete=models.SET_NULL,
        related_name="actions_creator",
        null=True,
    )
    creation_entity = models.ForeignKey(
        "accounts.Entity",
        on_delete=models.SET_NULL,
        related_name="entity_actions",
        null=True,
    )
    last_modification_date = models.DateField(
        verbose_name=_("Date de modification"),
        auto_now=True,
    )
    last_modification_user = models.ForeignKey(
        "accounts.MixityUser",
        on_delete=models.SET_NULL,
        related_name="actions_modifier",
        null=True,
    )
    action_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date prévue de l'action"),
    )
    budget = models.IntegerField(null=True, blank=True)
    referent = models.ForeignKey(
        "accounts.MixityUser",
        on_delete=models.SET_NULL,
        related_name="actions",
        blank=True,
        null=True,
    )
    comment = models.TextField(
        verbose_name=_("Commentaire"),
        blank=True,
        null=True,
    )
    objective = models.ForeignKey(
        "Objective",
        verbose_name=_("Objectif"),
        on_delete=models.CASCADE,
        related_name="actions",
    )
    height = models.CharField(
        max_length=125,
        verbose_name=_("Height"),
    )

    class Meta:
        verbose_name = _("Action")

    def __str__(self):
        return self.label


class ActionKpi(models.Model):
    label = models.CharField(
        max_length=125,
        verbose_name=_("Titre"),
        null=True,
        blank=True,
    )
    generic_kpi = models.ForeignKey(
        "GenericKpi",
        verbose_name=_("Kpi générique"),
        on_delete=models.PROTECT,
        related_name="action_kpis",
        null=True,
        blank=True,
    )
    unit = models.CharField(
        max_length=125,
        choices=UNIT_CHOICE,
        verbose_name=_("Unité"),
        null=True,
        blank=True,
    )
    creation_date = models.DateField(
        verbose_name=_("Date de création"),
        auto_now_add=True,
    )
    creation_user = models.ForeignKey(
        "accounts.MixityUser",
        on_delete=models.SET_NULL,
        related_name="kpis_creator",
        null=True,
    )
    creation_entity = models.ForeignKey(
        "accounts.Entity",
        on_delete=models.SET_NULL,
        related_name="entity_kpis",
        null=True,
    )
    last_modification_date = models.DateField(
        verbose_name=_("Date de modification"),
        auto_now=True,
    )
    last_modification_user = models.ForeignKey(
        "accounts.MixityUser",
        on_delete=models.SET_NULL,
        related_name="kpis_modifier",
        null=True,
    )
    trackers = models.ManyToManyField(
        "accounts.MixityUser",
        related_name="kpis_tracked",
    )
    value = models.IntegerField(
        default=0, null=True, blank=True, verbose_name=_("Valeur")
    )
    goal = models.IntegerField(default=0, verbose_name=_("Valeur souhaitée"))
    subcategory = models.ForeignKey(
        SubCategory,
        verbose_name=_("Sous-catégorie"),
        on_delete=models.PROTECT,
        related_name="action_kpis",
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_("Catégorie"),
        on_delete=models.PROTECT,
        related_name="action_kpis",
        blank=True,
        null=True,
    )
    action = models.ForeignKey(
        "LeadAction",
        verbose_name=_("Action"),
        on_delete=models.CASCADE,
        related_name="kpis",
    )

    class Meta:
        verbose_name = _("ActionKpi")

    def __str__(self):
        if not self.label:
            return self.generic_kpi.label
        return self.label


class GenericKpi(models.Model):
    label = models.CharField(
        max_length=125,
        verbose_name=_("Titre"),
    )
    unit = models.CharField(
        max_length=125,
        choices=UNIT_CHOICE,
        verbose_name=_("Unité"),
    )
    creation_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
    )
    subcategories = models.ManyToManyField(
        SubCategory,
        verbose_name=_("Sous-catégories"),
        related_name="generic_kpis",
    )
    categories = models.ManyToManyField(
        Category,
        verbose_name=_("catégories"),
        related_name="generic_kpis",
    )
    help_text = models.TextField(
        verbose_name=_("Texte d'aide"),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("GenericKpi")

    def __str__(self):
        return self.label
