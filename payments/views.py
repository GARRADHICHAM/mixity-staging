# payments/views.py
import datetime
import logging

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic.base import TemplateView

from accounts.mails import send_mail_mixity_start_subscribed
from accounts.models import Structure
from invoices.mails import alert_invoice_available, send_invoice_available
from invoices.models import Invoice
from payments.models import CheckoutSession

logger = logging.getLogger(__name__)


class StructurePaymentView(UserPassesTestMixin, LoginRequiredMixin, DetailView):
    model = Structure
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(StructurePaymentView, self).get_context_data(**kwargs)
        context["structure_id"] = self.get_object().id
        return context

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().is_partial:
            return redirect(
                reverse(
                    "structure:pursue_trial",
                    args=[self.get_object().first_subscriptionOption.pk],
                )
            )
        # Paiement en ligne désactivé (pas de clé Stripe) : la page de paiement
        # resterait bloquée sur « Chargement ». L'offre attend la validation de
        # l'équipe Mixity, comme les autres offres.
        if not settings.STRIPE_PUBLIC_KEY:
            messages.info(
                request,
                _(
                    "Votre demande a bien été enregistrée. L'équipe Mixity va "
                    "activer votre offre et vous prévenir par e-mail."
                ),
            )
            main_entity = self.get_object().get_main_entity
            if main_entity:
                return redirect(reverse("home", args=[main_entity.slug]))
            return redirect(reverse("home"))
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        struct = self.get_object()
        option = struct.first_subscriptionOption
        return (
            self.request.user in struct.owners
            and (not option.is_active or option.is_trial)
            and struct.can_pay_by_card
        )


@csrf_exempt
def stripe_config(request):
    if request.method == "GET":
        return JsonResponse({"publicKey": settings.STRIPE_PUBLIC_KEY}, safe=False)


class StructureCreateCheckoutSession(
    UserPassesTestMixin, LoginRequiredMixin, DetailView
):
    model = Structure

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        if request.method == "GET":
            # get_host() valide l'en-tête Host (ALLOWED_HOSTS), contrairement à request.META['HTTP_HOST']
            domain_url = f"{request.scheme}://{request.get_host()}/payments/{self.get_object().id}/"
            checkout_session = CheckoutSession.objects.filter(
                subscriptionOption=self.get_object().first_subscriptionOption
            ).first()
            if checkout_session:
                if checkout_session.is_expired:
                    checkout_session.delete()
                else:
                    return JsonResponse({"sessionId": checkout_session.checkout_id})
            try:
                if not self.get_object().stripe_customer_id:
                    email = request.user.email
                else:
                    email = None
                checkout_session = stripe.checkout.Session.create(
                    customer=self.get_object().stripe_customer_id,
                    client_reference_id=self.get_object().id,
                    customer_email=email,
                    allow_promotion_codes=True,
                    success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
                    cancel_url=domain_url + "cancelled/",
                    payment_method_types=[
                        "card",
                        "sepa_debit",
                        # "sofort",
                        # "giropay",
                    ],
                    mode="payment",
                    line_items=[
                        {
                            "price": self.get_object().first_subscriptionOption.stripe_price_id,
                            "quantity": 1,
                        }
                    ],
                    automatic_tax={
                        "enabled": True,
                    },
                )
                CheckoutSession.objects.create(
                    subscriptionOption=self.get_object().first_subscriptionOption,
                    checkout_id=checkout_session["id"],
                    payment_intent=checkout_session["payment_intent"],
                    expires_at=make_aware(
                        datetime.datetime.fromtimestamp(checkout_session["expires_at"])
                    ),
                )
                return JsonResponse({"sessionId": checkout_session["id"]})
            except Exception as e:
                logger.exception(e)
                return JsonResponse({"error": "CHECKOUT_SESSION_FAILED"}, status=400)

    def test_func(self):
        subscriptionOption = self.get_object().first_subscriptionOption
        return (
            self.request.user in self.get_object().owners
            and (not subscriptionOption.is_active or subscriptionOption.is_trial)
            and self.get_object().can_pay_by_card
        )


class CancelledView(LoginRequiredMixin, TemplateView):
    model = Structure
    template_name = "cancelled.html"


