import csv
import datetime
import io

from address.models import Country
from django import forms
from django.contrib import admin, messages
from django.utils.text import slugify
from django.contrib.admin import ModelAdmin, SimpleListFilter
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UsernameField
from django.db.models import JSONField
from django.db.models.query import Prefetch
from django.http import HttpResponse
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_json_widget.widgets import JSONEditorWidget
from modeltranslation.admin import TranslationAdmin
from django.db.models.functions import Coalesce
from django.db.models import Q, F, Count
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
from accounts.models import Structure
from tinymce.widgets import TinyMCE
from django_rq import job

from mixity.utils import CSSJsAdminMixin

# from scoring.admin import aggregate_score
from scoring.models import Evaluation, QuestionTag, QuestionSheet
from subscriptions.models import SubscriptionPack, SubscriptionOption, Product
from subscriptions.admin import generate_evaluations, generate_human_or_scan_evaluation


from .models import (
    DiversityLabel,
    Membership,
    MixityUser,
    Structure,
    BusinessLine,
    EntityLevel,
    Entity,
)


class StructureCountryFilter(SimpleListFilter):
    title = "country"
    parameter_name = "structure__address__locality__state__country"

    def lookups(self, request, model_admin):
        active_countries = Country.objects.filter(
            states__localities__isnull=False
        ).distinct()
        return active_countries.values_list("id", "name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                address__locality__state__country__id__exact=self.value()
            )
        else:
            return queryset


class StructureBusinessLineFilter(SimpleListFilter):
    title = "Business Line"
    parameter_name = "business_line"

    def lookups(self, request, model_admin):
        return BusinessLine.objects.values_list("id", "name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(business_line__id__exact=self.value())
                | Q(secondary_business_lines__id__exact=self.value())
            )
        else:
            return queryset


class MixityUserForm(UserChangeForm):
    class Meta:
        model = MixityUser
        fields = "__all__"
        field_classes = {"username": UsernameField}


class MembershipInline(admin.TabularInline):
    model = Membership
    fields = ["user", "is_owner", "is_reader"]


class UserMembershipInline(admin.TabularInline):
    model = Membership
    fields = ["structure", "entity", "is_owner", "is_reader"]


class MixityUserAdmin(UserAdmin):
    list_display = ["username", "email", "language", "first_name", "last_name"]
    inlines = [
        UserMembershipInline,
    ]
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "foto",
                    "gender",
                    "first_name",
                    "last_name",
                    "business_line",
                    "phone",
                    "is_qualified",
                    "language",
                    "currency",
                )
            },
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined", "last_segment_identify")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    form = MixityUserForm
    readonly_fields = ("is_qualified", "last_segment_identify")

    class Meta:
        fields = "__all__"


