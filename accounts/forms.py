from captcha.fields import ReCaptchaField
from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.core.validators import RegexValidator
from django.forms import ModelForm
from django.urls import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from django.utils.safestring import mark_safe
from address.widgets import AddressWidget
from address.forms import AddressField
from accounts.models import Structure, MixityUser, DiversityLabel, BusinessLine, Entity
from scoring.models import (
    QuestionSheetType,
    Evaluation,
    get_filtered_human_campus_slugs,
)
from address.models import Address
from localflavor.fr.forms import FRSIRETField
from subscriptions.models import SubscriptionType, Coupon, Product
import sys
from accounts.vocabularies import (
    BOOLEANS_ELEMENTS,
    AGE_CHOICES,
    CIVILITY_CHOICES,
    CAMPUS_CHOICE,
)
from django.core.exceptions import ValidationError
from mixity.utils import deep_getattr
from accounts.vocabularies import EUROPEAN_COUNTRY_CODE
from django.db.models import Q


if sys.version > "3":
    long = int
    basestring = (str, bytes)
    unicode = str


phone_regex = RegexValidator(
    regex=r"^(\+|00)?[-\d ]{6,20}$",
    message=_(
        "Votre numéro de téléphone ne doit comporter que des chiffres, tirets ou espacements sur moins de 22 caractères."
    ),
)

duns_regex = RegexValidator(
    regex=r"^\d{9}$",
    message=_("Votre numéro DUNS doit comporter 9 chiffres."),
)

tva_intracom_regex = RegexValidator(
    regex=r"^[0-9A-Z]{4,15}$",
    message=_(
        "Votre numéro de TVA intracommunautaire doit faire entre 4 et 15 caractères, et ne comporter que des chiffres et majuscules."
    ),
)

website_regex = RegexValidator(
    regex=r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()!@:%_\+.~#?&\/\/=]*)$",
    message=_("Votre URL n'est pas valide."),
)


class TempAddressWidget(AddressWidget):
    """
    Temp fixing until thoses issues are fixed
    - https://github.com/furious-luke/django-address/issues/89
    - https://github.com/furious-luke/django-address/issues/86
    """

    def render(self, name, value, attrs=None, **kwargs):
        if value in (None, ""):
            ad = {}
        elif isinstance(value, dict):
            ad = value
        elif isinstance(value, (int, long)):
            ad = Address.objects.get(pk=value)
            ad = ad.as_dict()
        else:
            ad = value.as_dict()
        elems = [
            super(AddressWidget, self).render(
                name, escape(ad.get("formatted", "")), attrs, **kwargs
            ),
            '<div id="%s_components">' % name,
        ]

        # Now add the hidden fields.
        for com in self.components:
            elems.append(
                '<input type="hidden" name="%s_%s" data-geo="%s" value="%s" />'
                % (name, com[0], com[1], escape(ad.get(com[0], "")))
            )
        elems.append("</div>")

        return mark_safe(unicode("\n".join(elems)))


class DateInput(forms.DateInput):
    input_type = "date"


class PhoneInput(forms.TextInput):
    input_type = "tel"


