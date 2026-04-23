from django import forms

from act.models import Solution, SolutionKeyword

from scoring.models import Category, SubCategory, MAIN_CATEGORIES_SLUGS
from mixity.models import Language
from django.utils.translation import ugettext_lazy as _


class SolutionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SolutionForm, self).__init__(*args, **kwargs)
        # Multiple choices fields
        self.fields["categories"] = forms.ModelMultipleChoiceField(
            queryset=Category.objects.filter(slug__in=MAIN_CATEGORIES_SLUGS),
            required=True,
            widget=forms.CheckboxSelectMultiple(),
            label="Catégories",
        )
        self.fields["subcategories"] = forms.ModelMultipleChoiceField(
            queryset=SubCategory.objects.filter(category__slug="all"),
            required=True,
            widget=forms.CheckboxSelectMultiple(),
            label="Sous-catégories",
        )
        self.fields["languages"] = forms.ModelMultipleChoiceField(
            queryset=Language.objects.all(),
            required=True,
            widget=forms.CheckboxSelectMultiple(),
            label="Langues",
        )
        self.fields["keywords"] = forms.ModelMultipleChoiceField(
            queryset=SolutionKeyword.objects.all(),
            required=True,
            widget=forms.CheckboxSelectMultiple(),
            label="Mots-clés",
        )

    class Meta:
        model = Solution
        fields = [
            "title",
            "summary",
            "photo",
            "referent",
            "email",
            "country",
            "region",
            "categories",
            "subcategories",
            "description",
            "languages",
            "price_desc",
            "keywords",
        ]

    def save(self, commit=True):
        solution = super().save()
        # duplicate txt in all language for searching in whatever the website language selected
        solution.title_en = solution.title
        solution.title_es = solution.title
        solution.title_fr = solution.title

        solution.description_en = solution.description
        solution.description_es = solution.description
        solution.description_fr = solution.description

        solution.summary_en = solution.summary
        solution.summary_es = solution.summary
        solution.summary_fr = solution.summary
        solution.save()
        return solution