def update_subscription(subscription):
    evaluation = subscription.evaluation
    if evaluation:
        evaluation.is_validated_by_user = False
        evaluation.is_validated_by_admin = False
        evaluation.private_display = False
        for tag in subscription.tags.all():
            evaluation.tags.remove(tag)
        evaluation.generate_answers()
        evaluation.save()
    subscription.tags.clear()


@csrf_exempt
@require_POST
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    if not sig_header:
        return HttpResponse(status=400)
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        logger.exception(e)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.exception(e)
        return HttpResponse(status=400)

    if "payment_intent" in event["data"]["object"]:
        checkout_session = CheckoutSession.objects.filter(
            payment_intent=event["data"]["object"]["payment_intent"]
        ).first()
    elif "id" in event["data"]["object"]:
        if event["data"]["object"]["object"] == "checkout.session":
            checkout_session = CheckoutSession.objects.filter(
                checkout_id=event["data"]["object"]["id"]
            ).first()
        elif event["data"]["object"]["object"] == "payment_intent":
            checkout_session = CheckoutSession.objects.filter(
                payment_intent=event["data"]["object"]["id"]
            ).first()
        else:
            return HttpResponse(status=200)
    else:
        return HttpResponse(status=200)

    # Session inconnue : on répond 200, sinon Stripe réessaie indéfiniment.
    if checkout_session is None:
        logger.warning("Webhook Stripe : session inconnue pour l'événement %s", event["type"])
        return HttpResponse(status=200)

    subscription = checkout_session.subscription
    if subscription is None:
        # Limite connue (point PAY-1) : la session de paiement est enregistrée avec une option
        # d'abonnement et non avec un abonnement, l'activation automatique n'est donc pas possible.
        logger.error(
            "Webhook Stripe : la session %s n'est liée à aucun abonnement, rien n'est activé.",
            checkout_session.pk,
        )
        return HttpResponse(status=200)

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        discount = event["data"]["object"]["total_details"]["amount_discount"]
        tax_free_price = event["data"]["object"]["amount_subtotal"] - discount
        tax_included_price = event["data"]["object"]["amount_total"]
        subscription.invoice = Invoice.objects.create(
            tax_free_price=tax_free_price / 100,
            tax_included_price=tax_included_price / 100,
            discount=discount / 100,
            tax=(tax_included_price - tax_free_price) / 100,
        )
        # Direct payment = instant activation
        if event["data"]["object"]["payment_status"] == "paid":
            logger.info("Payment was successful.")
            subscription.is_active = True
            invoice = subscription.invoice
            invoice.paid = True
            invoice.paid_at = timezone.now()
            invoice.save()
            if subscription.is_trial:
                update_subscription(subscription)
        else:
            logger.warning("Payment is delayed")

        subscription.save()

        checkout_session.payment_status = event["data"]["object"]["payment_status"]
        checkout_session.save()
        structure = subscription.structure
        structure.stripe_customer_id = event["data"]["object"][
            "customer"
        ]  # We save the customer information
        structure.save()
        send_invoice_available(structure)
        alert_invoice_available(subscription.invoice, structure)
        ###Outdated, datas are deprecated###
        # if subscription.subscription_type.slug == "mixity_start":
        #     send_mail_mixity_start_subscribed(structure)
    elif event["type"] == "charge.dispute.closed":
        # we disable the subscription only when dispute is lost
        if event["data"]["object"]["status"] == "lost":
            subscription.is_active = False
            invoice = subscription.invoice
            invoice.paid = False
            invoice.save()
            checkout_session.payment_status = "refunded"
            checkout_session.save()
            subscription.save()
            logger.warning("Subscription has been suspended")
    elif event["type"] == "checkout.session.async_payment_failed":
        # Async payment such as SEPA. If payment failed even if checkout.session.completed, we don't enable the account
        subscription.is_active = False
        checkout_session.payment_status = "unpaid_failed"
        checkout_session.save()
        subscription.save()
    elif event["type"] == "checkout.session.async_payment_succeeded":
        # Async payment such as SEPA. If payment succeeded, we enable the account
        checkout_session.payment_status = "paid"
        checkout_session.save()
        subscription.is_active = True
        invoice = subscription.invoice
        invoice.paid = True
        invoice.paid_at = timezone.now()
        invoice.save()
        subscription.save()

        if subscription.is_trial:
            update_subscription(subscription)
        logger.warning("Subscription has been enabled")

    return HttpResponse(status=200)
