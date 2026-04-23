from rest_framework import serializers
from accounts.models import Structure, DiversityLabel, BusinessLine


class StructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = ["juridic_name", "commercial_name"]


class DiversityLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiversityLabel
        fields = ["id", "name"]


class BusinessLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessLine
        fields = ["id", "name", "slug", "is_private"]
