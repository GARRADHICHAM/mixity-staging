from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse


def send_offer_validated(request, user, option):
    html_content = render_to_string(
        "mails/offer_request_validated.html",
        {
            "structure": str(option.subscriptionPack.structure),
            "subscription_label": _(option.product.question_sheet_type.name),
            "evaluation_url": request.build_absolute_uri(
                reverse("home")
            ),
        },
    )
    send(_("[MIXITY] Demande d'offre sur Mixity"), user.email, html_content)


def send_alert_offer_created(user, subscription):
    html_content = render_to_string(
        "mails/alert_offer_request.html",
        {
            "email": user.email,
            "structure": str(subscription.structure),
            "subscription": subscription.subscription_type.label,
        },
    )
    send(
        _("[MIXITY] Demande d'offre sur Mixity"),
        settings.MIXITY_EMAIL_SUPPORT,
        html_content,
    )


def send_alert_solver_created(user, solver):
    html_content = render_to_string(
        "mails/alert_offer_request.html",
        {
            "email": user.email,
            "structure": str(solver.structure),
            "subscription": "solutionneur",
        },
    )
    send(
        _("[MIXITY] Demande de solutionneur sur Mixity"),
        settings.MIXITY_EMAIL_SUPPORT,
        html_content,
    )


def send_alert_offer_created_start(user, subscription):
    html_content = render_to_string(
        "mails/alert_offer_start.html",
        {
            "email": user.email,
            "structure": str(subscription.structure),
            "subscription": subscription.subscription_type.label,
        },
    )
    send(
        _("[MIXITY] Nouvelle structure start sur Mixity"),
        settings.MIXITY_EMAIL_SUPPORT,
        html_content,
    )


def send(subject, to, html_content):
    msg = EmailMultiAlternatives(
        subject=subject, from_email=settings.MIXITY_EMAIL_FROM, to=[to]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
