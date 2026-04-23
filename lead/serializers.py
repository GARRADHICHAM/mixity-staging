from rest_framework import serializers
from lead.models import Objective, LeadAction, ActionKpi, GenericKpi
from scoring.models import Category, SubCategory
from accounts.models import Structure, Membership, MixityUser, Entity
from accounts.vocabularies import ACTION_STATUS


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ["is_owner", "is_reader"]


class GenericKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericKpi
        fields = ["pk", "label", "unit", "subcategories"]


class KpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionKpi
        fields = [
            "pk",
            "label",
            "generic_kpi",
            "unit",
            "value",
            "goal",
            "subcategory",
            "action",
            "creation_user",
            "creation_entity",
            "last_modification_user",
        ]


class ActionSerializer(serializers.ModelSerializer):
    kpis = KpiSerializer(many=True, read_only=True)

    class Meta:
        model = LeadAction
        fields = [
            "pk",
            "label",
            "status",
            "action_date",
            "budget",
            "referent",
            "objective",
            "comment",
            "kpis",
            "creation_user",
            "creation_entity",
            "last_modification_user",
            "height",
        ]


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ["pk", "name"]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["pk", "name", "color", "subcategories"]


class ObjectiveSerializer(serializers.ModelSerializer):
    actions = ActionSerializer(many=True, read_only=True)

    class Meta:
        model = Objective
        fields = [
            "pk",
            "label",
            "category",
            "subcategory",
            "structure",
            "entity",
            "actions",
            "progress_bar",
            "total_budget",
            "creation_user",
            "last_modification_user",
            "height",
        ]


class MixityUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MixityUser
        fields = ["pk", "username", "first_name", "last_name", "kpis_tracked"]


class StructureSerializer(serializers.ModelSerializer):
    members = MixityUserSerializer(many=True, read_only=True)

    class Meta:
        model = Structure
        fields = ["pk", "slug", "evaluations", "members"]