class StructureFormClass(forms.ModelForm):
    class Meta:
        model = Structure
        fields = [
            "juridic_name",
            "commercial_name",
            "category",
            "logo",
            "workforce",
            "business_line",
            "secondary_business_lines",
            "turnover_value",
            "siret",
            "duns",
            "num_tva_intracom",
            "creation_year",
            "address",
            "website",
            "phone1",
            "phone2",
            "phone3",
        ]

    address = AddressField(widget=TempAddressWidget, label=_("Adresse"))
    phone1 = forms.CharField(
        widget=PhoneInput, validators=[phone_regex], label=_("Téléphone Fixe")
    )
    phone2 = forms.CharField(
        widget=PhoneInput, validators=[phone_regex], label=_("Téléphone Mobile")
    )
    siret = FRSIRETField(required=False, label="SIRET")
    duns = forms.CharField(
        required=False, validators=[duns_regex], label=_("Numéro DUNS")
    )
    business_line = forms.ModelChoiceField(
        queryset=BusinessLine.objects.filter(is_private=False),
        required=True,
        label=_("Secteurs d'activité"),
    )
    secondary_business_lines = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        queryset=BusinessLine.objects.filter(is_private=False),
        required=False,
        label=_("Secteurs d'activité secondaire"),
    )
    num_tva_intracom = forms.CharField(
        required=False,
        validators=[tva_intracom_regex],
        label=_("Numéro de TVA intracommunautaire"),
    )
    website = forms.CharField(
        required=True, validators=[website_regex], label=_("Site Web")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["website"].widget.attrs.update(
            placeholder="https://www.mywebsite.com"
        )
        if self.instance.business_line not in self.fields["business_line"].queryset:
            self.fields["business_line"].queryset = BusinessLine.objects.filter(
                Q(is_private=False) | Q(name=self.instance.business_line)
            )
        self.fields["website"].initial = "https://"
        if self.instance.address_id:
            self.fields["address"].initial = str(
                Address.objects.get(pk=self.instance.address_id)
            )

    def clean_address(self):
        address = self.cleaned_data.get("address")
        if deep_getattr(address, "locality.state.country", None) is None:
            raise ValidationError(
                _(
                    "Veuillez valider votre adresse en sélectionnant un choix, celle-ci doit comporter un pays."
                )
            )
        return address


class EntityFormClass(forms.ModelForm):
    class Meta:
        model = Entity
        fields = ["name", "creation_year", "workforce", "address", "phone"]

    address = AddressField(widget=TempAddressWidget, label=_("Adresse"))
    phone = forms.CharField(
        widget=PhoneInput, validators=[phone_regex], label=_("Téléphone")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.address_id:
            self.fields["address"].initial = str(
                Address.objects.get(pk=self.instance.address_id)
            )

    def clean_address(self):
        address = self.cleaned_data.get("address")
        if deep_getattr(address, "locality.state.country", None) is None:
            raise ValidationError(
                _(
                    "Veuillez valider votre adresse en sélectionnant un choix, celle-ci doit comporter un pays."
                )
            )
        return address


class MixityUserFormClass(forms.ModelForm):
    class Meta:
        model = MixityUser
        fields = [
            "foto",
            "gender",
            "first_name",
            "last_name",
            "phone",
            "job",
        ]

    phone = forms.CharField(
        widget=PhoneInput, validators=[phone_regex], label=_("Téléphone")
    )


class MixityUserOrgaFormClass(forms.ModelForm):
    class Meta:
        model = MixityUser
        fields = [
            "foto",
            "gender",
            "first_name",
            "last_name",
            "job",
        ]


class StructureStartTrialFormClass(forms.ModelForm):
    class Meta:
        model = Structure
        fields = [
            "juridic_name",
            "business_line",
            "workforce",
            "address",
            "phone1",
        ]

    address = AddressField(widget=TempAddressWidget, label=_("Adresse"))
    business_line = forms.ModelChoiceField(
        queryset=BusinessLine.objects.filter(is_private=False),
        required=True,
        label=_("Secteurs d'activité"),
    )
    phone1 = forms.CharField(
        widget=PhoneInput, validators=[phone_regex], label=_("Téléphone Fixe")
    )
    tag_to_allow = forms.ChoiceField(
        choices=[
            ("gender", _("Égalité entre les femmes et les hommes")),
            ("disability", _("Handicap")),
        ],
        label=_("Essayez gratuitement Mixity start sur une dimension"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone1"].label = _("Numéro de téléphone")
        self.fields["juridic_name"].label = _("Nom de l'entreprise (juridique)")
        self.fields["workforce"].label = _("Nombre d'employés (f/h/nb)")

    def clean_address(self):
        address = self.cleaned_data.get("address")
        if deep_getattr(address, "locality.state.country", None) is None:
            raise ValidationError(
                _(
                    "Veuillez valider votre adresse en sélectionnant un choix, celle-ci doit comporter un pays."
                )
            )
        return address


class StructureStartPursueTrialFormClass(forms.ModelForm):
    class Meta:
        model = Structure
        fields = [
            "category",
            "logo",
            "turnover_value",
            "website",
            "siret",
            "duns",
            "num_tva_intracom",
        ]

    siret = FRSIRETField(required=True, label=_("SIRET"))
    duns = forms.CharField(
        required=True, validators=[duns_regex], label=_("Numéro DUNS")
    )
    num_tva_intracom = forms.CharField(
        required=True, label=_("Numéro de TVA intracommunautaire")
    )

    def adapt_to_country(self, country):
        if not country:
            return
        if country.code == "FR":
            del self.fields["duns"]
            del self.fields["num_tva_intracom"]
        elif country.code in EUROPEAN_COUNTRY_CODE:
            del self.fields["duns"]
            del self.fields["siret"]
        else:
            del self.fields["num_tva_intracom"]
            del self.fields["siret"]


class StructureClientOrSolverFormClass(forms.Form):
    structure_type = forms.ChoiceField(
        choices=[
            ("client", _("Devenir client")),
            ("solver", _("Devenir solutionneur")),
        ],
        label=_("Quel type de structure voulez vous devenir?"),
    )


class StructureInfoFormClass(forms.ModelForm):
    class Meta:
        model = Structure
        fields = [
            "juridic_name",
            "commercial_name",
            "category",
            "logo",
            "address",
            "phone1",
            "phone2",
            "business_line",
        ]

    address = AddressField(widget=TempAddressWidget, label=_("Adresse"))
    business_line = forms.ModelChoiceField(
        queryset=BusinessLine.objects.filter(is_private=False),
        required=True,
        label=_("Secteurs d'activité"),
    )
    phone1 = forms.CharField(
        widget=PhoneInput, validators=[phone_regex], label=_("Téléphone Fixe")
    )
    phone2 = forms.CharField(
        widget=PhoneInput, validators=[phone_regex], label=_("Téléphone Mobile")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.address_id:
            self.fields["address"].initial = str(
                Address.objects.get(pk=self.instance.address_id)
            )

    def clean_address(self):
        address = self.cleaned_data.get("address")
        if deep_getattr(address, "locality.state.country", None) is None:
            raise ValidationError(
                _(
                    "Veuillez valider votre adresse en sélectionnant un choix, celle-ci doit comporter un pays."
                )
            )
        return address


class StructureBusinessFormClass(forms.ModelForm):
    class Meta:
        model = Structure
        fields = [
            "creation_year",
            "workforce",
            "turnover_value",
            "siret",
            "duns",
            "num_tva_intracom",
        ]

    siret = FRSIRETField(required=True, label=_("SIRET"))
    duns = forms.CharField(
        required=True, validators=[duns_regex], label=_("Numéro DUNS")
    )
    num_tva_intracom = forms.CharField(
        required=True, label=_("Numéro de TVA intracommunautaire")
    )

    def adapt_to_country(self, country):
        if not country:
            return
        if country.code == "FR":
            del self.fields["duns"]
            del self.fields["num_tva_intracom"]
        elif country.code in EUROPEAN_COUNTRY_CODE:
            del self.fields["duns"]
            del self.fields["siret"]
        else:
            del self.fields["num_tva_intracom"]
            del self.fields["siret"]


class StructureDetailFormClass(forms.ModelForm):
    class Meta:
        model = Structure
        fields = [
            "website",
            "description",
        ]

    website = forms.CharField(
        required=True, validators=[website_regex], label=_("Site Web")
    )


class StructureOfferPreFormClass(forms.Form):
    product = forms.ModelChoiceField(
        label=_("Choisissez une offre"),
        queryset=Product.objects.filter(
            Q(slug="human") | Q(slug="diag"), is_active=True
        ),
    )

    def __init__(self, *args, **kwargs):
        super(StructureOfferPreFormClass, self).__init__(*args, **kwargs)


class StructureOfferFormClass(forms.Form):
    product = forms.ModelChoiceField(
        label=_("Choisissez une offre"),
        queryset=Product.objects.filter(~Q(slug="human"), is_active=True),
    )
    coupon = forms.CharField(
        required=False, label=_("Code de réduction"), max_length=32
    )

    def __init__(self, *args, **kwargs):
        super(StructureOfferFormClass, self).__init__(*args, **kwargs)
        for elem in BOOLEANS_ELEMENTS:
            self.fields["boolean_" + elem[0]] = forms.BooleanField(
                label=elem[1], required=False
            )

    def is_valid(self):
        is_valid = super().is_valid()
        coupon = self.data.get("OfferForm-coupon")
        if coupon:
            coupon = Coupon.objects.filter(code=coupon).first()
            if coupon and coupon.is_valid and is_valid:
                return True
            else:
                self.errors["coupon"] = _("Le code de réduction n'est pas valide")
                return False
        return is_valid

    def adapt_to_country(self, country):
        if not country:
            return
        if country.code != "FR":
            self.fields["product"].queryset = Product.objects.filter(
                ~Q(slug="human") & ~Q(slug="diag"), is_active=True
            )


class StructureTagPreFormClass(forms.Form):
    tag_choice = forms.ChoiceField(
        label=_("Vous souhaitez être évalué sur..."),
        choices=(
            ("1", _("Les 5 dimensions de la Diversité et de l’Inclusion (recommandé)")),
            ("2", _("Plusieurs dimensions au choix (minimum 3)")),
            (
                "3",
                _(
                    "Une seule dimension au choix (égalité f/h/nb, handicap, multiculturel…)"
                ),
            ),
        ),
    )


class StructureOneTagFormClass(forms.Form):
    tag_choice = forms.ChoiceField(
        label=_("Vous souhaitez être évalué sur..."),
        choices=(
            (
                "no_gender",
                _("L’égalité professionnelle entre les femmes et les hommes"),
            ),
            ("no_disability", _("Le handicap")),
            ("no_ethnicity", _("Les origines sociales et ethniques")),
            ("no_generations", _("Les âges et générations")),
            ("no_lgbt", _("L’orientation sexuelle et/ou identité de genre")),
        ),
    )


def minimum_tag(value):
    if len(value) < 3:
        raise forms.ValidationError("vous devez sélectionner au moins 3 choix")


class StructureMultipleTagFormClass(forms.Form):
    tag_choice = forms.MultipleChoiceField(
        label=_("Vous souhaitez être évalué sur..."),
        choices=(
            (
                "no_gender",
                _("L’égalité professionnelle entre les femmes et les hommes"),
            ),
            ("no_disability", _("Le handicap")),
            ("no_ethnicity", _("Les origines sociales et ethniques")),
            ("no_generations", _("Les âges et générations")),
            ("no_lgbt", _("L’orientation sexuelle et/ou identité de genre")),
        ),
        widget=forms.CheckboxSelectMultiple,
        validators=[minimum_tag],
    )


class StructureSheetFormClass(forms.Form):
    question_sheet_type = forms.ModelChoiceField(
        label=_("Choisissez un référenciel d'évaluation"),
        queryset=QuestionSheetType.objects.all(),
    )


class StructurePublicFormClass(forms.ModelForm):
    class Meta:
        model = Structure
        fields = [
            "description",
            "commitment",
        ]


class StructurePublicHumanFormClass(forms.ModelForm):
    class Meta:
        model = Structure
        fields = [
            "description",
            "human_description",
            "commitment",
        ]


class StructureMembersForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Email du collaborateur à ajouter",
        help_text=_("Ajouter un nouveau collaborateur à cette structure"),
    )

    class Meta:
        model = Structure
        fields = ()


class ContactForm(forms.Form):
    from_email = forms.EmailField(label=_("Adresse email"), required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
    last_name = forms.CharField(label=_("Nom"), required=True)
    first_name = forms.CharField(label=_("Prénom"), required=True)
    society = forms.CharField(label=_("Entreprise"), required=False)
    phone_number = forms.CharField(
        label=_("Numéro de téléphone"), validators=[phone_regex], required=True
    )
    captcha = ReCaptchaField()


class MixityUserCreationForm(UserCreationForm):
    captcha = ReCaptchaField()
    validate_cgu = forms.BooleanField(
        label=mark_safe(
            "<a href={}>{}</a>".format(
                "/home", _("Accepter les conditions d'utilisation")
            )
        ),
        required=True,
    )

    class Meta:
        model = MixityUser
        fields = ("email", "password1", "password2")
        error_messages = {
            "email": {
                "unique": _("Cette adresse est déjà utilisée."),
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["validate_cgu"].label = mark_safe(
            "{} <a href={}>{}</a>".format(
                _("J'accepte les"),
                ("https://mixity.io/cgu"),
                _("conditions générales d'utilisation"),
            )
        )


class CollaboratorCriteriaChoiceForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = []

    def __init__(self, evaluation, *args, **kwargs):
        self.evaluation = evaluation
        self.target = kwargs.pop("target")
        human_filter = None
        if "human_filter" in kwargs:
            human_filter = kwargs.pop("human_filter", None)
        super().__init__(*args, **kwargs)
        self.fields["civility"] = forms.MultipleChoiceField(
            choices=CIVILITY_CHOICES,
            required=False,
            widget=forms.CheckboxSelectMultiple(),
        )
        self.fields["age"] = forms.MultipleChoiceField(
            choices=AGE_CHOICES,
            required=False,
            widget=forms.CheckboxSelectMultiple(),
        )
        if self.evaluation and self.evaluation.is_campus:
            self.fields["status"] = forms.MultipleChoiceField(
                choices=CAMPUS_CHOICE,
                required=False,
                widget=forms.CheckboxSelectMultiple(),
            )
        if self.evaluation:
            for criteria in self.evaluation.human_criteria.all():
                self.fields[criteria.label] = forms.ModelMultipleChoiceField(
                    queryset=criteria.choices.all(),
                    required=False,
                    widget=forms.CheckboxSelectMultiple(),
                )
        # Used to check the value corresponding to human_filter in the form widget
        if human_filter:
            # Human Classic
            if self.evaluation.is_human and not self.evaluation.is_campus:
                self.fields["civility"].initial = [human_filter]
            # Human Campus
            elif self.evaluation.is_human and self.evaluation.is_campus:
                filters = get_filtered_human_campus_slugs(human_filter)
                self.fields["status"].initial = filters


class PasswordResetConfirmForm(SetPasswordForm, ModelForm):
    class Meta:
        model = MixityUser
        fields = ["first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = self.user
        if not self.instance:
            return
        if not self.user.has_usable_password():
            self.fields["accept_cgu"] = forms.BooleanField(
                required=True,
                validators=[lambda x: x],
                label=mark_safe(
                    _("En cochant cette case vous acceptez les")
                    + " <a target='_blank' href='"
                    + reverse_lazy("cgu")
                    + "'>"
                    + _("CGU</a> du site")
                ),
            )
        else:
            del self.fields["first_name"]
            del self.fields["last_name"]
