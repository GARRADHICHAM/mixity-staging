from django.db.models import Count

from mixity.testing import TestCase
from scoring.models import (
    Answer,
    Category,
    Collaborator,
    SubCategory,
    Evaluation,
    Question,
    QuestionSheet,
    QuestionSheetType,
    count_collaborators_with_answers,
)


class CountCollaboratorsWithAnswersTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        business_line = cls.make_business_line("bl", "Secteur", "Sector")
        structure = cls.make_structure("Société", "societe", 100, "Diversity", business_line)
        entity = cls.make_entity(structure.juridic_name, cls.make_entity_level(structure, "Groupe", 0), 100)
        sheet_type = QuestionSheetType.objects.create(slug="evaluation_collaborateurs_360", name="360", is_collaborator=True)
        sheet = QuestionSheet.objects.create(type=sheet_type, slug="s", version=0.1)
        cls.evaluation = Evaluation.objects.create(sheet=sheet, entity=entity)
        cls.make_categories()
        category, subcategory = Category.objects.first(), SubCategory.objects.first()
        cls.q1 = Question.objects.create(label="Q1", category=category, subcategory=subcategory)
        cls.q2 = Question.objects.create(label="Q2", category=category, subcategory=subcategory)

        cls.answered_once = Collaborator.objects.create(evaluation=cls.evaluation)
        cls.answered_twice = Collaborator.objects.create(evaluation=cls.evaluation)
        cls.silent = Collaborator.objects.create(evaluation=cls.evaluation)
        Answer.objects.create(evaluation=cls.evaluation, question=cls.q1, collaborator=cls.answered_once)
        Answer.objects.create(evaluation=cls.evaluation, question=cls.q1, collaborator=cls.answered_twice)
        Answer.objects.create(evaluation=cls.evaluation, question=cls.q2, collaborator=cls.answered_twice)

        other = Evaluation.objects.create(sheet=sheet, entity=entity)
        cls.other = other
        Collaborator.objects.create(evaluation=other)

    def old_way(self, collaborators):
        return collaborators.annotate(num_answers=Count("answers")).filter(num_answers__gt=0).count()

    def test_counts_each_collaborator_with_at_least_one_answer_once(self):
        # 2 collaborateurs ont répondu (l'un à 2 questions) ; le troisième n'a rien répondu
        self.assertEqual(count_collaborators_with_answers(self.evaluation.collaborators), 2)

    def test_same_result_as_the_previous_implementation(self):
        for evaluation in (self.evaluation, self.other):
            with self.subTest(evaluation=evaluation.pk):
                self.assertEqual(
                    count_collaborators_with_answers(evaluation.collaborators),
                    self.old_way(evaluation.collaborators),
                )

    def test_evaluation_without_answers_counts_zero(self):
        self.assertEqual(count_collaborators_with_answers(self.other.collaborators), 0)

    def test_filtered_queryset_is_respected(self):
        only_silent = Collaborator.objects.filter(pk=self.silent.pk)
        self.assertEqual(count_collaborators_with_answers(only_silent), 0)
        self.assertEqual(self.evaluation.get_filtered_collaborators_count(self.evaluation.collaborators.all()), 2)

    def test_answer_count_property_uses_the_same_rule(self):
        self.assertEqual(self.evaluation.answer_count, 2)
