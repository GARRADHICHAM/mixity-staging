from rest_framework import viewsets
from rest_framework import permissions
from .serializers import DiversityLabelSerializer
from .filters import DiversityLabelFilter
from .models import DiversityLabel

from django_filters.rest_framework import DjangoFilterBackend


class DiversityLabelViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows labels to be queryered
    """

    queryset = DiversityLabel.objects.all()
    serializer_class = DiversityLabelSerializer
    filterset_class = DiversityLabelFilter
    filter_backends = [DjangoFilterBackend]
    http_method_names = ["get"]
    permission_classes = [permissions.IsAuthenticated]
