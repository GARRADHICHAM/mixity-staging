from django.contrib.auth import views as auth_views
from django.urls import path

from accounts.views import (
    StructureCreateView,
    StructureDeleteView,
    StructureMemberDeleteView,
    ManageHumanCriteriaView,
    StructureMemberOwnerView,
    StructureMemberReaderView,
)

app_name = "structure"

urlpatterns = [
    path("add/", StructureCreateView.as_view(), name="add"),
    path(
        "<int:pk>/manage-criteria/",
        ManageHumanCriteriaView.as_view(),
        name="manage_criteria",
    ),
    path(
        "<int:pk>/delete/members/<int:user_pk>",
        StructureMemberDeleteView.as_view(),
        name="delete_member",
    ),
    path(
        "<int:pk>/set-owner/members/<int:membership_pk>",
        StructureMemberOwnerView.as_view(),
        name="set_owner_member",
    ),
    path(
        "<int:pk>/set-reader/members/<int:membership_pk>",
        StructureMemberReaderView.as_view(),
        name="set_reader_member",
    ),
    path("<int:pk>/delete/", StructureDeleteView.as_view(), name="delete"),
]
