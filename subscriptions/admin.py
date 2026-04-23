from django import forms
import datetime
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.safestring import mark_safe
from modeltranslation.admin import TranslationTabularInline
from django_rq import job
from django.utils.text import slugify
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
from django.db.models import Q

from mixity.utils import CSSJsAdminMixin
from scoring.models import Evaluation, QuestionSheet, QuestionSheetType, QuestionTag
from accounts.models import Entity
from subscriptions.mails import send_offer_validated
from subscriptions.models import (
    Subscription,
    SubscriptionType,
    Coupon,
    SubscriptionPack,
    SubscriptionOption,
    Product,
)


# class PriceInline(TranslationTabularInline):
#     model = Price
#     can_delete = True
#     extra = 0
#     # fields = ["workforce_limit", "tax_free_price"]


class SubscriptionTypeAdmin(admin.ModelAdmin, CSSJsAdminMixin):
    list_display = [
        "label",
        "slug",
        "order",
        "is_active",
        "allow_structure_evaluation",
        "allow_public_display",
        "allow_collaborator_evaluation",
    ]
    # inlines = [PriceInline]
    exclude = (
        "allow_opinion_activation",
        "allow_advanced_search",
        "search_criteria_number",
        "allow_kitcom_purchasing",
        "allow_evaluation_opinions",
    )
    filter_horizontal = ("question_sheet_types",)


class EvaluationInline(admin.TabularInline):
    model = Evaluation
    can_delete = True
    extra = 0
    fields = ("entity", "sheet", "created_date")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class CustomQuestionSheetTypeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.workforce_limit:
            return f"{obj.name} - moins de {obj.workforce_limit} personnes"
        else:
            return f"{obj.name}"


class CustomQuestionSheetTypeAdminForm(forms.ModelForm):
    question_sheet_type = CustomQuestionSheetTypeChoiceField(
        queryset=QuestionSheetType.objects.all()
    )

    class Meta:
        model = Subscription
        fields = "__all__"


class SubscriptionAdmin(admin.ModelAdmin):
    form = CustomQuestionSheetTypeAdminForm
    search_fields = ["structure__juridic_name", "structure__commercial_name"]
    list_display = [
        "structure",
        "subscription_type",
        "evaluations_list",
        "question_sheet_type_label",
        "is_active",
        "start_date",
        "end_date",
    ]
    exclude = [
        "allow_advanced_search",
        "search_criteria_number",
        "allow_kitcom_purchasing",
    ]
    inlines = [
        EvaluationInline,
    ]
    filter_horizontal = ("tags",)
    readonly_fields = ["pdf_invoice"]

    def get_queryset(self, request):
        queryset = super(SubscriptionAdmin, self).get_queryset(request)
        return queryset.select_related(
            "structure",
            "question_sheet_type",
            "subscription_type",
        ).prefetch_related("evaluations__entity")

    def evaluations_list(self, obj):
        evaluations = []
        for evaluation in obj.evaluations.all():
            evaluations.append(evaluation.entity.name)
        return evaluations

    def question_sheet_type_label(self, obj):
        if obj.question_sheet_type and obj.question_sheet_type.workforce_limit:
            return f"{obj.question_sheet_type.name} - moins de {obj.question_sheet_type.workforce_limit} personnes"
        elif obj.question_sheet_type:
            return f"{obj.question_sheet_type.name}"
        else:
            return "-"

    def pdf_invoice(self, obj):
        if not obj.invoice:
            return None
        reverse_pdf = reverse("invoices:view", args=(obj.invoice.pk,))
        return mark_safe(f"<a target='_blank' href='{reverse_pdf}'>{reverse_pdf}</a>")

    pdf_invoice.short_description = "Facture PDF"

    class Meta:
        fields = "__all__"


class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "quantity", "is_valid", "already_use"]

    class Meta:
        fields = "__all__"

    def already_use(self, obj):
        return obj.subscriptions.count()


