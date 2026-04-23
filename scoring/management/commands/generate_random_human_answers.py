import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Prefetch
from django.conf import settings
from django.db import connection

from accounts.vocabularies import CIVILITY_CHOICES, AGE_CHOICES, CAMPUS_CHOICE
from scoring.models import (
    Evaluation,
    Answer,
    ScoreCategory,
    SubAnswer,
    Collaborator,
    Question,
    QuestionTag,
)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("evaluation_id", type=int, help="evaluation_id")
        parser.add_argument("number", type=int, help="number")

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if settings.ENVIRONMENT_NAME.lower() not in [
            "developement",
            "staging",
            "test",
            "demo",
        ]:
            raise Exception("Can't use this command in production !")
        evaluation = (
            Evaluation.objects.select_related(
                "sheet", "entity__entity_level__structure"
            )
            .prefetch_related(
                "human_criteria__choices",
                Prefetch(
                    "sheet__questions",
                    queryset=Question.objects.select_related("subcategory", "category")
                    .prefetch_related("subquestions__choices", "choices")
                    .filter(display=True),
                ),
            )
            .get(id=kwargs["evaluation_id"])
        )
        question_tags = {}
        if evaluation.entity.entity_level.structure.category == "school":
            question_tags = {tag.name: tag for tag in QuestionTag.objects.all()}
        for i in range(kwargs["number"]):
            status = None
            tag = None
            if evaluation.entity.entity_level.structure.category == "school":
                status = CAMPUS_CHOICE[random.randint(0, 4)][0]
                tag = question_tags.get(status.split("__")[0])
            collaborator = Collaborator.objects.create(
                civility=CIVILITY_CHOICES[random.randint(0, 3)][0],
                age=AGE_CHOICES[random.randint(0, 3)][0],
                status=status,
                tag=tag,
                evaluation=evaluation,
            )
            for criteria in evaluation.human_criteria.all():
                collaborator.human_criteria_choices.add(
                    random.choice(criteria.choices.all())
                )
            questions_qs = evaluation.sheet.questions.select_related(
                "subcategory", "category"
            ).all()
            answers_with_subanswers = []
            answers_to_create = []
            subanswers_to_create = []
            categories = set()
            for question in questions_qs:
                categories.add(question.category)
                answer = Answer(
                    evaluation=evaluation,
                    question=question,
                    collaborator=collaborator,
                    display=True,
                )
                if question.ui_type == "text":
                    answer.collaborator_comment = "This is my comment"
                elif question.ui_type == "select":
                    answer.choice = random.choice(question.choices.all())
                else:
                    subanswers = self.generate_subanswers(question, answer)
                    if len(subanswers):
                        answers_with_subanswers.append(answer)
                    subanswers_to_create += subanswers
                answers_to_create.append(answer)
            Answer.objects.bulk_create(answers_to_create)
            SubAnswer.objects.bulk_create(subanswers_to_create)
            # Note: answer.choice affectations will occur upon evaluation.do_user_validation()
            evaluation.do_initialize_score_categories(categories)

    def generate_subanswers(self, question, answer):
        subanswers = []
        subquestions = question.subquestions.all()
        if question.ui_type == "sq_select":
            for subquestion in subquestions:
                subanswers.append(
                    SubAnswer(
                        subquestion=subquestion,
                        answer=answer,
                        choice=random.choice(subquestion.choices.all()),
                    )
                )
        elif question.ui_type == "sq_dual":
            infirst = random.choice(subquestions)
            for subquestion in subquestions:
                choice = None
                if subquestion == infirst:
                    choice = subquestion.choices.all()[0]
                elif random.randint(0, 1) == 1:
                    choice = subquestion.choices.all()[1]
                else:
                    continue
                subanswers.append(
                    SubAnswer(subquestion=subquestion, answer=answer, choice=choice)
                )
        elif question.ui_type == "sq_qcm":
            for subquestion in subquestions:
                subanswers.append(
                    SubAnswer(
                        subquestion=subquestion,
                        answer=answer,
                        value=random.randint(0, 1),
                    )
                )
        return subanswers
