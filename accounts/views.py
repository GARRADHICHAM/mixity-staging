import datetime
import json
from collections import defaultdict

from django.contrib import messages
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import (
    PasswordResetConfirmView as BasePasswordResetConfirmView,
)
from django.db import transaction
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.db.models import Prefetch, Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    DeleteView,
    DetailView,
    FormView,
    RedirectView,
    TemplateView,
    UpdateView,
    CreateView,
)
from formtools.wizard.views import SessionWizardView
from simple_email_confirmation.exceptions import EmailConfirmationExpired

from accounts.forms import (
    MixityUserCreationForm,
    MixityUserFormClass,
    MixityUserOrgaFormClass,
    StructureBusinessFormClass,
    StructureDetailFormClass,
    StructureInfoFormClass,
    StructureOfferPreFormClass,
    StructureOfferFormClass,
    StructureTagPreFormClass,
    StructureOneTagFormClass,
    StructureMultipleTagFormClass,
    StructureStartTrialFormClass,
    StructureStartPursueTrialFormClass,
    CollaboratorCriteriaChoiceForm,
    StructureClientOrSolverFormClass,
    PasswordResetConfirmForm,
)
from accounts.mails import (
    send_alert_account_created,
    send_mail_validation_mail,
    send_structure_created_mail,
    send_mail_mixity_start_created,
    send_mail_validation_custom,
)
from accounts.models import (
    Membership,
    MixityUser,
    Structure,
    Entity,
    EntityLevel,
    HumanCriteria,
    HumanCriteriaChoice,
)
from act.models import Solver
from accounts.vocabularies import (
    BOOLEANS_ELEMENTS,
    TARGET_CHOICE,
    MONTHS,
    CIVILITY_CHOICES,
    CAMPUS_CHOICE,
)
from mixity.dashboard.views import DashboardStructureViewMixin
from mixity.settings import (
    SMALL_COMPANY_LIMIT,
    MIDDLE_COMPANY_LIMIT,
    VERY_SMALL_COMPANY_LIMIT,
    HUMAN_FILTER_LIMIT,
    COMPANY_50_250,
)
from mixity.utils import deep_getattr, segment_tracking
from mixity.views import logger
from scoring.mails import send_structure_created_mail_start
from scoring.models import (
    Answer,
    Category,
    Evaluation,
    SubAnswer,
    QuestionTag,
    QuestionSheetType,
    Aim,
    ScoreCategory,
    Collaborator,
    get_human_campus_short_slug,
    get_filtered_human_campus_slugs,
    CollaboratorsStatistics,
)
from subscriptions.mails import (
    send_alert_offer_created,
    send_alert_offer_created_start,
    send_alert_solver_created,
)
from subscriptions.models import (
    SubscriptionPack,
    SubscriptionOption,
    Product,
    Subscription,
)

# fixing dev environnement where CLOUDINARY_URL is not set
try:
    from cloudinary_storage.storage import MediaCloudinaryStorage

    ImageStorage = MediaCloudinaryStorage()
except ImproperlyConfigured:
    ImageStorage = FileSystemStorage()


class PasswordResetFormAllowNoPassword(PasswordResetForm):
    def get_users(self, email):
        active_users = get_user_model()._default_manager.filter(
            email__iexact=email, is_active=True
        )
        return active_users


class ResetPasswordViews(
    TemplateView,
):
    template_name = "accounts/forgotten-password-mail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ResetPasswordConfirmView(
    TemplateView,
):
    template_name = "accounts/forgotten-password-change.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uuid"] = self.kwargs["uidb64"]
        return context


def old_user_account_view(request):
    return redirect(reverse("home"))


def is_mixity_a_la_carte(wizard):
    product = wizard.get_cleaned_data_for_step("OfferForm") or {}
    product = product.get("product")
    return product == Product.objects.get(slug="diag") and is_client_structure(wizard)


def is_one_tag(wizard):
    tag = wizard.get_cleaned_data_for_step("TagPreForm") or {}
    tag = tag.get("tag_choice")
    return tag == "3" and is_client_structure(wizard)


def is_multiple_tag(wizard):
    tag = wizard.get_cleaned_data_for_step("TagPreForm") or {}
    tag = tag.get("tag_choice")
    return tag == "2" and is_client_structure(wizard)


def is_not_human(wizard):
    product = wizard.get_cleaned_data_for_step("OfferPreForm") or {}
    product = product.get("product")
    return product != Product.objects.get(slug="human") and is_client_structure(wizard)


def is_client_structure(wizard):
    struct_type = wizard.get_cleaned_data_for_step("ClientOrSolverForm") or {}
    struct_type = struct_type.get("structure_type")
    return struct_type == "client"


class StructureCreateView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/structure_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class StructureMemberDeleteView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    success_message = _("Vous avez mis à jour vos utilisateurs")

    def test_func(self):
        return self.request.user in self.get_structure().owners

    def get_structure(self):
        return get_object_or_404(Structure, pk=self.kwargs["pk"])

    def get_user(self):
        return get_object_or_404(MixityUser, id=self.kwargs["user_pk"])

    def get_redirect_url(self, *args, **kwargs):
        self.get_structure().members.remove(self.get_user())
        messages.success(self.request, self.success_message)
        return reverse(
            "dashboard:account:update_members", args=(self.get_structure().slug,)
        )


