from urllib.parse import quote_plus

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse


from django.utils.translation import ugettext_lazy as _
from django.conf import settings


def send_invoice_available(structure):
    users_mails = []
    for user in structure.owners:
        users_mails.append(user.email)
    invoice = reverse("dashboard:account:update", args=[structure.get_main_entity.slug, "structure"])
    html_content = render_to_string(
        "mails/mail_invoice.html",
        {
            "invoice_url": invoice,
            "domain": settings.ENVIRONMENT_DOMAIN,
            "protocol": settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL,
        },
    )
    send(_("[MIXITY] Paiement pour votre offre Mixity reçu"), users_mails, html_content)


def alert_invoice_available(invoice, structure):

    invoice_url = reverse("invoices:view", args=[invoice.id])
    html_content = render_to_string(
        "mails/mail_alert_invoice.html",
        {
            "invoice_url": invoice_url,
            "domain": settings.ENVIRONMENT_DOMAIN,
            "structure": structure,
            "protocol": settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL,
        },
    )
    send(
        _("[MIXITY] Nouvelle facture Mixity disponible"),
        [settings.MIXITY_EMAIL_FROM],
        html_content,
    )


def send(subject, to, html_content):
    msg = EmailMultiAlternatives(
        subject=subject, from_email=settings.MIXITY_EMAIL_FROM, to=to
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