class StructureForm(forms.ModelForm):
    class Meta:
        model = Structure
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(StructureForm, self).__init__(*args, **kwargs)
        self.fields["human_description_fr"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["human_description_en"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["human_description_es"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["human_description_it"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["human_description_zh_hans"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["human_description_zh_hant"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["human_description_ja"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )


class StructureAdmin(TranslationAdmin, CSSJsAdminMixin):
    form = StructureForm
    change_list_template = "accounts/admin_changelist.html"
    search_fields = [
        "juridic_name",
        "commercial_name",
        "siret",
        "duns",
        "num_tva_intracom",
    ]
    list_display = [
        "juridic_name",
        "workforce",
        "category",
        "business_line",
        "secondary_business_lines_joined",
        # "structure_report_link",
        "has_logo",
        "logo_displayed",
    ]
    inlines = [MembershipInline]
    filter_horizontal = (
        "labels",
        "tags",
        "secondary_business_lines",
        "favorite_solutions",
    )

    list_filter = [
        StructureBusinessLineFilter,
        StructureCountryFilter,
    ]
    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }
    actions = [
        "create_human_pack",
        "create_diag_pack",
        "create_360_pack",
    ]

    class Meta:
        fields = "__all__"

    def get_urls(self):
        return [path("csv_export/", self.csv_export)] + super().get_urls()

    def csv_export(self, request):
        output = io.StringIO()
        writer = csv.writer(
            output,
            delimiter=";" if request.GET.get("delimiter") == "semicolon" else ",",
            quoting=csv.QUOTE_NONNUMERIC,
        )
        writer.writerow(
            [
                "structure_id",
                "structure_name",
                "structure_phone_number",
                "member_first_name",
                "member_last_name",
                "member_email",
                "member_status",
            ]
        )
        for structure in Structure.objects.all():
            writer.writerow(
                [
                    structure.id,
                    structure.juridic_name or structure.commercial_name,
                    structure.phone1,
                ]
            )
            owners = structure.owners.all()
            for member in structure.members.all():
                writer.writerow(
                    [
                        "",
                        "",
                        "",
                        member.first_name,
                        member.last_name,
                        member.email,
                        "owner" if member in owners else "member",
                    ]
                )
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="structure_dump_'
            + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            + '.csv"'
        )
        return response

    def get_queryset(self, request):
        return (
            super(StructureAdmin, self)
            .get_queryset(request)
            .prefetch_related(
                Prefetch(
                    "entity_level__entities",
                    queryset=Entity.objects.all(),
                ),
                "secondary_business_lines",
            )
            .annotate(
                num_evaluations=Coalesce(
                    Count("entity_level__entities__evaluations", distinct=True), 0
                )
            )
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        self.ensure_main_entity(form.instance)

    @staticmethod
    def ensure_main_entity(structure):
        # Même initialisation que la création côté client (CreateStructure) :
        # sans entité principale, le tableau de bord et les packs ne fonctionnent pas.
        entity = structure.get_main_entity
        if entity is None:
            entity_level, _ = EntityLevel.objects.get_or_create(
                structure=structure, level=0, defaults={"label": "Groupe"}
            )
            entity = Entity.objects.create(
                name=f"{structure.juridic_name}-main",
                entity_level=entity_level,
                workforce=structure.workforce,
                country=structure.country,
                phone=structure.phone1,
            )

            workforce = structure.workforce
            if workforce < 50:
                tag_name = "very_small_company"
            elif workforce < 250:
                tag_name = "50_250_company"
            elif workforce < 500:
                tag_name = "small_company"
            elif workforce < 1000:
                tag_name = "middle_company"
            elif workforce < 5000:
                tag_name = "1000_4999_company"
            else:
                tag_name = "5000_company"
            tags = list(QuestionTag.objects.filter(name=tag_name))
            if structure.country:
                country_tag, _ = QuestionTag.objects.get_or_create(
                    name=structure.country.code.lower()
                )
                tags.append(country_tag)
            structure.tags.add(*tags)
            entity.tags.add(*tags)
            structure.__dict__.pop("get_main_entity", None)

        structure.memberships.filter(entity__isnull=True).update(entity=entity)

    def secondary_business_lines_joined(self, obj):
        return ", ".join(bs.name for bs in obj.secondary_business_lines.all())

    # def structure_report_link(self, obj):
    #     if obj.num_evaluations > 0:
    #         url = reverse("scoring:detail_public", args=[obj.slug])
    #         link = '<strong><a href="{}">Dernière fiche entreprise</a></strong>'.format(
    #             url
    #         )
    #         return mark_safe(link)

    #     return "Aucune fiche entreprise disponible"

    def has_logo(self, obj):
        return bool(obj.logo and obj.logo.url)

    has_logo.boolean = True

    def logo_displayed(self, obj):
        return self.has_logo(obj) and obj.display_on_website

    logo_displayed.boolean = True

    # structure_report_link.short_description = "Fiche Entreprise"

    def create_pack_and_option(self, structure, slug):
        start_date = now().date()
        end_date = start_date + relativedelta(years=1)

        if not SubscriptionPack.objects.filter(
            structure=structure, end_date__gte=now().date()
        ).exists():
            new_pack = SubscriptionPack.objects.create(
                is_active=True,
                start_date=start_date,
                end_date=end_date,
                structure=structure,
            )
        else:
            # Correspond à la création d'un pack 360, évite de créer un pack en doublon.
            new_pack = (
                SubscriptionPack.objects.filter(structure=structure)
                .order_by("-start_date")
                .first()
            )
        option = SubscriptionOption.objects.create(
            is_active=True,
            start_date=start_date,
            end_date=end_date,
            subscriptionPack=new_pack,
            product=Product.objects.get(slug=slug),
        )

        if not SubscriptionPack.objects.filter(
            structure=structure, end_date__lte=now().date()
        ).exists():
            if slug == "diag":
                message, level = generate_evaluations(option)
            else:
                message, level = generate_human_or_scan_evaluation(option)
            return (
                f"Succès : Création du nouveau pack, de l'option {slug}, {message}.",
                level,
            )
        # Si un pack inactif existe, on doit vérifier s'il y a des évaluations en cours ou non.
        else:
            if slug == "diag" and not Evaluation.objects.filter(
                display_version="en-cours"
            ).exclude(sheet__type__slug="evaluation_collaborateurs_360").exclude(
                sheet__type__slug="mixity_evaluation_scan"
            ):
                message, level = generate_evaluations(option)
                return (
                    f"Succès : Création du nouveau pack, de l'option {slug}, {message}.",
                    level,
                )
            elif slug == "human" and not Evaluation.objects.filter(
                display_version="en-cours",
                sheet__type__slug="evaluation_collaborateurs_360",
            ):
                message, level = generate_human_or_scan_evaluation(option)
                return (
                    f"Succès : Création du nouveau pack, de l'option {slug}, {message}.",
                    level,
                )
            else:
                return (
                    f"Succès : Création du nouveau pack, de l'option {slug}, évaluation.s déjà en cours.",
                    messages.SUCCESS,
                )

    def handle_create_pack(self, request, queryset, slug):
        if queryset.count() != 1:
            return (
                "Veuillez sélectionner une seule structure à la fois.",
                messages.ERROR,
            )

        structure = queryset.first()
        if SubscriptionPack.objects.filter(
            structure=structure, end_date__gte=now().date()
        ).exists():
            return (
                "Cette structure a déjà un pack actif ! Rendez-vous dans subscription pack pour mettre à jour les options",
                messages.ERROR,
            )

        try:
            message, level = self.create_pack_and_option(structure, slug)
            return message, messages.SUCCESS
        except Exception as e:
            return (
                f"Erreur lors de la création du pack ou de l'option : {str(e)}",
                messages.ERROR,
            )

    def create_human_pack(self, request, queryset):
        message, level = self.handle_create_pack(request, queryset, "human")
        self.message_user(request, message, level=level)

    def create_diag_pack(self, request, queryset):
        message, level = self.handle_create_pack(request, queryset, "diag")
        self.message_user(request, message, level=level)

    def create_360_pack(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Veuillez sélectionner une seule structure à la fois.",
                level=messages.ERROR,
            )
            return

        structure = queryset.first()
        if SubscriptionPack.objects.filter(
            structure=structure, end_date__gte=now().date()
        ).exists():
            self.message_user(
                request,
                "Cette structure a déjà un pack actif ! Rendez-vous dans subscription pack pour mettre à jour les options",
                level=messages.ERROR,
            )
            return

        try:
            message_human, level = self.create_pack_and_option(structure, "human")
            message_diag, level = self.create_pack_and_option(structure, "diag")
            self.message_user(request, f"{message_human} {message_diag}", level=level)
        except Exception as e:
            self.message_user(
                request,
                f"Erreur lors de la création des packs ou des options : {str(e)}",
                level=messages.ERROR,
            )


class DiversityLabelAdmin(admin.ModelAdmin):
    list_display = ["name", "image_url"]


class BusinessLineAdmin(admin.ModelAdmin, CSSJsAdminMixin):
    list_display = ["slug", "name_fr", "name_en", "name_es", "is_private"]
    ordering = ["slug"]

    class Meta:
        fields = "__all__"


class EntityLevelAdmin(admin.ModelAdmin):
    list_display = ["structure", "level", "label"]

    class Meta:
        fields = "__all__"


class SelectWOA(forms.widgets.Select):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super(SelectWOA, self).create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if option["value"] and option["name"] == "entity_level":
            option["label"] = (
                _(option["value"].instance.structure_name) + " - " + option["label"]
            )
        return option


class EntityForm(forms.ModelForm):
    entity_level = forms.ModelChoiceField(
        queryset=EntityLevel.objects.only("level").annotate(
            structure_name=F("structure__juridic_name")
        ),
        widget=SelectWOA(),
    )
    model = Entity
    fields = "__all__"


class EntityAdmin(admin.ModelAdmin):
    form = EntityForm
    search_fields = [
        "name",
        "entity_level__level",
        "entity_level__structure__juridic_name",
    ]
    list_display = ["name", "parent_entity", "entity_level", "structure"]
    filter_horizontal = [
        "favorite_solutions",
        "tags",
        "favorite_best_practices",
    ]
    inlines = [MembershipInline]

    def structure(self, obj):
        return obj.entity_level.structure

    class Meta:
        fields = "__all__"


admin.site.register(DiversityLabel, DiversityLabelAdmin)
admin.site.register(Structure, StructureAdmin)
admin.site.register(MixityUser, MixityUserAdmin)
admin.site.register(BusinessLine, BusinessLineAdmin)
admin.site.register(EntityLevel, EntityLevelAdmin)
admin.site.register(Entity, EntityAdmin)
