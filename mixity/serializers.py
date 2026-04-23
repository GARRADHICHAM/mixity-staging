from django.utils.functional import Promise
from django.utils.encoding import force_text
from rest_framework import serializers
from django.core.serializers.json import DjangoJSONEncoder
from lead.serializers import MixityUserSerializer

from accounts.models import Structure, EntityLevel, Entity, MixityUser, HumanCriteria
from accounts.vocabularies import (
    COLLABORATOR_STATISTICS_STATUSES,
    TYPE_CHOICES,
    SUMMARY_TYPE,
)
from scoring.models import (
    Evaluation,
    ReevaluationRequest,
    QuestionSheetType,
    QuestionSheet,
    Aim,
    Strength,
    Weakness,
    ScoreCategory,
    Category,
    SubCategory,
    CollaboratorsStatistics,
    IndicatorType,
    Indicator,
    Question, ScanCollaborator, Profile,
)
from lead.models import LeadAction
from lead.serializers import MembershipSerializer
from act.models import Solution
from subscriptions.models import SubscriptionPack, SubscriptionOption, Product


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["pk", "label", "slug", "is_active"]


class SubscriptionOptionToPackSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = SubscriptionOption
        fields = [
            "pk",
            "product",
            "start_date",
            "end_date",
            "is_active",
            "is_current",
        ]


class SubscriptionPackSerializer(serializers.ModelSerializer):
    options = SubscriptionOptionToPackSerializer(many=True)

    class Meta:
        model = SubscriptionPack
        fields = ["pk", "is_active", "options", "start_date", "end_date"]


class SubscriptionOptionSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    subscriptionPack = SubscriptionPackSerializer()

    class Meta:
        model = SubscriptionOption
        fields = [
            "pk",
            "product",
            "subscriptionPack",
            "start_date",
            "end_date",
            "is_active",
            "is_current",
        ]


class MixityUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MixityUser
        fields = ["pk", "username", "first_name", "last_name"]


class NestedEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ["pk", "slug"]


class EntityLevelSerializer(serializers.ModelSerializer):
    entities = NestedEntitySerializer(many=True)

    class Meta:
        model = EntityLevel
        fields = ["pk", "label", "entities", "level"]


class StructureSerializer(serializers.ModelSerializer):
    subscription_pack = SubscriptionPackSerializer(many=True)
    entity_level = EntityLevelSerializer(many=True)
    members = MixityUserSerializer(many=True, read_only=True)

    class Meta:
        model = Structure
        fields = [
            "pk",
            "slug",
            "juridic_name",
            "subscription_pack",
            "entity_level",
            "members",
            "favorite_solutions",
            "logo",
        ]


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ["pk", "name"]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["pk", "slug", "name", "color", "subcategories"]


class ScoreCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreCategory
        fields = [
            "pk",
            "category",
            "value",
            "mean_score",
            "mean_score_in_business_line",
            "display_value",
        ]


class AimSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField(method_name="get_category")
    subcategory = serializers.SerializerMethodField(method_name="get_subcategory_name")

    def get_category(self, instance):
        try:
            return instance.category.slug
        except:
            return None

    def get_subcategory_name(self, instance):
        try:
            return instance.subcategory.name
        except:
            return None

    class Meta:
        model = Aim
        fields = [
            "description",
            "subcategory",
            "category",
            "order",
            "custom_title",
        ]


class StrengthSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField(method_name="get_category")
    subcategory = serializers.SerializerMethodField(method_name="get_subcategory_name")

    def get_category(self, instance):
        try:
            return instance.category.slug
        except:
            return None

    def get_subcategory_name(self, instance):
        try:
            return instance.subcategory.name
        except:
            return None

    class Meta:
        model = Strength
        fields = [
            "description",
            "subcategory",
            "category",
            "order",
            "custom_title",
        ]


class WeaknessSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField(method_name="get_category")
    subcategory = serializers.SerializerMethodField(method_name="get_subcategory_name")

    def get_category(self, instance):
        try:
            return instance.category.slug
        except:
            return None

    def get_subcategory_name(self, instance):
        try:
            return instance.subcategory.name
        except:
            return None

    class Meta:
        model = Weakness
        fields = [
            "description",
            "subcategory",
            "category",
            "order",
            "custom_title",
        ]


class VersionsListSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return {"display_version": instance.display_version}

    class Meta:
        model = Evaluation
        fields = {}


class QuestionSheetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionSheetType
        fields = ["slug"]


class QuestionSheetSerializer(serializers.ModelSerializer):
    type = QuestionSheetTypeSerializer()

    class Meta:
        model = QuestionSheet
        fields = ["slug", "type"]


class EvaluationSerializer(serializers.ModelSerializer):
    scores_categories = serializers.SerializerMethodField()
    aims = serializers.SerializerMethodField()
    strengths = serializers.SerializerMethodField()
    weaknesses = serializers.SerializerMethodField()

    def get_scores_categories(self, obj):
        scores_categories = (
            ScoreCategory.objects.filter(evaluation=obj)
            .select_related("category")
        )
        return ScoreCategorySerializer(instance=scores_categories, many=True).data

    def get_aims(self, obj):
        aims = (
            Aim.objects.filter(evaluation=obj)
            .select_related("category", "subcategory")
        )
        return AimSerializer(instance=aims, many=True).data

    def get_strengths(self, obj):
        strengths = (
            Strength.objects.filter(evaluation=obj)
            .select_related("category", "subcategory")
        )
        return StrengthSerializer(instance=strengths, many=True).data

    def get_weaknesses(self, obj):
        weaknesses = (
            Weakness.objects.filter(evaluation=obj)
            .select_related("category", "subcategory")
        )
        return WeaknessSerializer(instance=weaknesses, many=True).data

    class Meta:
        model = Evaluation
        fields = [
            "pk",
            "global_score",
            "scores_categories",
            "get_footprint_url",
            "is_validated_by_user",
            "get_collaborators_profile_levels",
            "get_computed_values_by_skills",
            "get_computed_values_by_subcategories",
            "is_validated_by_admin",
            "public_display",
            "get_workforce_from_evaluation",
            "get_radar_data",
            "private_display",
            "collaborator_url",
            "is_category_evaluation",
            "get_global_score_delta",
            "modified_by_user_date",
            "is_human",
            "is_diag",
            "is_scan",
            "answer_count",
            "aims",
            "strengths",
            "weaknesses",
            "version",
            "display_version",
            "display_version_slugified",
            "is_started",
            "collaborators_mail",
            "collaborators_mail_object",
            "need_auth",
            "is_the_last_diag",
            "csrd_tag_on",
            "is_campus",
            "get_mean_score_in_business_line",
            "get_mean_score",
        ]


class ReevaluationRequestSerializer(serializers.ModelSerializer):
    structure = StructureSerializer()

    class Meta:
        model = ReevaluationRequest
        fields = [
            "structure",
            "request_date",
            "is_accepted",
            "reopening_date",
        ]


class AssessScoreCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    sibling = serializers.SerializerMethodField(method_name="get_serialized_sibling")
    evolution = serializers.SerializerMethodField(method_name="get_evolution")
    inner_percent = serializers.SerializerMethodField(method_name="get_inner_percent")
    between_percent = serializers.SerializerMethodField(method_name="get_between_percent")
    outter_percent = serializers.SerializerMethodField(method_name="get_outter_percent")
    evaluation = EvaluationSerializer()

    def get_evolution(self, instance):
        try:
            return instance.evolution
        except:
            return None

    def get_inner_percent(self, instance):
        try:
            return instance.inner_percent
        except:
            return None

    def get_outter_percent(self, instance):
        try:
            return instance.outter_percent
        except:
            return None

    def get_between_percent(self, instance):
        try:
            return instance.between_percent
        except:
            return None

    def get_serialized_sibling(self, instance):
        sibling_instance = instance.sibling
        serialized_sibling = AssessScoreCategorySerializer(sibling_instance)
        return serialized_sibling.data

    class Meta:
        model = ScoreCategory
        fields = [
            "pk",
            "category",
            "sibling",
            "value",
            "mean_score",
            "mean_score_in_business_line",
            "display_value",
            "evolution",
            "evaluation",
            "inner_percent",
            "between_percent",
            "outter_percent",
        ]


