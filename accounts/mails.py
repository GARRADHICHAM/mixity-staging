import _io
import os
import base64
from urllib.parse import quote_plus, unquote_plus

from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import AES
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from sesame.utils import get_query_string

from mixity.utils import build_absolute_uri, encryption


def send_mail_forgotten_password(user, request, uuid, token):
    url = (
        "https://"
        + settings.ENVIRONMENT_DOMAIN
        + reverse(
            "user:password_reset_confirm",
            kwargs={"uidb64": uuid, "token": token},
        )
    )
    html_content = render_to_string("mails/password_reset.html", {"url": url})
    send(
        _("[MIXITY] Réinitialisation de votre mot de passe"), [user.email], html_content
    )


def send_mail_validation_custom(user, request, redirect=""):
    confirmation_key = user.get_confirmation_key()
    token = get_query_string(user)
    url = request.build_absolute_uri(
        redirect
        + token
        + "&confirmation_key="
        + confirmation_key
        + "&email="
        + quote_plus(user.email)
    )
    html_content = render_to_string("mails/mail_validation.html", {"url": url})
    send(_("[MIXITY] Merci de confirmer votre email"), [user.email], html_content)


def send_mail_validation_mail(user, request, alternative=""):
    confirmation_key = user.get_confirmation_key()
    token = get_query_string(user)
    url = request.build_absolute_uri(
        reverse("user:email_confirm" + alternative)
        + token
        + "&confirmation_key="
        + confirmation_key
        + "&email="
        + quote_plus(user.email)
    )
    html_content = render_to_string("mails/mail_validation.html", {"url": url})
    send(_("[MIXITY] Merci de confirmer votre email"), [user.email], html_content)


def send_mail_evaluation_started(user, evaluation, host=None):
    if not host:
        host = settings.ENVIRONMENT_DOMAIN
    if evaluation.is_human:
        encryption_class = encryption()
        encrypted_email = quote_plus(encryption_class.encrypt_data(user.email))
        encrypted_email = encrypted_email.replace("%2F", "%252F")
        url = (
            "https://"
            + host
            + reverse(
                "dashboard:account:collaborator_evaluation_redirect",
                kwargs={
                    "slug": evaluation.entity.slug,
                    "encrypted_email": encrypted_email,
                },
            )
        )
    else:
        url = (
            "https://"
            + host
            + reverse(
                "dashboard:evaluation_survey",
                kwargs={"slug": evaluation.entity.slug, "product": "scan"},
            )
        )
    html_render = evaluation.collaborators_mail
    html_render = html_render.replace("{ENTITY_NAME}", evaluation.entity.name)
    html_render = html_render.replace("{COLLABORATOR_NAME}", user.first_name)
    html_render = html_render.replace("{COLLABORATOR_NAME}", user.first_name)
    html_render = html_render.replace("[temps estim&eacute;]", "20-30 ")
    html_render = html_render.replace(
        "{ACCESS_BUTTON}",
        """
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin: 20px auto; text-align: center;">
            <tr>
                <td align="center">
                    <a href='"""
        + url
        + """' style="border-radius: 2.5em; background: #18ffc3; color: #181b3d; padding: 1em 2em; text-decoration: none; font-size: 16px; display: inline-block;">
                    Accéder à l'évaluation
                   </a>
                </td>
            </tr>
        </table>
        """,
    )

    send(
        evaluation.collaborators_mail_object,
        [user.email],
        html_render,
    )


def send_mail_mixity_start_created(user, structure, request):
    url = request.build_absolute_uri(
        reverse("structure:update_footprints", kwargs={"pk": structure.pk})
    )
    html_content = render_to_string(
        "mails/mixity_start_created.html", {"evaluation_url": url}
    )
    send(_("[MIXITY] Votre essai Mixity Start a été créé"), [user.email], html_content)


def send_mail_mixity_start_subscribed(structure):
    url = build_absolute_uri("structure:update_footprints", args=[structure.pk])
    account_url = build_absolute_uri("structure:account", args=[structure.pk])
    html_content = render_to_string(
        "mails/mixity_start_subscribed.html",
        {"evaluation_url": url, "account_url": account_url},
    )
    send(
        _("[MIXITY] Votre abonnement Mixity Start est disponible"),
        structure.owners.values_list("email", flat=True),
        html_content,
    )


