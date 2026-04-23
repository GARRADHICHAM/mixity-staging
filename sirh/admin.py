from django.contrib import admin
from django.db.models import JSONField
from django_json_widget.widgets import JSONEditorWidget

from scoring.models import Question
from sirh.models import (
    ADPCredentials,
    ADPSoftware,
    ADPIndicatorType,
    ADPIndicator,
    ADPField,
    ADPFieldMapping,
    ADPFieldValue,
    ADPStatus,
)


# Register your models here.
class ADPCredentialsAdmin(admin.ModelAdmin):
    class Meta:
        fields = "__all__"


class ADPStatusAdmin(admin.ModelAdmin):

    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }

    class Meta:
        fields = "__all__"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ["processed_indicators", "partial_indicators"]:
            kwargs["queryset"] = ADPIndicator.objects.select_related("entity", "type")
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class ADPSoftwareAdmin(admin.ModelAdmin):
    class Meta:
        fields = "__all__"


class ADPIndicatorTypeAdmin(admin.ModelAdmin):
    class Meta:
        fields = "__all__"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("questions")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "questions":
            kwargs["queryset"] = Question.objects.select_related("subcategory")
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class ADPIndicatorAdmin(admin.ModelAdmin):
    class Meta:
        fields = "__all__"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("entity", "type")


class ADPFieldAdmin(admin.ModelAdmin):
    class Meta:
        fields = "__all__"


class ADPFieldMappingAdmin(admin.ModelAdmin):
    class Meta:
        fields = "__all__"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "field_value":
            kwargs["queryset"] = ADPFieldValue.objects.select_related("field")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(ADPCredentials, ADPCredentialsAdmin)
admin.site.register(ADPStatus, ADPStatusAdmin)
admin.site.register(ADPSoftware, ADPSoftwareAdmin)
admin.site.register(ADPIndicatorType, ADPIndicatorTypeAdmin)
admin.site.register(ADPIndicator, ADPIndicatorAdmin)
admin.site.register(ADPField, ADPFieldAdmin)
admin.site.register(ADPFieldMapping, ADPFieldMappingAdmin)
