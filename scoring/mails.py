import datetime
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

from mixity.utils import build_absolute_uri


def send_structure_created_mail_start(user, structure, request):
    html_content = render_to_string(
        "mails/structure_created_start.html",
        {
            "structure_url": request.build_absolute_uri(
                reverse("structure:update_footprints", args=[structure.id])
            )
        },
    )
    send(_("[MIXITY] Création de votre évaluation"), [user.email], html_content)


def send_evaluation_created_mail(user, request, evaluation):
    if evaluation.sheet.slug == "mixity_start":
        html_content = render_to_string(
            "mails/evaluation_created_start.html",
            {
                "footprint_url": request.build_absolute_uri(
                    reverse(
                        "detail_public",
                        args=[evaluation.entity.slug],
                    )
                ),
                "structure_url": request.build_absolute_uri(
                    reverse(
                        "structure:update_footprints",
                        args=[evaluation.entity.entity_level.structure.id],
                    )
                ),
            },
        )
    else:
        html_content = render_to_string("mails/evaluation_created.html", {})
    send(_("[MIXITY] Création de votre évaluation"), [user.email], html_content)


def send_evaluation_validated_mail(user, request, evaluation):
    active_subscription = evaluation.entity.entity_level.structure.active_subscription
    diffusion = False
    if (
        active_subscription
        and active_subscription.subscription_type.allow_public_display
    ):
        diffusion = True
    html_content = render_to_string(
        "mails/evaluation_validated.html",
        {
            "structure_public_url": request.build_absolute_uri(
                reverse(
                    "detail_public",
                    args=[evaluation.entity.slug],
                )
            ),
            "diffusion": diffusion,
        },
    )
    send(_("[MIXITY] Validation de votre évaluation"), [user.email], html_content)


def send_human_statistics(evaluation):
    answers_count = evaluation.collaborators.count()
    number_of_employees = evaluation.entity.entity_level.structure.workforce
    rate = round(answers_count * 100 / number_of_employees)
    html_content = render_to_string(
        "mails/human_statistics.html",
        {
            "footprint_update_url": build_absolute_uri(
                "structure:update_footprints",
                args=[evaluation.entity.entity_level.structure.id],
            ),
            "total_answers": answers_count,
            "rate_answers": rate,
            "number_of_employees": number_of_employees,
        },
    )
    send(
        _("[MIXITY] Statistiques de votre évaluation Mixity Human"),
        evaluation.entity.entity_level.structure.owners.values_list("email", flat=True),
        html_content,
    )


def send_evaluation_published_private_mail(user, request, evaluation):
    html_content = render_to_string(
        "mails/evaluation_published.html",
        {
            "title": _(
                "Félicitations, votre évaluation est désormais disponible sur votre espace privé !"
            ),
            "structure_public_url": request.build_absolute_uri(
                reverse(
                    "detail_public",
                    args=[evaluation.entity.slug],
                )
            ),
        },
    )
    send(
        _("[MIXITY] Fiche entreprise disponible sur votre espace"),
        [user.email],
        html_content,
    )


def send_evaluation_published_public_mail(user, request, evaluation):
    html_content = render_to_string(
        "mails/evaluation_published.html",
        {
            "title": _(
                "Félicitations, votre évaluation est désormais disponible publiquement !"
            ),
            "public": evaluation.public_display,
            "structure_public_url": request.build_absolute_uri(
                reverse(
                    "detail_public",
                    args=[evaluation.entity.slug],
                )
            ),
        },
    )
    send(
        _("[MIXITY] Fiche entreprise disponible publiquement"),
        [user.email],
        html_content,
    )


def alert_evaluation_created_mail(user, request, evaluation):
    html_content = render_to_string(
        "mails/alert_evaluation_created.html",
        {
            "user": user,
            "workforce": evaluation.entity.entity_level.structure.workforce,
            "subscription_type": evaluation.subscription.subscription_type,
            "evaluation": evaluation,
            "evaluation_url": request.build_absolute_uri(
                reverse("admin:scoring_evaluation_change", args=[evaluation.id])
            ),
        },
    )
    send(
        _("[MIXITY] Une évaluation a été crée sur Mixity"),
        [settings.MIXITY_EMAIL_FROM],
        html_content,
    )


def alert_evaluation_published_mail(request, evaluation):
    html_content = render_to_string(
        "mails/alert_evaluation_published.html",
        {
            "evaluation": evaluation,
            "evaluation_url": request.build_absolute_uri(
                reverse("admin:scoring_evaluation_change", args=[evaluation.id])
            ),
        },
    )
    send(
        _("[MIXITY] Une évaluation a été publiée sur Mixity"),
        [settings.MIXITY_EMAIL_FROM],
        html_content,
    )


def alert_evaluation_reminder(email, evaluation):
    html_content = render_to_string(
        "mails/alert_evaluation_reminder_" + str(evaluation.reminder_count) + ".html",
        {
            "evaluation_url": "https://mixity.co/structure/"
            + str(evaluation.entity.entity_level.structure.id)
            + "/update/footprints/"
        },
    )
    send(_("[MIXITY] Votre évaluation est toujours en cours"), [email], html_content)


def alert_admin_computing(email, evaluation, only_filters=False):
    """
    This function alert the admin by sending an email when : 1.the comuting of all scores is done or 2.the computing only of filters is done
    """

    email_list = [email]
    date = datetime.datetime.now().strftime("%d/%m/%y à %H:%M:%S")
    structure_name = evaluation.entity.name

    #  Default case : computing all the scores
    email_html = "updating_scores.html"

    subject = _("Recalcul des scores et des filtres de la structure {}")

    if only_filters:
        email_html = "recomputing_pre_registered_filters.html"
        subject = _("Recalcul des filtres de la structure {}")

    html_content = render_to_string(
        "mails/{}".format(email_html),
        {"structure_name": structure_name, "date": date},
    )

    send(
        subject.format(structure_name),
        email_list,
        html_content,
    )


def send_adp_connection_request(user, entity, request):
    html_content = render_to_string("mails/adp_connection_request.html")
    send(
        _("[MIXITY] Demande de connexion ADP"),
        [settings.MIXITY_EMAIL_FROM],
        html_content,
    )


def alert_reevaluation_request(evaluation):
    html_content = render_to_string(
        "mails/reevaluation_request.html",
        {"evaluation": evaluation, "entity": evaluation.entity.slug},
    )
    send(
        _("[MIXITY] Demande de réouverture d'évaluation"),
        [settings.MIXITY_EMAIL_FROM],
        html_content,
    )


def send_reevaluation_accepted(evaluation, email):
    html_content = render_to_string(
        "mails/reevaluation_accepted.html",
        {"evaluation": evaluation, "entity": evaluation.entity.slug},
    )
    send(
        _("[MIXITY] Réouverture évaluation diag"),
        [email],
        html_content,
    )


def send(subject, to, html_content):
    msg = EmailMultiAlternatives(
        subject=subject, from_email=settings.MIXITY_EMAIL_FROM, to=to
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
