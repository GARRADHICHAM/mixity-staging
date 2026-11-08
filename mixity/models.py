from functools import cached_property

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured

from accounts.vocabularies import LANGUAGE_CHOICES
from mixity.settings.base import ENABLED_WEBSITE_LANGUAGES, LANGUAGES_GOOGLE_SHEETS
from mixity.services.namsor.models import *  # Used to register Namsor models to the Django migration system
from django import forms

try:
    from mixity.storage import FlatCloudinaryStorage, FlatRawCloudinaryStorage

    class RawStorage(FlatRawCloudinaryStorage):
        pass

    class ImageStorage(FlatCloudinaryStorage):
        pass

except ImproperlyConfigured:

    from mixity.storage_dev import LocalOrCloudinaryRawStorage, LocalOrCloudinaryStorage

    class RawStorage(LocalOrCloudinaryRawStorage):
        pass

    class ImageStorage(LocalOrCloudinaryStorage):
        pass


class PressArticle(models.Model):
    title = models.TextField()
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to="press/",
        verbose_name="Image",
    )
    text = models.TextField()
    date = models.DateField()
    link = models.URLField()

    class Meta:
        verbose_name = _("Article de presse")
        verbose_name_plural = _("Articles de presse")
        ordering = ("-date",)

    def __str__(self):
        return self.title

    def get_image_url(self):
        if not self.image:
            return ""
        return self.image.url


class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    category = models.ForeignKey(
        "FAQCategory", related_name="faqs", on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ("category",)

    def __str__(self):
        return self.question


class FAQCategory(models.Model):
    name = models.CharField(max_length=128)
    order = models.IntegerField()
    slug = models.SlugField(max_length=100, unique=True, default="", blank=True)

    class Meta:
        verbose_name = "Catégorie de FAQ"
        verbose_name_plural = "Catégories de FAQ "
        ordering = ("order",)

    def save(self, **kwargs):
        if self.slug == "":
            self.slug = slugify(self.name)
        super().save(**kwargs)

    def __str__(self):
        return self.name


class ConditionsMainCategory(models.Model):
    slug = models.CharField(max_length=128)
    language = models.CharField(
        choices=LANGUAGE_CHOICES, default="fr", max_length=7, verbose_name=_("Langue")
    )

    class Meta:
        verbose_name = "Catégorie principale d'une page de conditions"
        verbose_name_plural = "Catégories principales des pages de conditions"
        ordering = ("slug", "language")

    @property
    def name(self):
        return str(self)

    def __str__(self):
        return self.slug + "_" + self.language


class ConditionsSection(models.Model):
    category = models.ForeignKey(
        "ConditionsMainCategory", related_name="sections", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=128)
    content = models.TextField()
    order = models.IntegerField()

    class Meta:
        verbose_name = "Section d'une condition"
        verbose_name_plural = "Sections d'une condition"
        ordering = ("order",)

    def __str__(self):
        return self.title

    def get_content(self):
        return self.content.__str__().replace("\n", "<br/>")

    def hash(self):
        return self.__hash__().__str__()


def upload_location(instance, filename):
    base_path = "img/partners/"
    file_name, extension = filename.split(".")
    return base_path + slugify(instance.image_alt)[:60] + "." + extension


class NonEvaluatedClient(models.Model):
    image_alt = models.CharField(max_length=128, blank=True)
    image = models.ImageField(upload_to=upload_location, blank=True)
    order = models.IntegerField(default=0)
    pme = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Client non évalué"
        verbose_name_plural = "Clients non évalués"
        ordering = ["order", "image_alt"]

    @property
    def get_logo_url(self):
        return self.image.url

    @property
    def has_logo(self):
        return bool(self.image)


class Language(models.Model):
    code = models.CharField(max_length=2, unique=True)
    label = models.CharField(max_length=30)

    @cached_property
    def flag_url(self):
        return f"static/language_flags/{self.code}.svg"

    def is_enabled(self):
        return self.code in ENABLED_WEBSITE_LANGUAGES

    def is_google_sheet_lang(self):
        for lang in LANGUAGES_GOOGLE_SHEETS:
            if self.code == LANGUAGES_GOOGLE_SHEETS[lang]:
                return True
        return False

    def __str__(self):
        return self.label


def get_default_order():
    return None


class SolutionFormat(models.Model):
    slug = models.SlugField(max_length=45, blank=True, null=True)
    label = models.CharField(max_length=45)

    def __str__(self):
        return self.label


# Customized django admin form field in scoring
class ModifiedArrayField(ArrayField):
    def formfield(self, **kwargs):
        defaults = {
            "form_class": forms.MultipleChoiceField,
            "choices": self.base_field.choices,
            "widget": forms.CheckboxSelectMultiple,
            **kwargs,
        }
        return super(ArrayField, self).formfield(**defaults)
