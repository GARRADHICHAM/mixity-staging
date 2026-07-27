import json
import logging
import random
from datetime import datetime
import base64

import magicattr
import os, sys

from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import AES
from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime
from django_rq import job

from accounts.models import MixityUser
from mixity.services.segment import SegmentAPI

from cryptography.fernet import Fernet


def deep_getattr(obj, attrs, default=None):
    try:
        return magicattr.get(obj, attrs)
    except AttributeError:
        return default


class DictCache:
    def __init__(self, duration=30):
        """
        Class to cache values
        @param duration: duration of the cache
        """
        self.cache = {}
        self.duration = duration

    def get_or_set(self, key, function, method_arguments=None):
        """
        Get or set a value to cache. Expired cache will not be cleared automatically.
        @param method_arguments: arguments to send to the method provided in parameters
        @param key: key of the cache
        @param function: method to call if cache is expired or empty
        @return: value of the cache
        """
        if method_arguments is None:
            method_arguments = {}
        if (
            not key in self.cache
            or (datetime.now() - self.cache[key]["datetime"]).total_seconds()
            >= self.duration
        ):
            self.cache[key] = {
                "value": function(**method_arguments),
                "datetime": datetime.now(),
            }
        return self.cache[key]["value"]


class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


class encryption:
    def encrypt_data(self, email):
        key_bytes = settings.EMAIL_ENCRYPTION_KEY.encode()
        fernet = Fernet(key_bytes)
        encoded_email = fernet.encrypt(email.encode())
        return base64.urlsafe_b64encode(encoded_email).decode()

    def decrypt_data(self, encoded_email):
        key_bytes = settings.EMAIL_ENCRYPTION_KEY.encode()
        fernet = Fernet(key_bytes)
        decoded_email = fernet.decrypt(base64.urlsafe_b64decode(encoded_email.encode()))
        return decoded_email.decode()


def build_absolute_uri(path, args):
    return f"{settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL}://{settings.ENVIRONMENT_DOMAIN}{reverse(path, args=args)}"


def evaluation_random_generator(
    modeladmin=None, request=None, queryset=None, not_random=False
):
    if settings.ALLOW_AUTO_EVAL:
        from scoring.models import SubAnswer, Answer

        queryset = queryset.prefetch_related(
            Prefetch(
                "answers",
                queryset=Answer.objects.select_related(
                    "question", "evaluation", "choice__question"
                ).prefetch_related(
                    "question__subquestions", "question__choices", "subanswers"
                ),
            )
        )
        for evaluation in queryset:
            with transaction.atomic():
                for answer in evaluation.answers.all():
                    type = answer.question.get_types()
                    if "qcm" in type[0]:
                        answer.choice = (
                            not_random
                            and answer.question.choices.first()
                            or random.choice(answer.question.choices.all())
                        )
                        answer.save()
                    elif "valeur" in type[0] or "pourcentage" in type[0]:
                        if len(type) == 1:
                            answer.value = not_random and 10 or random.randint(0, 10000)
                        else:
                            try:
                                answer.value = (
                                    not_random and 10 or float(random.choice(type[1:]))
                                )
                            except ValueError:
                                answer.value = (
                                    not_random and 10 or random.randint(0, 10000)
                                )
                        answer.save()
                    elif "subquestion" in type[0]:
                        if len(type) > 1 and "qcm" in type[1]:
                            for sq in answer.question.subquestions.all():
                                sub_answer, _ = SubAnswer.objects.update_or_create(
                                    subquestion=sq,
                                    answer=answer,
                                    defaults={
                                        "value": not_random
                                        and 1
                                        or random.randint(0, 1)
                                    },
                                )
                        else:
                            subquestions = answer.question.subquestions.all()
                            if "pourcentage" in subquestions[0].ui_type:
                                max_value = 100
                                sub_answer = None
                                for sq in subquestions:
                                    val = random.randint(0, max_value)
                                    max_value -= val
                                    sub_answer, _ = SubAnswer.objects.select_related(
                                        "subquestion",
                                        "answer__question",
                                        "answer__evaluation",
                                    ).update_or_create(
                                        subquestion=sq,
                                        answer=answer,
                                        defaults={
                                            "value": not_random
                                            and 33.3333333
                                            or random.randint(0, val)
                                        },
                                    )
                                if sub_answer and not not_random:
                                    sub_answer.value += max_value
                                    sub_answer.save()
                            else:
                                for sq in subquestions:
                                    sub_answer, _ = SubAnswer.objects.select_related(
                                        "subquestion",
                                        "answer__question",
                                        "answer__evaluation",
                                    ).update_or_create(
                                        subquestion=sq,
                                        answer=answer,
                                        defaults={
                                            "value": not_random
                                            and 10
                                            or random.randint(0, 10000)
                                        },
                                    )
    elif request:
        from django.contrib import messages

        messages.add_message(
            request,
            messages.ERROR,
            "Les évaluations automatiques sont désactivées. Pour pouvoir remplir automatiquement les évaluations, "
            "passez le paramètre ALLOW_AUTO_EVAL à true sur Heroku.",
        )


evaluation_random_generator.short_description = "Remplir aléatoirement l'évaluation"


class CSSJsAdminMixin(object):
    # Add css to admin
    class Media:
        css = {
            "all": ("admin/admin.css",),
        }
        js = ["admin/admin.js"]


def mixity_bench(callback):
    def wrapper(*args, **kwargs):
        import cProfile, pstats, io

        pr = cProfile.Profile()
        pr.enable()
        res = callback(*args, **kwargs)
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
        ps.print_stats("mixity", 0.2)
        return res

    return wrapper


@job("default")
def segment_tracking_job(user_id, event_name, event_content):
    user = MixityUser.objects.get(id=user_id)
    event_content = json.loads(event_content)
    if not settings.SEGMENT_KEY:
        return
    if (
        user.last_segment_identify is None
        or localtime(user.last_segment_identify).date() != timezone.now().date()
    ):
        identify = SegmentAPI().identify(
            str(user.uuid),
            {
                "email": user.email,
                "name": user.__str__(),
                "is_solver": (
                    user.structures.first().is_solver
                    if user.structures.first()
                    else False
                ),
            },
        )
        if identify.status_code >= 400:
            logging.exception(
                f"Identify failed for user {user.email} : {identify.text}"
            )
        user.last_segment_identify = timezone.now()
        user.save()
    track = SegmentAPI().track(str(user.uuid), event_name, event_content)

    if track.status_code >= 400:
        logging.exception(f"Track failed for user {user.email} : {track.text}")


def segment_tracking(user, event_name, event_content=None):
    if event_content is None:
        event_content = {
            "email": user.email,
            "name": user.__str__(),
            "event": event_name,
        }
    try:
        segment_tracking_job.delay(user.id, event_name, json.dumps(event_content))
    except Exception:
        pass