class StructureMemberOwnerView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    success_message = _("Vous avez mis à jour vos utilisateurs")

    def test_func(self):
        return self.request.user in self.get_structure().owners

    def get_structure(self):
        return get_object_or_404(Structure, pk=self.kwargs["pk"])

    def get_membership(self):
        return get_object_or_404(Membership, id=self.kwargs["membership_pk"])

    def get_redirect_url(self, *args, **kwargs):
        membership = self.get_membership()
        membership.is_owner = abs(membership.is_owner - 1)
        membership.save()
        messages.success(self.request, self.success_message)
        return reverse(
            "dashboard:account:update_members", args=(self.get_structure().slug,)
        )


class StructureMemberReaderView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    success_message = _("Vous avez mis à jour vos utilisateurs")

    def test_func(self):
        return self.request.user in self.get_structure().owners

    def get_structure(self):
        return get_object_or_404(Structure, pk=self.kwargs["pk"])

    def get_membership(self):
        return get_object_or_404(Membership, id=self.kwargs["membership_pk"])

    def get_redirect_url(self, *args, **kwargs):
        membership = self.get_membership()
        membership.is_reader = abs(membership.is_reader - 1)
        membership.save()
        messages.success(self.request, self.success_message)
        return reverse(
            "dashboard:account:update_members", args=(self.get_structure().slug,)
        )


class EmailConfirmationView(RedirectView):
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
            return reverse("dashboard:account:dashboard_login")

        if not user.is_confirmed:
            messages.error(
                self.request,
                "Votre mail n'a pas été validé, veuillez vous inscrire avec un autre mail",
            )
            return reverse("dashboard:account:dashboard_register")
        else:
            return reverse("dashboard:account:dashboard_register_confirmed")


class EmailConfirmationStartView(EmailConfirmationView):
    def get_redirect_url(self, *args, **kwargs):
        url = super(EmailConfirmationStartView, self).get_redirect_url(*args, **kwargs)
        if url == reverse("dashboard:account:dashboard_register_confirmed"):
            return reverse("dashboard:account:dashboard_register_start_confirmed")
        else:
            return url


class StructureDeleteView(
    LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView
):
    model = Structure
    success_url = reverse_lazy("home")
    success_message = _("La structure a bien été supprimée.")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

    def test_func(self):
        return self.request.user in self.get_object().owners

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        structure = self.get_object()
        context["structure"] = structure.juridic_name
        return context


class ManageHumanCriteriaView(
    LoginRequiredMixin, SuccessMessageMixin, UserPassesTestMixin, DetailView
):
    permission_denied_message = _("Vous n'avez pas la possibilité de générer de lien")
    template_name = "accounts/manage_human_criteria.html"
    model = Structure

    def get_context_data(self, **kwargs):
        context = super(ManageHumanCriteriaView, self).get_context_data(**kwargs)

        context["default_criteria"] = {
            "label": _("Fonction"),
            "choice": [
                _("Agent de maîtrise"),
                _("Technicien.ne"),
                _("Associé.e"),
                _("Cadre"),
                _("Employé.e"),
                _("Autre"),
            ],
        }
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            criteria_json = json.loads(request.body.decode("utf-8"))
            structure = get_object_or_404(Structure, pk=self.kwargs["pk"])
            active_human_sub = (
                Subscription.objects.filter(
                    subscription_type__slug="human", structure=structure
                )
                .order_by("-start_date")
                .first()
            )
            if not Evaluation.objects.filter(subscription=active_human_sub).exists():
                evaluation = Evaluation.objects.create(
                    subscription=active_human_sub,
                    name=structure.juridic_name or structure.commercial_name,
                    sheet=active_human_sub.question_sheet_type.question_sheets.last(),
                    entity=structure.get_main_entity,
                )
                evaluation.tags.add(
                    *(list(structure.tags.all()) + list(active_human_sub.tags.all()))
                )
                for criteria in criteria_json:
                    human_criteria = HumanCriteria.objects.create(
                        evaluation=evaluation, label=criteria["label"]
                    )
                    for choice in criteria["choices"]:
                        HumanCriteriaChoice.objects.create(
                            criteria=human_criteria, label=choice
                        )
                messages.success(self.request, "Votre lien a bien été généré")
                return JsonResponse({"success": True})
            else:
                eval = Evaluation.objects.filter(subscription=active_human_sub).first()
                msg = f"Invalid subscription {active_human_sub} (structure {structure}) or evaluation {eval} already exists"
                logger.error(msg)
                return JsonResponse({"message": msg}, status=400)

        except Exception as e:
            logger.exception(e)
            return JsonResponse({"message": str(e)}, status=400)

    def test_func(self):
        structure = get_object_or_404(Structure, pk=self.kwargs["pk"])
        s = Subscription.objects.filter(
            structure=structure,
            subscription_type__slug="human",
        ).last()
        return (
            s.is_active
            and self.request.user
            and self.request.user.is_authenticated
            and (
                self.request.user in structure.owners
                or self.request.user in structure.get_main_entity.owners
            )
        )
