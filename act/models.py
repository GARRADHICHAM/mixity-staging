from functools import cached_property

from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured
from accounts.vocabularies import LANGUAGE_CHOICES


from accounts.vocabularies import (
    COUNTRIES_CHOICES,
    REGIONS_CHOICES,
)
from mixity.models import Language, SolutionFormat

try:
    from cloudinary_storage.storage import (
        RawMediaCloudinaryStorage,
        MediaCloudinaryStorage,
    )

    class RawStorage(RawMediaCloudinaryStorage):
        pass

    class ImageStorage(MediaCloudinaryStorage):
        pass

except ImproperlyConfigured:

    class RawStorage(FileSystemStorage):
        pass

    class ImageStorage(FileSystemStorage):
        pass


class Solver(models.Model):
    inscription_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'inscription"),
        editable=False,
    )
    structure = models.OneToOneField(
        "accounts.Structure",
        on_delete=models.CASCADE,
        verbose_name=_("Structure"),
        related_name="solver",
    )
    is_validated_by_admin = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Validée par l'Admin",
    )

    def __str__(self):
        return self.structure.juridic_name

    def do_admin_validation(self):
        self.is_validated_by_admin = True
        self.save()


class SolutionKeyword(models.Model):
    slug = models.SlugField(max_length=50)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


class Solution(models.Model):
    """
    - NOTE about Translations :
        For the text and char fields translations ( FR, EN, ES)
        will be given by the solvers
    - NOTE about media files storage :
        solution media files (thumbnail photo, video and attachments) are meant to be stored with Cloudinary
    """

    solver = models.ForeignKey(
        to=Solver,
        related_name="solutions",
        verbose_name=_("Solutionneur"),
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=80, verbose_name=_("Titre"))
    creation_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        editable=False,
    )
    modification_date = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
    )
    summary = models.TextField(max_length=250, verbose_name=_("Résumé"))
    photo = models.ImageField(
        blank=True,
        null=True,
        upload_to="solutions_thumbnails/",
        verbose_name=_("Miniature de la solution"),
        storage=ImageStorage,
    )

    referent = models.CharField(max_length=50, verbose_name=_("Responsable"), null=True)

    email = models.EmailField(_("Adresse email"), null=True)

    @cached_property
    def photo_url(self):
        if self.photo and hasattr(self.photo, "url"):
            return self.photo.url
        else:
            return "default"

    description = models.TextField(verbose_name=_("Description"), blank=True, null=True)

    # Territory (NB : by default, the territory is the country except for France is regions)
    country = models.CharField(
        choices=COUNTRIES_CHOICES + [("", _("Choisissez un pays"))],
        verbose_name=_("Pays"),
        max_length=50,
        default=("FR", "France"),
    )
    region = models.CharField(
        choices=list(REGIONS_CHOICES[:-1]) + [("", _("Choisissez une région"))],
        verbose_name=_("Région"),
        max_length=50,
        blank=True,
        null=True,
    )

    languages = models.ManyToManyField(
        to=Language, related_name="solutions", verbose_name=_("Langues")
    )

    # Video : TODO LATER

    price_desc = models.TextField(
        verbose_name=_("Description des tarifs"), blank=True, null=True
    )

    # Public : TODO LATER

    keywords = models.ManyToManyField(
        to=SolutionKeyword,
        related_name="solutions",
        verbose_name=_("Mots-clés"),
        blank=True,
    )
    categories = models.ManyToManyField(
        "scoring.Category",
        verbose_name=_("Catégories"),
        related_name="solutions",
    )
    subcategories = models.ManyToManyField(
        "scoring.SubCategory",
        verbose_name=_("Sous-catégories"),
        related_name="solutions",
    )

    public = models.TextField(verbose_name=_("Public"), blank=True, null=True)
    objective = models.TextField(verbose_name=_("Objectif"), blank=True, null=True)
    format_session = models.TextField(verbose_name=_("Format"), blank=True, null=True)
    solution_formats = models.ManyToManyField(
        to=SolutionFormat,
        related_name="solutions",
        verbose_name=_("Formats de la solution"),
        blank=True,
    )
    # Tracking user on solution click
    users_tracked = models.ManyToManyField(
        to="accounts.MixityUser",
        blank=True,
        related_name="solutions_seen",
        verbose_name="Utilisateurs ayant vu la solution",
    )
    # Tracking user on contact button click
    users_tracked_contact = models.ManyToManyField(
        to="accounts.MixityUser",
        blank=True,
        related_name="solutions_contacted",
        verbose_name="Utilisateurs ayant voulu prendre contact",
    )

    def __str__(self):
        return self.title

    def is_favorite(self, structure):
        """
        Check if the solution in the favorite list solutions of a structure or no
        """
        return structure.favorite_solutions.filter(id=self.id).exists()


class SolutionAttachment(models.Model):
    solution = models.ForeignKey(
        to=Solution,
        related_name="attachments",
        verbose_name=_("Solution"),
        on_delete=models.CASCADE,
    )
    file = models.FileField(
        upload_to="solutions_files/", blank=True, null=True, storage=RawStorage
    )