class SubscriptionPackAdmin(admin.ModelAdmin):
    search_fields = ["structure__juridic_name", "structure__commercial_name"]
    list_display = [
        "structure",
        "structure_link",
        "start_date",
        "end_date",
        "is_active",
    ]
    actions = [
        "add_human_option",
        "add_diag_option",
        "add_360_option",
    ]

    def display_products(self, obj):
        return ", ".join(
            [product.label for product in obj.subscriptionoption_set.all()]
        )

    display_products.short_description = "Products"

    def structure_link(self, obj):
        url = reverse("admin:accounts_structure_change", args=[obj.structure.id])
        link = '<strong><a href="{}">{}</a></strong>'.format(url, obj.structure)
        return mark_safe(link)

    structure_link.short_description = "Structure"

    def add_option(self, obj, slug):
        now_date = now().date()
        options = obj.options.filter(end_date__gte=now_date, product__slug=slug)

        if options.count() >= 1:
            current_option = options.order_by("-end_date").first()
            tags = current_option.tags.all()
            new_subscription_option = SubscriptionOption.objects.create(
                is_active=True,
                start_date=now_date,
                end_date=current_option.end_date + relativedelta(years=1),
                subscriptionPack=obj,
                product=Product.objects.get(slug=slug),
            )

            option_message, level = (
                f"Succès : Le renouvellement de l'option {slug} a été enregistré.",
                messages.SUCCESS,
            )

            current_option.is_active = False
            current_option.end_date = now_date
            current_option.save()
            for tag in tags:
                new_subscription_option.tags.add(tag)
            if obj.end_date < new_subscription_option.end_date:
                obj.end_date = new_subscription_option.end_date
                obj.save()

            # Génération des évaluations :
            evaluation_message = ""
            if (
                slug == "diag"
                and Evaluation.objects.filter(display_version="en-cours")
                .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .exists()
            ):
                evaluation_message, eval_level = generate_evaluations(
                    new_subscription_option
                )
            elif (
                slug == "human"
                and Evaluation.objects.filter(
                    display_version="en-cours",
                    sheet__type__slug="evaluation_collaborateurs_360",
                ).exists()
            ):
                evaluation_message, eval_level = generate_human_or_scan_evaluation(
                    new_subscription_option
                )

            if evaluation_message != "":
                return (f"{option_message} {evaluation_message}", level)
            else:
                return (f"{option_message} évaluation.s en cours à compléter", level)
        else:
            new_subscription_option = SubscriptionOption.objects.create(
                is_active=True,
                start_date=now_date,
                end_date=now_date + relativedelta(years=1),
                subscriptionPack=obj,
                product=Product.objects.get(slug=slug),
            )
            # Allongement de la durée du pack si période de validité de l'option plus longue.
            if obj.end_date < new_subscription_option.end_date:
                obj.end_date = new_subscription_option.end_date
                obj.save()

            option_message, level = (
                f"Succès : L'option {slug} a été ajoutée au pack, ",
                messages.SUCCESS,
            )

            # Génération des évaluations.
            evaluation_message = ""
            if (
                slug == "diag"
                and not Evaluation.objects.filter(display_version="en-cours")
                .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .exists()
            ):
                evaluation_message, eval_level = generate_evaluations(
                    new_subscription_option
                )
            elif (
                slug == "human"
                and not Evaluation.objects.filter(
                    display_version="en-cours",
                    sheet__type__slug="evaluation_collaborateurs_360",
                ).exists()
            ):
                evaluation_message, eval_level = generate_human_or_scan_evaluation(
                    new_subscription_option
                )

            if evaluation_message != "":
                return (f"{option_message} {evaluation_message}", level)
            else:
                return (f"{option_message} évaluation.s en cours à compléter", level)

    def add_human_option(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Veuillez sélectionner un seul pack à la fois.",
                level=messages.ERROR,
            )
            return

        obj = queryset.first()
        if obj.end_date < now().date():
            self.message_user(
                request,
                "Le pack séléctionné n'est plus valide, veuillez en créer un nouveau pour cette structure",
                level=messages.ERROR,
            )
            return
        message, level = self.add_option(obj, "human")
        self.message_user(request, message, level=level)

    add_human_option.short_description = "Ajouter l'option human"

    def add_diag_option(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Veuillez sélectionner un seul pack à la fois.",
                level=messages.ERROR,
            )
            return

        obj = queryset.first()
        if obj.end_date < now().date():
            self.message_user(
                request,
                "Le pack séléctionné n'est plus valide, veuillez en créer un nouveau pour cette structure",
                level=messages.ERROR,
            )
            return
        message, level = self.add_option(obj, "diag")
        self.message_user(request, message, level=level)

    add_diag_option.short_description = "Ajouter l'option diag"

    def add_360_option(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Veuillez sélectionner un seul pack à la fois.",
                level=messages.ERROR,
            )
            return

        obj = queryset.first()
        if obj.end_date < now().date():
            self.message_user(
                request,
                "Le pack séléctionné n'est plus valide, veuillez en créer un nouveau pour cette structure",
                level=messages.ERROR,
            )
            return
        messages_to_return = []

        # Ajout ou renouvellement de l'option "human"
        message, level = self.add_option(obj, "human")
        messages_to_return.append((message, level))

        # Ajout ou renouvellement de l'option "diag"
        message, level = self.add_option(obj, "diag")
        messages_to_return.append((message, level))

        # Gestion des messages utilisateurs
        for message, level in messages_to_return:
            self.message_user(request, message, level=level)

    add_360_option.short_description = "Ajouter l'option human et l'option diag"


