from rest_framework import serializers
from scoring.models import (
    QuestionSheet,
    QuestionSheetType,
    Evaluation,
    Question,
    Answer,
    Choice,
    QuestionTag,
    SubCategory,
    Category,
    Collaborator,
    SubQuestion,
    SubquestionChoice,
    Indicator,
    IndicatorType,
    Comment,
    GeneralAnalysis,
    Entity,
)
from accounts.serializers import StructureSerializer
from mixity.serializers import (
    ProductSerializer,
    SubscriptionPackSerializer,
    SubscriptionOptionSerializer,
    NestedEntitySerializer,
)
from accounts.vocabularies import (
    POSITION_CHOICES,
    SERVICE_CHOICES,
    CIVILITY_CHOICES,
    AGE_CHOICES,
)
from django.utils.translation import ugettext_lazy as _


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["slug", "name", "color"]


class CollaboratorSerializer(serializers.ModelSerializer):
    civility = serializers.CharField(source="get_civility_display")
    # position = serializers.CharField(source="get_position_display")
    service = serializers.CharField(source="get_service_display")
    age = serializers.CharField(source="get_age_display")
    is_lgbt = serializers.CharField(source="get_is_lgbt_display")

    class Meta:
        model = Collaborator
        fields = [
            "id",
            "civility",
            # "position",
            "service",
            "age",
            "is_lgbt",
        ]


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ["slug", "name"]


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "label", "value"]


class AnswerSerializer(serializers.ModelSerializer):
    choice = ChoiceSerializer()
    collaborator = CollaboratorSerializer()

    class Meta:
        model = Answer
        fields = [
            "id",
            "collaborator",
            "choice",
            "question",
            "value",
            "collaborator_comment",
        ]


class SubquestionChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubquestionChoice
        fields = [
            "label",
            "id",
        ]


class SubquestionSerializer(serializers.ModelSerializer):
    choices = SubquestionChoiceSerializer(many=True)

    class Meta:
        model = SubQuestion
        fields = ["label", "id", "choices"]


class TagsSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return instance.name

    class Meta:
        model = QuestionTag
        fields = ["name"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)
    subquestions = SubquestionSerializer(many=True)
    subcategory = SubCategorySerializer()
    category = CategorySerializer()
    mandatory_tags = TagsSerializer(many=True)
    forbidden_tags = TagsSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "label",
            "help_text",
            "type",
            "ui_type",
            "choices",
            "subcategory",
            "category",
            "google_sheets_id",
            "subquestions",
            "mandatory_tags",
            "forbidden_tags",
        ]


class CommentSerializer(serializers.ModelSerializer):
    subcategory = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "is_good",
            "description",
            "category",
            "subcategory",
        ]

    def get_subcategory(self, obj):
        return SubCategorySerializer(obj.question.subcategory).data

    def get_category(self, obj):
        return CategorySerializer(obj.question.category).data


class GeneralAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralAnalysis
        fields = "__all__"

    def to_representation(self, instance):
        if not instance:
            return None
        dimension_analysis = []
        for dim in instance.analysis_by_dimension.all():
            dimension_analysis.append(
                {
                    "category": dim.category.name,
                    "content": dim.content,
                    "pk": dim.category.pk,
                    "color": dim.category.color,
                }
            )

        result = {
            "general_analysis": instance.content[3:-4],
            "expert": {
                "first_name": instance.expert.first_name,
                "last_name": instance.expert.last_name,
                "title": instance.expert.title,
                "photo": instance.expert.photo.url,
                "comment": instance.comment[3:-4],
            },
            "dimension_analysis": dimension_analysis,
            "key_recommendations": [
                reco.content for reco in instance.key_recommendations.all()
            ],
            "best_practices": [
                best_practice.content
                for best_practice in instance.assess_best_practices.all()
            ],
        }
        return result


class NestedQuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "label",
            "help_text",
            "type",
            "answers",
            "choices",
            "google_sheets_id",
        ]


