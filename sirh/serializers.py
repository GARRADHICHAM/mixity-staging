from rest_framework import serializers

from sirh.models import ADPStatus


class ADPStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ADPStatus
        fields = [
            "pk",
            "processed_indicators",
            "unprocessed_indicator_types",
            "partial_indicators",
            "steps",
            "update_frequency",
            "last_updated",
            "update_automatically",
            "can_update",
        ]