def validate_offer(modeladmin, request, queryset):
    for option in queryset:
        option.is_active = True
        if option.product.slug == "diag":
            message, level = generate_evaluations(option)
        else:
            message, level = generate_human_or_scan_evaluation(option)

        modeladmin.message_user(request, message, level=level)
        if level == messages.SUCCESS:
            option.save()
            for user in option.subscriptionPack.structure.owners:
                send_offer_validated(request, user, option)


validate_offer.short_description = "Valider les offres"


@job("default")
def generate_human_or_scan_evaluation(option):
    structure = option.subscriptionPack.structure

    # On vérifie qu'aucune évaluation en cours n'existe pour le même produit
    if option.product.slug == "human" and Evaluation.objects.filter(
        entity__entity_level__structure=option.subscriptionPack.structure,
        display_version="en-cours",
        sheet__type__slug="evaluation_collaborateurs_360",
    ):
        return (
            "évaluation déjà en cours.",
            messages.ERROR,
        )
    elif option.product.slug == "scan" and Evaluation.objects.filter(
        entity__entity_level__structure=option.subscriptionPack.structure,
        display_version="en-cours",
        sheet__type__slug="mixity_evaluation_scan",
    ):
        return (
            "évaluation déjà en cours.",
            messages.ERROR,
        )
    else:
        if option.product.slug == "human":
            previous_option = structure.active_human_product
        else:
            previous_option = structure.active_scan_product
        if previous_option == None:
            previous_option = option
        print(previous_option)
        evaluation = Evaluation.objects.create(
            name=structure.juridic_name or structure.commercial_name,
            created_date=now(),
            sheet=previous_option.product.question_sheet_type.question_sheets.last(),
            entity=structure.get_main_entity,
        )
        evaluation.tags.add(
            *(list(structure.tags.all()) + list(previous_option.tags.all()))
        )
        evaluation.save()
        return (
            "évaluation générée avec succès",
            messages.SUCCESS,
        )


