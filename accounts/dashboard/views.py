import datetime

from mixity.utils import encryption
from urllib.parse import unquote_plus, quote_plus

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    UpdateView,
    DetailView,
    TemplateView,
    View,
    RedirectView,
)
from django.views.generic.edit import FormMixin

from simple_email_confirmation.exceptions import EmailConfirmationExpired

from collaborator_evaluation.views import SignedEvaluationMixin

from accounts.forms import (
    StructureFormClass,
    EntityFormClass,
    StructureMembersForm,
    StructurePublicFormClass,
    StructurePublicHumanFormClass,
    MixityUserFormClass,
)
from accounts.mails import (
    send_invitation_mail,
)
from scoring.models import Evaluation
from accounts.models import Membership, MixityUser, Structure, Entity
from mixity.dashboard.views import DashboardStructureViewMixin, DashboardAccessMixin
from mixity.utils import segment_tracking
from scoring.models import (
    QuestionSheetType,
)
from subscriptions.forms import SubscriptionForm
from subscriptions.mails import send_alert_offer_created
from subscriptions.models import Subscription
from django.contrib.auth.views import PasswordChangeView as BasePasswordChangeView


def reorganise_entities_list(accessible_entities):
    ordered_entities = []
    for ent in accessible_entities:
        if ent.parent_entity:
            index = ordered_entities.index(ent.parent_entity)
            ordered_entities.insert(index + 1, ent)
        else:
            ordered_entities.append(ent)
    return ordered_entities


class StructureUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "accounts/structure-update.html"
    form_class = StructureFormClass

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_category"] = kwargs["category"]
        context["current_page"] = _("Informations de la structure")
        context["current_app"] = _("Structure")
        context["is_owner"] = (
            self.request.user in self.entity.entity_level.structure.owners
        )
        context["commercial_name"] = self.entity.entity_level.structure.commercial_name
        context["category"] = self.entity.entity_level.structure.category
        context["logo"] = self.entity.entity_level.structure.logo
        context["workforce"] = self.entity.entity_level.structure.workforce
        context["business_line"] = self.entity.entity_level.structure.business_line
        context[
            "secondary_business_lines"
        ] = self.entity.entity_level.structure.secondary_business_lines
        context["siret"] = self.entity.entity_level.structure.siret
        context["duns"] = self.entity.entity_level.structure.duns
        context[
            "num_tva_intracom"
        ] = self.entity.entity_level.structure.num_tva_intracom
        context["address"] = self.entity.entity_level.structure.address
        context["website"] = self.entity.entity_level.structure.website
        context["phone"] = self.entity.entity_level.structure.phone1
        return context


class ProfileUpdateView(
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "accounts/profile_update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class PasswordChangeView(
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    TemplateView,
):
    template_name = "accounts/password-change.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_mail"] = self.request.user.email
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class DashboardRegisterConfirmedRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = get_object_or_404(MixityUser, username=self.request.GET["email"])
        try:
            user.confirm_email(self.request.GET["confirmation_key"])
        except EmailConfirmationExpired:
            messages.error(
                self.request,
                "Pour des raisons de sécurité, le lien de connexion automatique a expiré. "
                "Vous pouvez vous connecter avec votre mail et votre mot de passe",
            )
            return "/account/login/"

        if not user.is_confirmed:
            messages.error(
                self.request,
                "Votre mail n'a pas été validé, veuillez vous inscrire avec un autre email",
            )
            return "/account/register/"
        else:
            return reverse("dashboard_register_confirmed")


class DashboardRegisterStartView(
    LoginRequiredMixin,
    TemplateView,
):
    template_name = "accounts/register_start.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

  
class DashboardRegisterConfirmedView(
    TemplateView,
):
    template_name = "accounts/register_confirmed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(MixityUser, username=self.request.GET["email"])
        user.confirm_email(self.request.GET["confirmation_key"])
        return context

  
class DashboardMailValidationView(
    TemplateView,
):
    template_name = "accounts/mail_validation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

   
class DashboardRegisterView(
    TemplateView,
):
    template_name = "accounts/register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subscription"] = kwargs.get("subscription", "public")
        return context

 
class DashboardLoginView(
    TemplateView,
):
    template_name = "accounts/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class DashboardRegisterStartConfirmedView(
    TemplateView,
):
    template_name = "accounts/register_start_confirmed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(MixityUser, username=self.request.GET["email"])
        user.confirm_email(self.request.GET["confirmation_key"])
        return context

  
class InvitationConfirmedView(
    TemplateView,
):
    template_name = "accounts/invitation_confirmed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        encryption_class = encryption()
        email = encryption_class.decrypt_data(unquote_plus(kwargs["encrypted_email"]))
        context["email"] = email
        context["slug"] = kwargs["slug"]
        return context

  
class InvitationCreatePasswordView(
    TemplateView,
):
    template_name = "accounts/invitation_create_password.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        encryption_class = encryption()
        email = encryption_class.decrypt_data(unquote_plus(kwargs["encrypted_email"]))
        context["email"] = email
        context["slug"] = kwargs["slug"]
        return context

   
class CollaboratorRedirectEvaluationView(SignedEvaluationMixin, View):
    def get(self, request, *args, **kwargs):
        encryption_class = encryption()
        email = encryption_class.decrypt_data(unquote_plus(kwargs["encrypted_email"]))
        slug = kwargs["slug"]
        user = get_object_or_404(MixityUser, email=email)
        evaluations = Evaluation.objects.filter(entity__slug=slug)
        evaluation = None
        if evaluations.exists() == False:
            return redirect("/")
        for eval in evaluations:
            if (
                eval.is_started == True
                and eval.entity.get_human_status == "in_progress"
            ):
                evaluation = eval
                break
        if evaluation == None:
            return redirect("/")
        if (
            evaluation.is_started == True
            and evaluation.entity.get_human_status == "in_progress"
        ):
            if request.user == user:
                return redirect("/")
            if request.user != user and request.user.is_authenticated:
                return redirect("/")
            if user.has_usable_password() == True:
                return redirect("/login/")
            else:
                return redirect(
                    request.get_full_path().replace(
                        "invitation/redirect/", "invitation/create_password/"
                    )
                )
        return redirect("/")