class EntitySerializer(serializers.ModelSerializer):
    structure = serializers.SerializerMethodField()
    members = MixityUserSerializer(many=True, read_only=True)
    evaluations = serializers.SerializerMethodField()
    last_global_evaluation = serializers.SerializerMethodField()
    last_human_evaluation = serializers.SerializerMethodField()

    def get_structure(self, obj):
        structure = (
            Structure.objects.filter(entity_level=obj.entity_level)
            .prefetch_related("entity_level__entities")
            .first()
        )
        return StructureSerializer(instance=structure).data

    def get_evaluations(self, obj):
        evaluations = Evaluation.objects.filter(entity=obj)
        return EvaluationSerializer(evaluations, many=True).data

    def get_last_global_evaluation(self, obj):
        last_eval = obj.last_global_evaluation
        return EvaluationSerializer(last_eval).data if last_eval else None

    def get_last_human_evaluation(self, obj):
        last_eval = obj.last_human_evaluation
        return EvaluationSerializer(last_eval).data if last_eval else None

    class Meta:
        model = Entity
        fields = [
            "pk",
            "slug",
            "name",
            "get_global_status",
            "get_human_status",
            "parent_entity",
            "members",
            "evaluations",
            "entity_level",
            "structure",
            "favorite_best_practices",
            "last_global_evaluation",
            "last_human_evaluation",
        ]


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadAction
        fields = ["pk", "label", "status", "action_date"]


class SolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solution
        fields = ["pk", "title", "summary", "photo"]


class CollaboratorsStatisticsSerializer(serializers.ModelSerializer):
    status_label = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = CollaboratorsStatistics
        fields = ["status", "name", "can_delete", "status_label", "summary", "type"]

    def get_status_label(self, obj):
        return COLLABORATOR_STATISTICS_STATUSES.get(obj.status, obj.status)

    def get_status(self, obj):
        return obj.status in COLLABORATOR_STATISTICS_STATUSES and obj.status or "error"

    def get_name(self, obj):
        for key, choice in TYPE_CHOICES:
            if key == obj.type:
                return choice

    def get_summary(self, obj):
        return SUMMARY_TYPE.get(obj.type)


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
    # indicator_infos = serializers.SerializerMethodField()

    # def get_indicator_infos(self, obj):
    #     result = Indicator.objects.first()
    #     if result:
    #         return IndicatorParamSerializer(result).data
    #     else:
    #         return None

    class Meta:
        model = Question
        fields = [
            "google_sheets_id",
        ]


class OneIndicatorSerializer(serializers.ModelSerializer):
    indicator_infos = serializers.SerializerMethodField()

    def get_indicator_infos(self, obj):
        result = Indicator.objects.filter(question=obj).first()
        if result:
            return IndicatorParamSerializer(result).data
        else:
            return None

    class Meta:
        model = Question
        fields = ["google_sheets_id", "indicator_infos"]

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["name", "strenght", "improvement", "type"]

class ScanCollaboratorSerializer(serializers.ModelSerializer):
    criteria_choices = serializers.SerializerMethodField()
    profile = ProfileSerializer()

    def get_criteria_choices(self, obj):
        result = []
        for cr_choice in obj.scan_criteria_choices.all():
            hc = HumanCriteria.objects.get(choices=cr_choice)
            result.append({hc.label: cr_choice.pk})
        return result
    class Meta:
        model = ScanCollaborator
        fields = ["id", "evaluation", "civility", "age", "job", "service", "criteria_choices", "tag", "profile"]
