import django_filters

from .models import DiversityLabel


class DiversityLabelFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = DiversityLabel
        fields = ["name"]