class NestedSubCategorySerializer(serializers.ModelSerializer):
    questions = NestedQuestionSerializer(many=True)

    class Meta:
        model = SubCategory
        fields = ["slug", "name", "questions"]


class QuestionSheetTypeSerializer(serializers.ModelSerializer):
    questionary = ProductSerializer()

    class Meta:
        model = QuestionSheetType
        fields = ["questionary"]


class QuestionSheetSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)
    type = QuestionSheetTypeSerializer()

    class Meta:
        model = QuestionSheet
        fields = ["slug", "questions", "type"]


class EvaluationSerializer(serializers.ModelSerializer):
    sheet = QuestionSheetSerializer()
    # subscription_option = SubscriptionOptionSerializer()
    collaborators = serializers.SerializerMethodField()
    collaborator_types = serializers.SerializerMethodField()
    entity = NestedEntitySerializer()
    subcategories = serializers.SerializerMethodField()
    scores = serializers.SerializerMethodField()

    def get_collaborators(self, obj):
        collaborators = Collaborator.objects.filter(
            answers__in=obj.answers.all()
        ).distinct()
        return CollaboratorSerializer(instance=collaborators, many=True).data

    def get_collaborator_types(self, obj):
        return [
            {
                "label": _("Civilité"),
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
            {
                "label": _("Votre Fonction"),
                "slug": "position",
                "helper": _("Votre fonction dans l'entreprise"),
                "values": POSITION_CHOICES,
            },
            {
                "label": "LGBT",
                "slug": "is_lgbt",
                "helper": "Votre fonction dans l'entreprise",
                "values": (
                    ("lgbt", _("LGBTQIA+")),
                    ("ally", _("Alliés (f/h/nb)")),
                    ("not_lgbt", _("Non LGBTQIA+")),
                    ("not_ally", _("Non allié")),
                ),
            },
        ]

    def get_scores(self, obj):
        values = obj.get_subcategories_values

        return {
            "score": values[0],
            "mean": values[1],
            "mean_in_business_line": values[2],
        }

    def get_subcategories(self, obj):
        subcategories = (
            SubCategory.objects.filter(questions__in=obj.sheet.questions.all())
            .distinct()
            .prefetch_related(
                "questions",
                "questions__choices",
                "questions__answers__choice",
                "questions__answers",
                "questions__answers__collaborator",
                "category",
            )
        )
        return NestedSubCategorySerializer(instance=subcategories, many=True).data

    class Meta:
        model = Evaluation
        fields = [
            "entity",
            "sheet",
            "collaborators",
            "collaborator_types",
            "subcategories",
            "scores",
        ]


class IndicatorSerializer(serializers.ModelSerializer):
    scores_json = serializers.SerializerMethodField(method_name="get_scores_json")

    def get_scores_json(self, instance):
        try:
            return instance.scores_json
        except Exception:
            return None

    class Meta:
        model = Indicator
        fields = [
            "scores_json",
        ]


class IndicatorSlugSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorType
        fields = [
            "slug",
        ]


class IndicatorParamSerializer(serializers.ModelSerializer):
    Indicator_Slug = serializers.SerializerMethodField()

    def get_Indicator_Slug(self, obj):
        result = IndicatorType.objects.filter(indicators=obj).first()
        if result:
            return IndicatorSlugSerializer(result).data
        else:
            return None

    class Meta:
        model = Indicator
        fields = [
            "title",
            "Indicator_Slug",
            "selector_labels",
            "selector",
            "displaying_params",
            "params",
            "get_colors",
        ]


class AllIndicatorSerializer(serializers.ModelSerializer):
    indicator_infos = serializers.SerializerMethodField()

    def get_indicator_infos(self, obj):
        result = Indicator.objects.filter(question=obj).first()
        if result:
            return IndicatorParamSerializer(result).data
        else:
            return None

    class Meta:
        model = Question
        fields = [
            "label",
            "google_sheets_id",
            "indicator_infos",
        ]


class EntityTreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = [
            "pk",
            "slug",
            "name",
        ]
