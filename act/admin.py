from django.contrib import admin
from act.models import (
    Solver,
    SolutionKeyword,
    Solution,
    SolutionAttachment,
    BestPractice,
    BestPracticePublic,
    BestPracticeType,
    BestPracticeKeyword,
    BestPracticeOrganizationType,
    BestPracticeSize,
    Elearning,
    ElearningKeyword,
    ElearningEvaluationMethod,
    ElearningNotion,
)
from scoring.models import SubCategory
from django import forms
from django.db.models import Count
from mixity.admin import MixityAdmin
from tinymce.widgets import TinyMCE
from modeltranslation.admin import TranslationAdmin
from accounts.models import MixityUser


def validate_evaluation(modeladmin, request, queryset):
    for solver in queryset:
        solver.do_admin_validation()


validate_evaluation.short_description = "Valider les solutionneurs selectionnées"


class SolutionInline(admin.TabularInline):
    model = Solution
    can_delete = False
    extra = 0
    verbose_name = "Solution"
    show_change_link = True
    fields = ("title", "modification_date", "categories", "subcategories")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class SolverAdmin(admin.ModelAdmin):
    readonly_fields = ["inscription_date"]
    list_display = ["structure", "inscription_date", "is_validated_by_admin"]
    inlines = [SolutionInline]

    actions = [validate_evaluation]


class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(SolutionForm, self).__init__(*args, **kwargs)
        self.fields["description_fr"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["price_desc_fr"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["public_fr"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["objective_fr"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )
        self.fields["format_session_fr"].widget = TinyMCE(
            attrs={"cols": 2, "rows": 2, "height": 200}
        )


class SolutionAdmin(TranslationAdmin):
    form = SolutionForm
    search_fields = ["title", "solver__structure__juridic_name"]
    list_display = [
        "title",
        "solver",
        "tracked_count",
        "tracked_contact_count",
        "creation_date",
        "modification_date",
    ]
    filter_horizontal = (
        "categories",
        "subcategories",
        "languages",
        "keywords",
        "solution_formats",
        "users_tracked",
        "users_tracked_contact",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            tracked_count=Count("users_tracked"),
            tracked_contact_count=Count("users_tracked"),
        )
        return queryset

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "users_tracked":
            kwargs["queryset"] = Solution.objects.get(
                pk=request.resolver_match.kwargs["object_id"]
            ).users_tracked.all()
        if db_field.name == "users_tracked_contact":
            kwargs["queryset"] = Solution.objects.get(
                pk=request.resolver_match.kwargs["object_id"]
            ).users_tracked_contact.all()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def tracked_count(self, obj):
        return obj.users_tracked.count()

    tracked_count.short_description = "Vues"

    def tracked_contact_count(self, obj):
        return obj.users_tracked_contact.count()

    tracked_contact_count.short_description = "Prises de contact"

    class Meta:
        fields = "__all__"


class SolutionKeywordAdmin(admin.ModelAdmin):
    list_display = ["label"]


class BestPracticeAdmin(admin.ModelAdmin):

    list_display = ["label", "structure", "referent"]
    filter_horizontal = (
        "categories",
        "subcategories",
        "publics",
        "keywords",
        "type",
        "organization_type",
        "size",
    )


class BestPracticePublicAdmin(admin.ModelAdmin):
    list_display = ["slug", "label"]


class BestPracticeSizeAdmin(admin.ModelAdmin):
    list_display = ["slug", "label"]


class BestPracticeTypeAdmin(admin.ModelAdmin):
    list_display = ["slug", "label"]


class BestPracticeKeywordAdmin(admin.ModelAdmin):
    list_display = ["slug", "label"]


class BestPracticeOrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ["slug", "label"]


class ElearningAdmin(admin.ModelAdmin):
    list_display = ["slug", "title"]


class ElearningKeywordAdmin(admin.ModelAdmin):
    list_display = ["slug", "label"]


class ElearningEvaluationMethodAdmin(admin.ModelAdmin):
    list_display = ["slug", "label"]


class ElearningNotionAdmin(admin.ModelAdmin):
    list_display = ["slug", "label"]


admin.site.register(Solver, SolverAdmin)
admin.site.register(SolutionKeyword, SolutionKeywordAdmin)
admin.site.register(Solution, SolutionAdmin)
admin.site.register(SolutionAttachment)
admin.site.register(BestPractice, BestPracticeAdmin)
admin.site.register(BestPracticePublic, BestPracticePublicAdmin)
admin.site.register(BestPracticeType, BestPracticeTypeAdmin)
admin.site.register(BestPracticeKeyword, BestPracticeKeywordAdmin)
admin.site.register(BestPracticeOrganizationType, BestPracticeOrganizationTypeAdmin)
admin.site.register(BestPracticeSize, BestPracticeSizeAdmin)
admin.site.register(Elearning, ElearningAdmin)
admin.site.register(ElearningNotion, ElearningNotionAdmin)
admin.site.register(ElearningEvaluationMethod, ElearningEvaluationMethodAdmin)
admin.site.register(ElearningKeyword, ElearningKeywordAdmin)
