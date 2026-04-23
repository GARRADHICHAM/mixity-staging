from django import forms
from subscriptions.models import SubscriptionOption, Product
from django.utils.translation import ugettext_lazy as _


class SubscriptionForm(forms.ModelForm):
    subscription_type = forms.ModelChoiceField(
        label=_("Choisissez une offre"),
        queryset=Product.objects.filter(is_active=True),
    )

    class Meta:
        model = SubscriptionOption
        fields = [
            "product",
        ]
