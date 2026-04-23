from dataclasses import dataclass

from django.urls import reverse
from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from django.utils.safestring import mark_safe
from django.db import models
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from tinymce.widgets import TinyMCE
from django import forms

from mixity.models import (
    FAQ,
    FAQCategory,
    ConditionsMainCategory,
    ConditionsSection,
    PressArticle,
    NonEvaluatedClient,
    Language,
    SolutionFormat,
)
from mixity.utils import CSSJsAdminMixin, deep_getattr


def model_link(attr, model, tooltip=None, label=None, **kwargs):
    """
    Create an HTML link toward the targeted @model admin. This requires that @model already has a registered admin.

    Warning: to prevent performance issues, you need to select or prefetch the related fields.

    Usage:
        class MyAdmin(Admin):
            list_fields = [
                "id",
                "my_field",
                ...
            ]

            my_field = model_link("attr.subattr.final_attr", FinalModel)
    """
    if attr is None:
        getter = lambda obj: obj
    elif callable(attr):
        getter = attr
    else:
        getter = lambda obj: deep_getattr(obj, attr)
    if label is None:
        label = lambda obj: str(getter(obj))
    elif isinstance(label, str):
        label = lambda obj: deep_getattr(obj, label)
    if tooltip is None:
        tooltip = model._meta.model_name
    base_url = "admin:%s_change" % model._meta.db_table

    def link_func(self, obj):
        if getter(obj) is None:
            return "--"
        obj_label = label(obj) if callable(label) else label
        return mark_safe(
            '<a href="%s">%s</a>'
            % (reverse(base_url, args=(getter(obj).pk,)), obj_label)
        )

    link_func.short_description = tooltip
    return link_func


@dataclass
class RawInputMixin:
    fk_select_fields: tuple = tuple()
    force_prefetch_related: tuple = tuple()
    force_select_related: tuple = tuple()

    def force_raw_id_fields(self, db_field):
        field_name = db_field.name
        if (
            field_name not in self.raw_id_fields
            and field_name not in self.fk_select_fields
        ):
            if isinstance(db_field, (models.ForeignKey, models.ManyToManyField)):
                self.raw_id_fields = tuple(self.raw_id_fields) + (field_name,)

    def wrap_query(self, query):
        return query.prefetch_related(*self.force_prefetch_related).select_related(
            *self.force_select_related
        )


class MixityAdmin(ModelAdmin, RawInputMixin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        res = super().formfield_for_dbfield(db_field, **kwargs)
        self.force_raw_id_fields(db_field)
        return res

    def get_queryset(self, request):
        query = super().get_queryset(request)
        return self.wrap_query(query)


class MixityTabularInline(TabularInline, RawInputMixin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        res = super().formfield_for_dbfield(db_field, **kwargs)
        self.force_raw_id_fields(db_field)
        return res

    def get_queryset(self, request):
        query = super().get_queryset(request)
        return self.wrap_query(query)


class PressArticleAdmin(ModelAdmin):
    list_display = ["title", "date"]

    class Meta:
        fields = "__all__"


class FAQAdmin(TranslationAdmin, CSSJsAdminMixin):
    list_display = [
        "category",
        "question",
    ]

    class Meta:
        fields = "__all__"


class FAQCategoryAdmin(ModelAdmin):
    list_display = [
        "name",
    ]

    class Meta:
        fields = "__all__"


class ConditionsSectionInline(TabularInline):
    model = ConditionsSection
    can_delete = True
    extra = 0
    fields = ("title", "content", "order")
    formfield_overrides = {
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 30})},
    }


class ConditionsMainCategoryAdmin(ModelAdmin):
    list_display = ["name", "slug", "language"]
    inlines = [ConditionsSectionInline]

    class Meta:
        fields = "__all__"


class NonEvaluatedClientAdmin(ModelAdmin):
    list_display = ["image_alt", "order"]
    ordering = ["order", "image_alt"]

    class Meta:
        fields = "__all__"


class LanguageAdmin(ModelAdmin):
    list_display = ["label"]


class SolutionFormatAdmin(ModelAdmin):
    list_display = ["slug", "label"]


admin.site.register(PressArticle, PressArticleAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(FAQCategory, FAQCategoryAdmin)
admin.site.register(NonEvaluatedClient, NonEvaluatedClientAdmin)
admin.site.register(ConditionsMainCategory, ConditionsMainCategoryAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(SolutionFormat, SolutionFormatAdmin)
