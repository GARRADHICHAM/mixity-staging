import logging

from mixity.utils import encryption
from urllib.parse import unquote_plus, quote_plus

from django.db.models import Prefetch
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.views.generic import UpdateView, DetailView, TemplateView
from uuid import UUID

from accounts.models import HumanCriteriaChoice
from scoring.models import (
    Evaluation,
    Question,
    Collaborator,
    MixityUser,
    Answer,
    Choice,
    QuestionTag,
    SubQuestion,
    SubquestionChoice,
    SubAnswer,
    ScoreCategory,
)
from scoring.serializers import QuestionSheetSerializer, QuestionSerializer
from mixity.serializers import LazyEncoder
import json
from django.shortcuts import get_object_or_404, redirect
from django.core.signing import BadSignature
from django import forms
from django.db import transaction, connection
from accounts.vocabularies import (
    CAMPUS_CHOICE,
    SERVICE_CHOICES,
    CIVILITY_CHOICES,
    AGE_CHOICES,
)
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)


class SignedEvaluationMixin:
    # Add signed pk. Useful for Human URL
    def get_object(self, queryset=None):
        try:
            pk = Evaluation.signer.unsign(self.kwargs["signed_pk"])
        except BadSignature:
            return get_object_or_404(Evaluation, pk=0)
        return get_object_or_404(
            Evaluation.objects.select_related(
                "sheet", "entity__entity_level__structure"
            ).prefetch_related(
                Prefetch(
                    "sheet__questions",
                    queryset=Question.objects.select_related("subcategory", "category")
                    .prefetch_related("subquestions__choices", "choices")
                    .filter(display=True),
                ),
            ),
            pk=pk,
        )


class CollaboratorEvaluationLandingView(SignedEvaluationMixin, DetailView):
    template_name = "collaborators_evaluation_landing.html"
    model = Evaluation

    def dispatch(self, request, *args, **kwargs):
        evaluation = self.get_object()
        response = super().dispatch(request, *args, **kwargs)
        if (
            evaluation.need_auth == True
            and request.user.is_authenticated
            and getattr(request.user, "collaborator", None) != None
            and request.user.collaborator.evaluation == evaluation
        ) or (evaluation.need_auth == False):
            if (
                evaluation.need_auth == True
                and request.user.is_authenticated
                and request.user.collaborator.answers.count() > 0
            ):
                return redirect(evaluation.collaborator_end_url)
            return response
        else:
            return redirect("/")


class CollaboratorEvaluationEndView(SignedEvaluationMixin, DetailView):
    template_name = "collaborators_evaluation_end.html"
    model = Evaluation


# Outdated. Form wasn't checking anything, we were already checking in the form_valid method of the view.
# Useless queries
# class CollaboratorEvaluationForm(forms.ModelForm):
#     age = forms.CharField(required=False)
#     civility = forms.CharField(required=False)
#     service = forms.CharField(required=False)
#     status = forms.CharField(required=False)
#
#     def __init__(self, *args, **kwargs):
#         self.evaluation = kwargs.pop("evaluation")
#
#         for criteria in self.evaluation.human_criteria.all():
#             field = forms.CharField(
#                 label=criteria.label,
#                 required=False,
#             )
#             self.base_fields[f"criteria_{criteria.id}"] = field
#         questions = self.evaluation.sheet.questions.all()
#         subquestions = SubQuestion.objects.filter(question__in=questions)
#         subquestions_per_question = {}
#         for sq in subquestions:
#             if sq.question_id not in subquestions_per_question:
#                 subquestions_per_question[sq.question_id] = []
#             subquestions_per_question[sq.question_id].append(sq)
#         subquestions_with_choices = set(
#             SubquestionChoice.objects.filter(
#                 subquestion__question__in=questions
#             ).values_list("subquestion_id", flat=True)
#         )
#         for question in questions:
#             if question.id in subquestions_per_question:
#                 for subquestion in subquestions_per_question[question.id]:
#                     field = forms.CharField(
#                         label=question.label,
#                         required=False,
#                     )
#                     additionnal_str = ""
#                     if subquestion.id in subquestions_with_choices:
#                         additionnal_str = "_id"
#                     else:
#                         additionnal_str = "_value"
#                     self.base_fields[
#                         f"answer_{str(question.id)}_{str(subquestion.id)}{additionnal_str}"
#                     ] = field
#             else:
#                 field = forms.CharField(
#                     label=question.label,
#                     required=False,
#                 )
#                 self.base_fields[f"answer_{str(question.id)}"] = field
#         super().__init__(*args, **kwargs)
#
#     class Meta:
#         model = Evaluation
#         fields = []


