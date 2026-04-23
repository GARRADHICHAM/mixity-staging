from act.models import Elearning
from act.serializers import ElearningSerializer
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from mixity.dashboard.views import DashboardStructureViewMixin


class ApiElearning(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = ElearningSerializer
    queryset = Elearning.objects.all()

    def test_func(self):
        return self.entity is None or self.request.user.test_func_rights(self.entity)


class ApiElearningDetails(
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    APIView,
):
    serializer_class = ElearningSerializer

    def get(self, request, *args, **kwargs):
        try:
            print(self.kwargs["elearning"])
            elearning = Elearning.objects.get(slug=self.kwargs["elearning"])
            serializer = self.serializer_class(elearning)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Elearning.DoesNotExist:
            return Response(
                "Aucun Elearning trouvé", status=status.HTTP_400_BAD_REQUEST
            )

    def test_func(self):
        return self.entity is None or self.request.user.test_func_rights(self.entity)
