import datetime
from django.contrib import messages
from django.views.generic import UpdateView, ListView, RedirectView

from scoring.models import QuestionSheetType
from subscriptions.mails import send_alert_offer_created
from subscriptions.forms import SubscriptionForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic.edit import FormMixin
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from accounts.models import Structure
from subscriptions.models import SubscriptionOption, SubscriptionPack, Product


class ProductListView(ListView):
    model = Product
    template_name = "subscription_type_list.html"
    context_object_name = "products"


class AccountSubsriptionReNew(
    LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, RedirectView
):
    model = Structure
    success_message = _("Votre demande d'offre a bien été prise en compte")

    def get_subscriptionPack(self):
        return get_object_or_404(SubscriptionPack, pk=self.kwargs["offer_pk"])

    def get_redirect_url(self, *args, **kwargs):
        current_subscriptionPack = self.get_subscriptionPack()
        structure = current_subscriptionPack.structure
        return reverse("structure:account", args=(structure.pk,))

    # def dispatch(self, request, *args, **kwargs):
    #     current_subscriptionPack = self.get_subscriptionPack()
    #     structure = current_subscriptionPack.structure
    #     today = datetime.date.today()
    #     subscriptionPack, _c = SubscriptionPack.objects.get_or_create(
    #         structure=structure,
    #         is_active=False,
    #         start_date=today,
    #         question_sheet_type=current_subscriptionPack.options.question_sheet_type,
    #         subscription_type=current_subscription.subscription_type,
    #         end_date=today + current_subscription.subscription_type.duration,
    #     )
    #     send_alert_offer_created(self.request.user, subscription)
    #     messages.success(self.request, self.success_message)
    #     return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.request.user in self.get_subscriptionPack().structure.owners