class CollaboratorEvaluationAbstractView(SignedEvaluationMixin, DetailView):
    model = Evaluation

    def __init__(self):
        super(CollaboratorEvaluationAbstractView, self).__init__()
        self._evaluation = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs().copy()
        kwargs["evaluation"] = self.get_object()
        return kwargs

    def get_object(self, queryset=None):
        if not self._evaluation:
            pk = Evaluation.signer.unsign(self.kwargs["signed_pk"])
            self._evaluation = get_object_or_404(
                Evaluation.objects.select_related(
                    "sheet",
                    "entity__entity_level__structure",
                ).prefetch_related(
                    "sheet__questions__subquestions__choices",
                    "sheet__questions__choices",
                    "sheet__questions__subcategory",
                    "sheet__questions__category",
                    "sheet__questions__mandatory_tags",
                    "sheet__questions__forbidden_tags",
                ),
                pk=pk,
            )
        return self._evaluation


class CollaboratorEvaluationFillView(CollaboratorEvaluationAbstractView):
    template_name = "collaborators_evaluation_fill.html"

    def get_success_url(self):
        return self.get_object().collaborator_end_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if (
            self.get_object().is_validated_by_user
            or self.get_object().is_validated_by_admin
        ):
            return context
        # serializer = QuestionSheetSerializer(self.get_object().sheet)
        data = dict()
        data["slug"] = self.get_object().sheet.slug
        data["questions"] = []
        form = [
            {
                "label": _("Genre"),
                "slug": "civility",
                "helper": _("Votre genre"),
                "values": CIVILITY_CHOICES,
            },
            {
                "label": _("Âge"),
                "slug": "age",
                "helper": _("Votre tranche d'âge"),
                "values": AGE_CHOICES,
            },
        ]
        if self._evaluation.entity.entity_level.structure.category == "school":
            form.append(
                {
                    "label": _("Votre statut"),
                    "slug": "status",
                    "helper": _("Votre statut au sein du campus"),
                    "values": CAMPUS_CHOICE,
                }
            )
        for criteria in (
            self._evaluation.human_criteria.filter(is_csv_imported=False)
            .prefetch_related(
                Prefetch(
                    "choices",
                    queryset=HumanCriteriaChoice.objects.filter(
                        criteria__evaluation=self._evaluation
                    )
                    .prefetch_related(
                        "mandatory_questions", "forbidden_questions", "tags"
                    )
                    .order_by("order", "id"),
                ),
                "mandatory_tags",
                "forbidden_tags",
            )
            .all()
        ):
            values = []
            for choice in criteria.choices.all():
                values.append(
                    (
                        str(choice.id),
                        choice.label,
                        [q.google_sheets_id for q in choice.mandatory_questions.all()],
                        [q.google_sheets_id for q in choice.forbidden_questions.all()],
                        [tag.name for tag in choice.tags.all()],
                    )
                )
            form.append(
                {
                    "label": criteria.label,
                    "slug": criteria.label,
                    "id": criteria.id,
                    "helper": "",
                    "values": tuple(values),
                    "allow_multiple": criteria.allow_multiple,
                    "mandatory_tags": [
                        tag.name for tag in criteria.mandatory_tags.all()
                    ],
                    "forbidden_tags": [
                        tag.name for tag in criteria.forbidden_tags.all()
                    ],
                }
            )
        data["questions"].insert(
            0,
            {
                "type": "profile",
                "uitype": "profile",
                "subcategory": {"slug": "profile", "name": _("Profil")},
                "form": form,
            },
        )
        context["questionnaire"] = json.dumps(data, cls=LazyEncoder)  # content
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """{'age': 'more_40', 'civility': 'man', 'service': 'production', 'position': 'executive',
        'answer_207': 'Moyenne', 'answer_208': "Ni d'accord, ni pas d'accord",
        'answer_209': "Ni d'accord, ni pas d'accord", 'answer_210': "Ni d'accord, ni pas d'accord",
        'answer_211': "Ni d'accord, ni pas d'accord", 'answer_212': 'Non', 'answer_213': 'Non',
        'answer_214': 'Non', 'answer_215': 'Non', 'answer_216': 'Non', 'answer_217': 'Non', 'answer_218': 'Non',
        'answer_219': 'Non', 'answer_220': 'Non', 'answer_221': 'Non', 'answer_222': '', 'answer_223': '',
        'answer_224': '', 'answer_225': '', 'answer_226': '', 'answer_227': '', 'answer_228': '', 'answer_229': '',
         'answer_230': '', 'answer_231': '', 'answer_232': 'Non', 'answer_233': 'Non', 'answer_234': 'Non',
          'answer_236': 'fgh', 'answer_237': 'ghj'}"""

        try:
            UUID(request.POST.get("uuid"), version=4)
        except Exception:
            logger.exception("Someone sent a request with an invalid UUID (see POST)")
            return redirect(self.get_success_url())

        if (
            request.user.is_authenticated
            and getattr(request.user, "collaborator", None) != None
            and request.user.collaborator.evaluation == self.get_object()
        ):
            collaborator = request.user.collaborator
            collaborator.age = request.POST.get("age")
            collaborator.service = request.POST.get("service")
            collaborator.civility = request.POST.get("civility")
            collaborator.status = request.POST.get("status")
            collaborator.save()

        else:
            collaborator, created = Collaborator.objects.get_or_create(
                uuid=request.POST.get("uuid"),
                defaults={
                    "age": request.POST.get("age"),
                    "service": request.POST.get("service"),
                    "civility": request.POST.get("civility"),
                    "status": request.POST.get("status"),
                    "evaluation": self.get_object(),
                },
            )
            if not created:
                collaborator.human_criteria_choices.clear()
                collaborator.answers.all().delete()
        if request.POST.get("status"):
            collaborator.tag = QuestionTag.objects.get(
                name=request.POST.get("status").split("__")[0]
            )
        criteria_choices = []
        CriteriaCollaboratorThrough = collaborator.human_criteria_choices.through
        for criteria in self.get_object().human_criteria.all():
            criteria_fields = request.POST.get(f"criteria_{criteria.id}")
            if criteria_fields:
                criteria_fields = criteria_fields.split(",")
                for criteria_field in criteria_fields:
                    criteria_choices.append(
                        CriteriaCollaboratorThrough(
                            collaborator_id=collaborator.id,
                            humancriteriachoice_id=int(criteria_field),
                        )
                    )
        CriteriaCollaboratorThrough.objects.bulk_create(criteria_choices)
        collaborator.save()
        answers_with_subanswers = {}
        categories = {}
        questions_qs = self.get_object().sheet.questions.all()
        questions = {q.id: q for q in questions_qs}
        subquestions_qs = SubQuestion.objects.filter(question__in=questions_qs)
        subquestions = {sq.id: sq for sq in subquestions_qs}
        subquestions_choices = {
            sqc.id: sqc
            for sqc in SubquestionChoice.objects.filter(subquestion__in=subquestions_qs)
        }
        answers_to_create = {}
        subanswers_to_create = []

        def get_answer(q):
            if q.id not in answers_to_create:
                answers_to_create[question.id] = Answer(
                    evaluation=self.get_object(),
                    question=q,
                    collaborator=collaborator,
                    display=True,
                )
            return answers_to_create[q.id]

        for key, value in request.POST.items():
            if "answer" in key and value:
                split = key.split("_")
                if len(split) < 2:
                    logger.warning(f"Wrong answer provided, got {key}")
                    continue
                question_id = int(split[1])
                if question_id not in questions:
                    continue
                question = questions[question_id]
                categories[
                    question.category
                ] = question.category
                if len(split) <= 2:
                    if question.ui_type == Question.TEXT_UI_TYPE[0]:
                        get_answer(question).collaborator_comment = value
                    else:
                        choice = (
                            Choice.objects.select_related("question")
                            .filter(label=value, question=question)
                            .first()
                        )
                        if choice:
                            get_answer(question).choice = choice
                            if question.google_sheets_id == 51015 and value == "Oui":
                                collaborator.is_lgbt = True
                                collaborator.save()
                elif len(split) == 3:
                    if split[2] == "consent":
                        answer = get_answer(question)
                        answer.allow_raw_usage = True
                elif len(split) == 4:
                    if not int(split[2]) in subquestions:
                        continue
                    subquestion = subquestions[int(split[2])]
                    answer = get_answer(question)
                    answers_with_subanswers[question.id] = answer
                    if split[3] == "id":
                        sqc_id = int(value)
                        if sqc_id not in subquestions_choices:
                            continue

                        choice = subquestions_choices[sqc_id]
                        subanswers_to_create.append(
                            SubAnswer(
                                subquestion=subquestion, answer=answer, choice=choice
                            )
                        )
                    else:
                        subanswers_to_create.append(
                            SubAnswer(
                                subquestion=subquestion, answer=answer, value=int(value)
                            )
                        )
        Answer.objects.bulk_create(answers_to_create.values())
        SubAnswer.objects.bulk_create(subanswers_to_create)
        for answer in answers_with_subanswers.values():
            answer.choice = answer.question.get_choice_from_subanswers(
                answer.get_ordered_subanswers, self._evaluation, answer
            )
            answer.save()
        self.get_object().do_initialize_score_categories(categories)
        return redirect(self.get_success_url())


