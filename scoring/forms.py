from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from accounts.models import Structure, DiversityLabel, BusinessLine
from mixity import settings
from scoring.models import (
    Evaluation,
    ScoreCategory,
    Action,
)
from subscriptions.models import Subscription
from accounts.vocabularies import (
    REGIONS_CHOICES,
    CURRENCY_CHOICES,
)


class EvaluationSearchForm(forms.Form):
    search = forms.CharField(
        label=_("Champ de recherche"),
        max_length=256,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Rechercher une empreinte"),
                "aria-label": _("Rechercher une empreinte"),
                "type": "search",
                "class": "form-control",
                "style": "min-width: 210px; border-radius: 2.5em 0 0 2.5em; background-color: transparent;",
            }
        ),
    )


class EvaluationComparisonForm(forms.Form):
    search = forms.CharField(
        label=_("Champ de recherche"),
        max_length=256,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Rechercher une empreinte"),
                "style": "border-radius: 2.5em 0 0 2.5em",
            }
        ),
    )
    business_line = forms.ModelChoiceField(
        label=_("Secteur d'activité"),
        queryset=BusinessLine.objects.all(),
        required=False,
    )
    region = forms.ChoiceField(
        label=_("Région"),
        choices=REGIONS_CHOICES + (("", _("Choisissez une région")),),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.base_fields = self.base_fields.copy()
        self.base_fields["business_line"] = forms.ModelChoiceField(
            label=_("Secteur d'activité"),
            queryset=BusinessLine.objects.all(),
            required=False,
            empty_label=_("Choisissez un secteur d'activité"),
            widget=forms.Select(
                attrs={
                    "style": "border-radius: 2.5em 0 0 2.5em",
                }
            ),
        )
        from address.models import State

        self.base_fields["region"] = forms.ModelChoiceField(
            label=_("Région"),
            queryset=State.objects.all(),
            required=False,
            widget=forms.Select(
                attrs={
                    "style": "border-radius: 2.5em 0 0 2.5em",
                }
            ),
        )

        super().__init__(*args, **kwargs)


class EvaluationCreationForm(forms.Form):
    # Nothing is done here because now we create all evaluations for several entities at the same time in the form_valid
    """ """


class EvaluationFillForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.subcategory = kwargs.pop("subcategory")
        self.category = kwargs.pop("category")
        self.evaluation = kwargs.pop("evaluation")
        self.target = kwargs.pop("target")
        self.page = kwargs.pop("page")
        self.questions = kwargs.pop("questions")
        self.base_fields = self.base_fields.copy()

        # order questions according to the GSheet doc
        elems = self.questions
        elems.sort(key=lambda elem: elem.order_num)

        needs_labels_question = False
        have_children = self.evaluation.entity.children_entities.exists()

        for elem in elems:
            sheets_id = elem.google_sheets_id

            if (
                self.evaluation.sheet.slug == "mixity_evaluation_diag"
                and have_children
                and not elem.display_custom_question_label
            ):
                blocked_aggregation_field = forms.BooleanField(
                    label=_("Bloquer l'agrégation"),
                    required=False,
                )
                self.base_fields[f"question_{str(elem.id)}_blocked_aggregation"] = (
                    blocked_aggregation_field
                )
            if elem.display_not_applicable:
                not_applicable_field = forms.BooleanField(
                    label=_("Non applicable"), required=False
                )
                self.base_fields[f"question_{str(elem.id)}_not_applicable"] = (
                    not_applicable_field
                )
            if elem.is_indicator:
                indicator_not_followed_field = forms.BooleanField(
                    label=_("Cet indicateur n'est pas suivi"), required=False
                )
                self.base_fields[f"question_{str(elem.id)}_indicator_not_followed"] = (
                    indicator_not_followed_field
                )

            if elem.display_custom_question_label:
                custom_question_label_field = forms.CharField(
                    label=_("Libellé"),
                    max_length=360,
                    required=False,
                    widget=forms.TextInput(attrs={"placeholder": _("Libellé")}),
                )
                self.base_fields[f"question_{str(elem.id)}_custom_question_label"] = (
                    custom_question_label_field
                )

            if sheets_id in [1, 2020001, 20214001, 20215015]:
                needs_labels_question = True

            if "subquestions" in elem.type:
                first = True
                field = None
                has_prefix = False
                sqs = elem.subquestions.all()
                for sq in sqs:
                    if "pourcentage" in sq.ui_type:
                        if not "novalidator" in sq.ui_type:
                            validators = [
                                MaxValueValidator(100),
                                MinValueValidator(0),
                            ]
                        else:
                            validators = []
                        field = forms.FloatField(
                            label=sq.label_html,
                            required=False,
                            help_text=elem.help_text,
                            validators=validators,
                        )
                        if not "novalidator" in sq.ui_type:
                            field.widget.attrs["min"] = 0
                            field.widget.attrs["max"] = 100
                            field.widget.attrs["class"] = "sub_pourcentage"
                        field.is_percentage = True
                        if first:
                            field.prefix = True
                            has_prefix = True
                    elif "valeur" in sq.ui_type:
                        field = forms.FloatField(
                            label=sq.label_html,
                            help_text=elem.help_text,
                            required=False,
                        )
                        if first:
                            field.prefix = True
                            has_prefix = True
                    elif "multiple_qcm" in sq.ui_type:
                        field = forms.BooleanField(label=sq.label_html, required=False)
                        field.ui_type = "multiple_qcm"
                    if first:
                        self.base_fields[f"question_{str(elem.id)}_maintitle"] = (
                            forms.Field(
                                label=elem.label_html,
                                help_text=elem.help_text,
                                required=False,
                            )
                        )
                    first = False
                    field.suffix = False
                    self.base_fields[f"question_{str(elem.id)}_sub_{str(sq.id)}"] = (
                        field
                    )
                if has_prefix:
                    field.suffix = True
            else:
                if "pourcentage" in elem.type:
                    field = forms.FloatField(
                        label=elem.label_html,
                        required=False,
                        help_text=elem.help_text,
                    )
                    field.is_percentage = True
                    if "croissance" in elem.label or "croissance" in elem.type:
                        field.validators = []
                    else:
                        field.validators = [
                            MinValueValidator(0),
                            MaxValueValidator(100),
                        ]
                        field.widget.attrs["min"] = 0
                        field.widget.attrs["max"] = 100

                elif "valeur" in elem.type:
                    field = forms.FloatField(
                        label=elem.label_html,
                        help_text=elem.help_text,
                        required=False,
                    )
                elif "date" in elem.type:
                    field = forms.DateField(
                        label=elem.label_html,
                        help_text=elem.help_text,
                        required=False,
                        widget=forms.DateInput(attrs={"type": "date"}),
                    )
                elif "libre" in elem.type:
                    field = forms.CharField(
                        widget=forms.Textarea,
                        label=elem.label_html,
                        help_text=elem.help_text,
                        required=False,
                    )
                    field.widget.attrs["rows"] = 2
                elif "text" in elem.type:
                    field = forms.CharField(
                        widget=forms.Textarea,
                        label=elem.label_html,
                        help_text=elem.help_text,
                        required=False,
                    )
                    field.widget.attrs["rows"] = 4
                elif elem.choices.exists():
                    field = forms.ModelChoiceField(
                        label=elem.label_html,
                        help_text=elem.help_text,
                        queryset=elem.choices.all(),
                        required=False,
                        empty_label=None,
                        widget=forms.RadioSelect,
                    )
                self.base_fields[f"question_{str(elem.id)}"] = field
                if "currency" in elem.type:
                    currency_field = forms.ChoiceField(choices=CURRENCY_CHOICES)
                    currency_field.widget.attrs["style"] = "width:64px"
                    self.base_fields[f"question_{str(elem.id)}_currency"] = (
                        currency_field
                    )
                    field.currency_field = True

            if elem.ask_detail:
                detail_field = forms.CharField(
                    label=_("Commentaire"),
                    max_length=720,
                    required=False,
                    widget=forms.Textarea(attrs={"rows": 2}),
                )
                self.base_fields[f"question_{str(elem.id)}_detail"] = detail_field

            if needs_labels_question:
                self.base_fields["questionnaire_labels"] = (
                    forms.ModelMultipleChoiceField(
                        queryset=DiversityLabel.objects.all(),
                        required=False,
                        widget=forms.CheckboxSelectMultiple(),
                        label=_("Labels et certifications"),
                    )
                )
                needs_labels_question = False

        super().__init__(*args, **kwargs)


class EvaluationConfirmForm(forms.Form):
    """ """


class EvaluationCategoryConfirmForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ()

    def __init__(self, *args, **kwargs):
        questions = {
            "all": {
                "detail": _(
                    "Avez-vous mis en place d'autres actions au sein de votre organisation pour encourager la diversité et l'inclusion de manière globale ?"
                ),
                "aim": _(
                    "Quels sont les grands objectifs que vous souhaitez atteindre dans les 1 à 3 ans (de manière globale sur la diversité et l'inclusion) ?"
                ),
            },
            "gender": {
                "detail": _(
                    "Avez-vous mis en place d'autres modes d'actions au sein de votre organisation ?"
                ),
                "aim": _(
                    "Quels sont les grands objectifs que vous souhaitez atteindre dans les 1 à 3 ans (spécifiquement sur le sujet de l'égalité professionnelle entre les femmes et les hommes) ?"
                ),
            },
            "disability": {
                "detail": _(
                    "Avez-vous mis en place d'autres modes d'actions au sein de votre organisation ?"
                ),
                "aim": _(
                    "Quels sont les grands objectifs que vous souhaitez atteindre dans les 1 à 3 ans (spécifiquement sur le sujet du handicap) ?"
                ),
            },
            "cultural_diversity": {
                "detail": _(
                    "Avez-vous mis en place d'autres modes d'actions au sein de votre organisation ?"
                ),
                "aim": _(
                    "Quels sont les grands objectifs que vous souhaitez atteindre dans les 1 à 3 ans (spécifiquement sur le sujet de la diversité d'origine ethnique et/ou sociale) ?"
                ),
            },
            "generational_diversity": {
                "detail": _(
                    "Avez-vous mis en place d'autres modes d'actions au sein de votre organisation ?"
                ),
                "aim": _(
                    "Quels sont les grands objectifs que vous souhaitez atteindre dans les 1 à 3 ans (spécifiquement sur le sujet des âges) ?"
                ),
            },
            "lgbt": {
                "detail": _(
                    "Avez-vous mis en place d'autres modes d'actions au sein de votre organisation ?"
                ),
                "aim": _(
                    "Quels sont les grands objectifs que vous souhaitez atteindre dans les 1 à 3 ans (spécifiquement sur le sujet LGBTQIA+) ?"
                ),
            },
            "csrd": {
                "detail": _(
                    "Avez-vous mis en place d'autres modes d'actions au sein de votre organisation ?"
                ),
                "aim": _(
                    "Quels sont les grands objectifs que vous souhaitez atteindre dans les 1 à 3 ans (spécifiquement sur le sujet CSRD) ?"
                ),
            },
        }
        self.category = kwargs.pop("category")
        super().__init__(*args, **kwargs)
        self.fields["detail_label"] = forms.Field(
            label=questions[self.category.slug]["detail"], required=False
        )

        for i in range(0, settings.DEFAULT_ACTION_ROW_NUMBER):
            self.fields["intitules_detail_" + str(i)] = forms.CharField(
                widget=forms.Textarea, max_length=700, required=False
            )
            self.fields["intitules_detail_" + str(i)].col = 0
            self.fields["intitules_detail_" + str(i)].widget.attrs["rows"] = 3
            self.fields["descriptif_detail_" + str(i)] = forms.CharField(
                widget=forms.Textarea, max_length=700, required=False
            )
            self.fields["descriptif_detail_" + str(i)].col = 1
            self.fields["descriptif_detail_" + str(i)].widget.attrs["rows"] = 3

        self.fields["aim_label"] = forms.Field(
            label=questions[self.category.slug]["aim"], required=False
        )

        for i in range(0, settings.DEFAULT_ACTION_ROW_NUMBER):
            self.fields["intitules_aim_" + str(i)] = forms.CharField(
                widget=forms.Textarea, max_length=700, required=False
            )
            self.fields["intitules_aim_" + str(i)].col = 0
            self.fields["intitules_aim_" + str(i)].widget.attrs["rows"] = 3
            self.fields["descriptif_aim_" + str(i)] = forms.CharField(
                widget=forms.Textarea, max_length=700, required=False
            )
            self.fields["descriptif_aim_" + str(i)].col = 1
            self.fields["descriptif_aim_" + str(i)].widget.attrs["rows"] = 3

        self.fields["intitules_detail_0"].array_prefix = True
        self.fields["descriptif_detail_4"].array_suffix = True
        self.fields["intitules_aim_0"].array_prefix = True
        self.fields["descriptif_aim_4"].array_suffix = True
