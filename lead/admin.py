from django.contrib import admin
from django.utils.safestring import mark_safe
from django import forms
from django.db import models
from django.db.models import F
from django.utils.translation import ugettext
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelMultipleChoiceField
from scoring.models import SubCategory, Category
from lead.models import Objective, LeadAction, ActionKpi, GenericKpi
from modeltranslation.admin import (
    TranslationAdmin,
)


class ObjectiveAdmin(admin.ModelAdmin):
    title = "objective"
    list_display = [
        "label",
        "category",
        "subcategory",
        "structure",
    ]
    readonly_fields = [
        "creation_date",
        "creation_user",
        "last_modification_date",
        "last_modification_user",
    ]


class ActionAdmin(admin.ModelAdmin):
    title = "action"
    list_display = [
        "label",
        "action_date",
        "status",
        "referent",
    ]
    readonly_fields = [
        "creation_date",
        "creation_user",
        "last_modification_date",
        "last_modification_user",
    ]


class SelectWOA(forms.widgets.Select):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super(SelectWOA, self).create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if option["value"] and option["name"] == "subcategory":
            option["label"] = (
                ugettext(option["value"].instance.category_name)
                + " - "
                + option["label"]
            )
        return option



class ActionKpiAdmin(admin.ModelAdmin):
    # form = ActionKpiForm
    title = "kpi"
    list_display = [
        "__str__",
        "value",
        "goal",
        "category",
        "subcategory",
    ]
    readonly_fields = [
        "creation_date",
        "creation_user",
        "last_modification_date",
        "last_modification_user",
    ]



class CategorySubCategorySelectMultiple(FilteredSelectMultiple):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        if value is not None:
            label = f"{value.instance.category_name} - {value.instance.name}"
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        return option


# class GenericKpiForm(forms.ModelForm):
#     subcategories = ModelMultipleChoiceField(
#         queryset=SubCategory.objects.exclude(
#             category__slug="your-suggestions"
#         ).annotate(category_name=F("category__name")),
#         widget=CategorySubCategorySelectMultiple(
#             "Subcategories", False, attrs={"class": "filtered"}
#         ),
#     )
#
#     class Meta:
#         model = GenericKpi
#         fields = "__all__"


class GenericKpiAdmin(TranslationAdmin):
    # form = GenericKpiForm
    title = "generickpi"
    list_display = ["label", "unit", "kpi_categories", "kpi_subcategories"]

    def kpi_subcategories(self, obj):
        subcategories = []
        for subcat in obj.subcategories.all():
            subcategories.append(" - " + subcat.name)
        return subcategories

    def kpi_categories(self, obj):
        categories = []
        for cat in obj.categories.all():
            categories.append(cat.name)
        return categories


admin.site.register(Objective, ObjectiveAdmin)
admin.site.register(LeadAction, ActionAdmin)
admin.site.register(ActionKpi, ActionKpiAdmin)
admin.site.register(GenericKpi, GenericKpiAdmin)