def send_mail_mixity_start_validated(user, subscription, request):
    pursue_trial_url = request.build_absolute_uri(
        reverse("structure:pursue_trial", kwargs={"pk": subscription.pk})
    )
    results_url = request.build_absolute_uri(
        reverse(
            "scoring:detail_public_subscription",
            kwargs={
                "slug": subscription.evaluations.first().entity.slug,
                "subscriptionOption": subscription.product.slug,
            },
        )
    )
    html_content = render_to_string(
        "mails/mixity_start_validated.html",
        {
            "pursue_trial_url": pursue_trial_url,
            "results_url": results_url,
            "price": subscription.get_price,
            "request": request,
        },
    )
    send(
        _("[MIXITY] Votre essai Mixity Start a été validé"), [user.email], html_content
    )


def send_account_created_mail(user, request):
    html_content = render_to_string("mails/account_created.html")
    send(_("[MIXITY] Confirmation de création de compte"), [user.email], html_content)


def send_alert_account_created(user, request):
    html_content = render_to_string(
        "mails/alert_account_created.html", {"email": user.email}
    )
    send(_("[MIXITY] Nouvel utilisateur"), [settings.MIXITY_EMAIL_TO], html_content)


def send_structure_created_mail(user, request, structure, subscription):
    html_content = render_to_string(
        "mails/structure_created.html",
        {
            "user": user,
            "structure_name": str(structure),
            "subscription_label": _(subscription.subscriptionOption.product.label),
            "contact_url": "https://www.mixity.io/contact/",
            "structure_url": request.build_absolute_uri(
                reverse("structure:update_footprints", args=[structure.id])
            ),
        },
    )
    send(_("[MIXITY] Création de votre structure"), [user.email], html_content)


def send_invitation_mail(user, request, structure, inviter, uid=None, token=None):
    encryption_class = encryption()
    encrypted_email = quote_plus(encryption_class.encrypt_data(user.email))
    encrypted_email = encrypted_email.replace("%2F", "%252F")
    invite_url = request.build_absolute_uri(
        reverse(
            "dashboard:account:invitation_create_password",
            kwargs={"slug": structure.slug, "encrypted_email": encrypted_email},
        )
    )
    html_content = render_to_string(
        "mails/user_invitation.html",
        {
            "user": user,
            "inviter": inviter,
            "structure": structure,
            "invite_url": invite_url,
        },
    )
    send(
        _(f"[MIXITY] Invitation à collaborer sur {structure}"),
        [user.email],
        html_content,
    )


def send_invitation_mail_without_link(user, request, structure, inviter):
    invite_url = (
        "https://"
        + settings.ENVIRONMENT_DOMAIN
        + reverse("dashboard:account:dashboard_login")
    )

    html_content = render_to_string(
        "mails/user_invitation_without_link.html",
        {
            "user": user,
            "inviter": inviter,
            "structure": structure,
            "invite_url": invite_url,
        },
    )
    send(
        _(f"[MIXITY] Invitation à collaborer sur {structure}"),
        [user.email],
        html_content,
    )


def send_evaluation_answers_export(email, evaluation, zipname, zipfile):
    html_content = render_to_string(
        "mails/evaluation_answers_export.html", {"evaluation": evaluation}
    )
    send(
        _("[MIXITY] Export des réponses pour l'évaluation %s terminé")
        % evaluation.entity.name,
        [email],
        html_content,
        attachments=[(zipname, zipfile)],
    )


def send_users_export(email, name, file):
    html_content = "Votre export des utilisateurs de la plateforme est disponible."
    send(
        _("[MIXITY] Export des utilisateurs de la plateforme"),
        [email],
        html_content,
        attachments=[(name, file)],
    )


def send(subject, to, html_content, attachments=None):
    email = EmailMultiAlternatives(
        subject=subject, from_email=settings.MIXITY_EMAIL_FROM, to=to
    )
    email.attach_alternative(html_content, "text/html")
    if attachments:
        for attachment in attachments:
            # Unpacking each attachment tuple
            if len(attachment) == 2:
                (name, path) = attachment
                attachment_type = None
            elif len(attachment) == 3:
                (name, path, attachment_type) = attachment

            # Accessing the path of type BufferedReader
            filepath = path
            if type(path) == _io.BufferedReader:
                filepath = path.name

            # Making attachments
            with open(filepath, "rb") as fd:
                if attachment_type:
                    email.attach(name, fd.read(), attachment_type)
                else:
                    email.attach(name, fd.read())
    email.send()
