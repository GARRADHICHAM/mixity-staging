import copy

from django.core.management.base import BaseCommand
from django.db import transaction

from scoring.models import Evaluation, SubQuestion, SubAnswer


class Command(BaseCommand):
    """
    Fix a given evaluation which as started before question 2021018 was a SubAnswer type
    """

    def add_arguments(self, parser):
        parser.add_argument("evaluation_id", type=int, help="evaluation_id")
        parser.add_argument(
            "--both",
            action="store_true",
            default=False,
            help="add both subquestion",
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        evaluation = Evaluation.objects.get(id=kwargs["evaluation_id"])
        both_subquestion = kwargs["both"]
        answers = evaluation.answers.filter(
            question__google_sheets_id=2021018, subanswers__isnull=True
        ).select_related("choice")
        agissement = SubQuestion.objects.get(id=638)
        violence = SubQuestion.objects.get(id=639)
        for answer in answers:
            choice_agissement = agissement.choices.get(label_fr=answer.choice.label_fr)
            choice_violence = violence.choices.get(label_fr=answer.choice.label_fr)
            SubAnswer.objects.create(
                subquestion_id=638, answer_id=answer.id, choice_id=choice_agissement.id
            )
            if both_subquestion:
                SubAnswer.objects.create(
                    subquestion_id=639,
                    answer_id=answer.id,
                    choice_id=choice_violence.id,
                )