class HumanSheetApiView(CollaboratorEvaluationAbstractView):
    """
    Endpoint to retrieve Human Question Sheet depending on criteria answers
    """

    def get(self, request, *args, **kwargs):
        get_object_or_404(Evaluation, pk=0)
        return JsonResponse({})

    def post(self, request, *args, **kwargs):
        evaluation = self.get_object()
        if not evaluation:
            return JsonResponse({"error": "Invalid evaluation"})
        params = json.loads(request.body.decode("utf-8"))
        mandatory_questions = (
            "mandatory_questions" in params and params["mandatory_questions"] or []
        )
        forbidden_questions = (
            "forbidden_questions" in params and params["forbidden_questions"] or []
        )
        criteria_tags = "criteria_tags" in params and params["criteria_tags"] or []
        data = {
            "questions": [
                QuestionSerializer(question).data
                for question in evaluation.get_questions_human(
                    mandatory_questions, forbidden_questions, criteria_tags
                )
            ]
        }

        for question in data["questions"]:
            question["mandatory_tags"] = [
                tag for tag in question["mandatory_tags"] if tag.startswith("campus_")
            ]
            question["forbidden_tags"] = [
                tag for tag in question["forbidden_tags"] if tag.startswith("campus_")
            ]
        for key in range(len(data["questions"])):
            data["questions"][key]["subcategory"]["name"] = _(
                data["questions"][key]["subcategory"]["name"]
            )
            data["questions"][key]["category"]["name"] = _(
                data["questions"][key]["category"]["name"]
            )
        return JsonResponse(data)
