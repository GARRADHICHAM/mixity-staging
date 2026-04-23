from rest_framework import serializers
from act.models import (
    Solution,
    SolutionKeyword,
    Solver,
    BestPractice,
    BestPracticeKeyword,
    BestPracticeType,
    BestPracticePublic,
    BestPracticeSize,
    BestPracticeOrganizationType,
    Elearning,
    ElearningEvaluationMethod,
    ElearningKeyword,
    ElearningNotion,
)
from accounts.models import Structure, Entity
from scoring.models import Category, SubCategory
from mixity.models import (
    Language,
    SolutionFormat,
)


class SolutionKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolutionKeyword
        fields = ["pk", "label"]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["pk", "label", "code", "is_enabled", "is_google_sheet_lang"]


class SolutionFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolutionFormat
        fields = ["pk", "label"]


# class SubCategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SubCategory
#         fields = ["pk", "name", "color"]


class CategorySerializer(serializers.ModelSerializer):
    # subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["pk", "name", "color", "slug"]


class SolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solution
        fields = [
            "pk",
            "title",
            "summary",
            "photo",
            "referent",
            "email",
            "description",
            "country",
            "region",
            "price_desc",
            "public",
            "objective",
            "format_session",
            "solver",
            "categories",
            "subcategories",
            "languages",
            "keywords",
            "solution_formats",
            "structures",
            "users_tracked",
            "users_tracked_contact",
        ]


class StructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = ["pk", "juridic_name", "logo", "slug", "favorite_solutions"]


class SolversSerializer(serializers.ModelSerializer):
    structure = StructureSerializer(read_only=True)

    class Meta:
        model = Solver
        fields = ["pk", "structure"]


class SolverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solver
        fields = ["pk", "is_validated_by_admin"]


class BestPracticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BestPractice
        fields = [
            "pk",
            "label",
            "structure",
            "country",
            "logo",
            "deployment_date",
            "summary",
            "description",
            "setting_up",
            "difficulties",
            "advice",
            "testimony",
            "results",
            "publics",
            "type",
            "size",
            "categories",
            "subcategories",
            "keywords",
            "organization_type",
        ]


class BestPracticeKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BestPracticeKeyword
        fields = ["pk", "label"]


class BestPracticeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BestPracticeType
        fields = ["pk", "label"]


class BestPracticePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BestPracticePublic
        fields = ["pk", "label"]


class BestPracticeSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BestPracticeSize
        fields = ["pk", "label"]


class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BestPracticeOrganizationType
        fields = ["pk", "label"]


class EntityFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ["pk", "name", "slug", "members", "favorite_best_practices"]


class ElearningEvaluationMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElearningEvaluationMethod
        fields = ["slug", "label"]


class ElearningKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElearningKeyword
        fields = ["slug", "label"]


class ElearningNotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElearningNotion
        fields = ["slug", "label"]


class ElearningSerializer(serializers.ModelSerializer):
    notions = ElearningNotionSerializer(many=True)
    category = CategorySerializer(many=True)
    evaluation_methods = ElearningEvaluationMethodSerializer(many=True)
    keywords = ElearningKeywordSerializer(many=True)
    languages = LanguageSerializer(many=True)

    class Meta:
        model = Elearning
        fields = [
            "slug",
            "title",
            "description",
            "summary",
            "photo",
            "languages",
            "time",
            "target",
            "video",
            "objective",
            "added_value",
            "keywords",
            "is_certifiable",
            "evaluation_methods",
            "category",
            "notions",
        ]