class BestPractice(models.Model):
    structure = models.ForeignKey(
        to="accounts.Structure",
        on_delete=models.CASCADE,
        verbose_name=_("Structure"),
        related_name="best_practices",
    )
    logo = models.ImageField(
        blank=True,
        null=True,
        upload_to="best_practices_logos/",
        verbose_name=_("Logo"),
        storage=ImageStorage,
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Site Web"),
    )
    email = models.EmailField(
        verbose_name=_("Mail de la personne référente"), blank=True, null=True
    )
    deployment_date = models.DateField(
        verbose_name=_("Date de déploiement"), blank=True, null=True
    )
    referent = models.CharField(
        max_length=50, verbose_name=_("Personne référente"), blank=True, null=True
    )
    label = models.CharField(
        max_length=80,
        verbose_name=_("Nom de la pratique"),
    )
    country = models.CharField(
        choices=COUNTRIES_CHOICES + [("", _("Choisissez un pays"))],
        verbose_name=_("Pays"),
        max_length=50,
        default=("FR", "France"),
    )
    summary = models.TextField(max_length=250, verbose_name=_("Résumé de la pratique"))
    description = models.TextField(verbose_name=_("Description de la pratique"))

    setting_up = models.TextField(
        verbose_name=_("Mise en place"), blank=True, null=True
    )

    difficulties = models.TextField(
        verbose_name=_("Difficultés"), blank=True, null=True
    )

    advice = models.TextField(verbose_name=_("Conseil"), blank=True, null=True)

    testimony = models.TextField(verbose_name=_("Témoignage"), blank=True, null=True)
    results = models.TextField(verbose_name=_("Résultats"), blank=True, null=True)
    publics = models.ManyToManyField(
        to="act.BestPracticePublic",
        related_name="best_practices",
        verbose_name=_("Public"),
    )
    type = models.ManyToManyField(
        to="act.BestPracticeType",
        related_name="best_practices",
        verbose_name=_("Type de bonne pratique"),
    )
    size = models.ManyToManyField(
        to="act.BestPracticeSize",
        related_name="best_practices",
        verbose_name=_("Taille"),
    )
    categories = models.ManyToManyField(
        to="scoring.Category",
        related_name="best_practices",
        verbose_name=_("Catégories"),
    )
    subcategories = models.ManyToManyField(
        to="scoring.SubCategory",
        related_name="best_practices",
        verbose_name=_("Dimensions"),
    )
    keywords = models.ManyToManyField(
        to="act.BestPracticeKeyword",
        related_name="best_practices",
        verbose_name=_("Mots clés"),
    )
    organization_type = models.ManyToManyField(
        to="act.BestPracticeOrganizationType",
        related_name="best_practices",
        verbose_name=_("Type d'organisation"),
    )
    is_public = models.BooleanField(verbose_name=_("est Publique"), default=False)

    def __str__(self):
        return self.label


class BestPracticePublic(models.Model):
    slug = models.SlugField(max_length=45, blank=True, null=True)
    label = models.CharField(max_length=45)

    def __str__(self):
        return self.label


class BestPracticeType(models.Model):
    slug = models.SlugField(max_length=45, blank=True, null=True)
    label = models.CharField(max_length=45)

    def __str__(self):
        return self.label


class BestPracticeSize(models.Model):
    slug = models.SlugField(max_length=30, blank=True, null=True)
    label = models.CharField(max_length=30)

    def __str__(self):
        return self.label


class BestPracticeKeyword(models.Model):
    slug = models.SlugField(max_length=45, blank=True, null=True)
    label = models.CharField(max_length=45)

    def __str__(self):
        return self.label


class BestPracticeOrganizationType(models.Model):
    slug = models.SlugField(max_length=40, blank=True, null=True)
    label = models.CharField(max_length=40)

    def __str__(self):
        return self.label


class ElearningNotion(models.Model):
    slug = models.SlugField(max_length=50)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


class ElearningEvaluationMethod(models.Model):
    slug = models.SlugField(max_length=50)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


class ElearningKeyword(models.Model):
    slug = models.SlugField(max_length=50)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


class Elearning(models.Model):
    slug = models.SlugField(max_length=40, blank=True, null=True)
    title = models.CharField(max_length=128, verbose_name=_("Titre"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    summary = models.TextField(max_length=250, verbose_name=_("Résumé"))
    photo = models.ImageField(
        blank=True,
        null=True,
        upload_to="elearning_thumbnails/",
        verbose_name=_("Miniature de l'elearning'"),
        storage=ImageStorage,
    )
    languages = models.ManyToManyField(
        to=Language, related_name="elearnings", verbose_name=_("Langues")
    )
    time = models.TextField(max_length=50, verbose_name=_("Durée de l'elearning"))
    target = models.TextField(max_length=50, verbose_name=_("public visé"))
    video = models.TextField(blank=True, verbose_name=_("Lien de la vidéo"))
    objective = models.TextField(verbose_name=_("Objectif"), blank=True, null=True)
    added_value = models.TextField(
        verbose_name=_("Valeur ajoutée"), blank=True, null=True
    )
    keywords = models.ManyToManyField(
        to=ElearningKeyword,
        related_name="elearning",
        verbose_name=_("Mots-clés"),
        blank=True,
    )
    is_certifiable = models.BooleanField(
        verbose_name=_("est certifiable"), default=False
    )
    evaluation_methods = models.ManyToManyField(
        to=ElearningEvaluationMethod,
        related_name="elearning",
        verbose_name=_("Méthodes d'évaluation"),
        blank=True,
    )
    category = models.ManyToManyField(
        "scoring.Category",
        verbose_name=_("Catégories"),
        related_name="elearnings",
    )
    notions = models.ManyToManyField(
        to=ElearningNotion,
        related_name="elearning",
        verbose_name=_("Notions"),
        blank=True,
    )

    def __str__(self):
        return self.title