@job("default")
def generate_evaluations(option):
    structure = option.subscriptionPack.structure
    entities = Entity.objects.filter(entity_level__structure=structure)

    sheet = QuestionSheet.get_new_evaluation_question_sheet(option)

    if (
        Evaluation.objects.filter(
            entity__entity_level__structure=option.subscriptionPack.structure,
            display_version="en-cours",
        )
        .exclude(
            sheet__type__slug="evaluation_collaborateurs_360",
        )
        .exclude(sheet__type__slug="mixity_evaluation_scan")
    ):
        return (
            "évaluation.s déjà en cours.",
            messages.SUCCESS,
        )

    display_aims_category = False
    if option.tags.filter(name="mixity_start").exists():
        display_aims_category = True

    booleans_tags = []
    tags = []

    # Récupération des tags booléens associés à la structure
    for key in structure.booleans:
        if structure.booleans[key]:
            tag, _ = QuestionTag.objects.get_or_create(name=key)
            booleans_tags.append(tag)

    evaluations_to_create = []

    for entity in entities:
        # Vérification de l'existence d'une évaluation pour la même période et le même produit
        start_datetime = datetime.datetime.combine(option.start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(option.end_date, datetime.time.max)

        if not Evaluation.objects.filter(
            entity=entity,
            created_date__gte=start_datetime,
            created_date__lte=end_datetime,
            sheet__type__slug=option.product.question_sheet_type.slug,
        ).exists():
            evaluations_to_create.append(
                Evaluation(
                    name=ugettext_lazy("Évaluation pour l'année {}").format(
                        timezone.now().year
                    ),
                    created_date=timezone.now(),
                    entity=entity,
                    sheet=sheet,
                    display_aims_category=display_aims_category,
                    is_started=True,
                )
            )

    _evaluations = Evaluation.objects.bulk_create(evaluations_to_create)

    for evaluation in _evaluations:
        tags = booleans_tags.copy()

        # Ajout des tags associés à l'entité de l'évaluation
        tags += list(evaluation.entity.tags.all())

        # Ajout des tags associés à l'option d'abonnement
        tags += list(option.tags.all())

        if evaluation.entity.address:
            tag, _ = QuestionTag.objects.get_or_create(
                name=slugify(structure.address.locality.state.country.code)
            )
            tags.append(tag)

        evaluation.tags.set(tags)
        evaluation.save()
        evaluation.generate_answers()
    return (
        "évaluation.s généré.es avec succès",
        messages.SUCCESS,
    )


class SubscriptionOptionAdmin(admin.ModelAdmin):
    search_fields = [
        "subscriptionPack__structure__juridic_name",
        "subscriptionPack__structure__commercial_name",
    ]
    list_display = [
        "option",
        "product_link",
        "structure_link",
        "pack_link",
        "start_date",
        "end_date",
        "is_active",
    ]
    actions = [
        validate_offer,
    ]

    def option(self, obj):
        return (
            obj.subscriptionPack.structure.juridic_name
            or obj.subscriptionPack.structure.commercial_name
        )

    def product_link(self, obj):
        url = reverse("admin:subscriptions_product_change", args=[obj.product.id])
        link = '<strong><a href="{}">{}</a></strong>'.format(url, obj.product.slug)
        return mark_safe(link)

    product_link.short_description = "Product"

    def structure_link(self, obj):
        url = reverse(
            "admin:accounts_structure_change", args=[obj.subscriptionPack.structure.id]
        )
        link = '<strong><a href="{}">{}</a></strong>'.format(
            url, obj.subscriptionPack.structure
        )
        return mark_safe(link)

    structure_link.short_description = "Structure"

    def pack_link(self, obj):
        url = reverse(
            "admin:subscriptions_subscriptionpack_change",
            args=[obj.subscriptionPack.id],
        )
        link = '<strong><a href="{}">{}</a></strong>'.format(
            url, obj.subscriptionPack.structure
        )
        return mark_safe(link)

    pack_link.short_description = "Pack"


class ProductAdmin(admin.ModelAdmin):
    search_fields = ["slug", "label"]
    list_display = [
        "product",
        "is_active",
        "question_sheet_type",
    ]

    def product(self, obj):
        return obj.label


admin.site.register(SubscriptionType, SubscriptionTypeAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(SubscriptionPack, SubscriptionPackAdmin)
admin.site.register(SubscriptionOption, SubscriptionOptionAdmin)
admin.site.register(Product, ProductAdmin)
