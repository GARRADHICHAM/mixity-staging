import json
import csv
import re
from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    Q,
    Count,
    Prefetch,
    BooleanField,
    TextField,
    OuterRef,
    Subquery,
    Sum,
    Avg,
    Case,
    FloatField,
    When,
)
from django.forms import model_to_dict
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import viewsets, status
from django_rq import job
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.utils.text import slugify
from django.shortcuts import get_object_or_404

from django.utils.translation import get_language, activate

from rest_framework.decorators import action
from django.db.models import Q

from accounts.mails import (
    send_mail_evaluation_started,
    send_invitation_mail,
)

from scoring.mails import alert_reevaluation_request

from accounts.models import (
    Structure,
    Entity,
    MixityUser,
    HumanCriteriaChoice,
    HumanCriteria,
)
from scoring.views import StructureDataViewMixin
from mixity.settings import (
    HUMAN_FILTER_LIMIT,
    LANGUAGES,
    ENABLED_WEBSITE_LANGUAGES,
    LANGUAGES_GOOGLE_SHEETS,
)
from mixity.templatetags.format_number import compute_evolution_points
from scoring.models import (
    Category,
    Aim,
    CollaboratorsStatistics,
    Evaluation,
    ReevaluationRequest,
    SubCategory,
    ScoreCategory,
    Collaborator,
    QuestionTag,
    Question,
    Answer,
    Comment,
    prepare_human_filters_queries,
    SubAnswer,
    Choice,
    MAIN_CATEGORIES_SLUGS,
    ScanCollaborator,
    IAScanAnalysis,
    IAScanAnalysisElement,
    Skill,
)
from scoring.ia_scan import IAScan

from mixity.models import (
    SolutionFormat,
)
from lead.models import Objective, LeadAction, ActionKpi, GenericKpi
from act.models import (
    Solution,
    SolutionKeyword,
    Solver,
    BestPracticeKeyword,
    BestPracticeType,
    BestPracticePublic,
    BestPracticeOrganizationType,
    BestPracticeSize,
    BestPractice,
)
from subscriptions.models import (
    SubscriptionOption,
    SubscriptionPack,
)
from mixity.dashboard.views import DashboardStructureViewMixin, DashboardAssessViewMixin
from accounts.vocabularies import (
    COUNTRIES_CHOICES,
    AGE_CHOICES,
    REGIONS_CHOICES,
    TYPE_CHOICES,
    COLLABORATOR_STATISTICS_STATUSES,
    AGE_CHOICES,
    CIVILITY_CHOICES,
    SCAN_ROLE_CHOICE,
    CAMPUS_CHOICE,
    MONTHS,
)
from mixity.services.namsor.api import Namsor

from mixity.serializers import (
    StructureSerializer,
    EntitySerializer,
    EvaluationSerializer,
    CategorySerializer,
    CollaboratorsStatisticsSerializer,
    AssessScoreCategorySerializer,
    AllIndicatorSerializer,
    OneIndicatorSerializer,
    VersionsListSerializer,
    SubscriptionOptionSerializer,
    SubscriptionPackSerializer,
    ScanCollaboratorSerializer,
)
from lead.serializers import (
    ObjectiveSerializer,
    ActionSerializer,
    KpiSerializer,
    GenericKpiSerializer,
    MixityUserSerializer,
)
from act.serializers import (
    SolutionSerializer,
    SolutionKeywordSerializer,
    LanguageSerializer,
    SolversSerializer,
    SolverSerializer,
    SolutionFormatSerializer,
    BestPracticeSerializer,
    BestPracticeKeywordSerializer,
    BestPracticeTypeSerializer,
    BestPracticePublicSerializer,
    OrganizationTypeSerializer,
    BestPracticeSizeSerializer,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse

from scoring.templatetags.get_collaborators_statistics import (
    get_collaborators_statistics,
)

# Catalogue solver API views
from scoring.serializers import (
    IndicatorSerializer,
    AllIndicatorSerializer,
    CommentSerializer,
    GeneralAnalysisSerializer,
    EntityTreeSerializer,
)


def generate_collaborator_filters(
    collaborator_filter, collaborator_criteria_filter, evaluation=None
):
    """
    generate_collaborator_filters permet de filtrer les collaborateurs à partir des :
        - collaborator_filter (filtres par défauts des collaborateurs)
        - collaborator_criteria_filter (filtres human_criteria créés au lancement de l'évaluation par le client)
    """
    if evaluation:
        queryset = evaluation.collaborators.all()
    else:
        queryset = Collaborator.objects.filter()
    if collaborator_filter:
        for key, value in collaborator_filter.items():
            if value:
                queryset = queryset.filter(**{f"{key}__in": value})
    if collaborator_criteria_filter:
        criterias = evaluation.human_criteria.filter(
            choices__id__in=collaborator_criteria_filter
        ).annotate(
            choice_ids=ArrayAgg(
                "choices__id", filter=Q(choices__id__in=collaborator_criteria_filter)
            )
        )
        for criteria in criterias:
            queryset = queryset.filter(
                human_criteria_choices__id__in=criteria.choice_ids
            )
    return queryset


class EntityTree(LoginRequiredMixin, UserPassesTestMixin, APIView):
    serializer_class = EntityTreeSerializer
    entity = None

    def get_object(self):
        if not self.entity:
            self.entity = Entity.objects.get(pk=self.kwargs["pk"])
        return self.entity

    def get(self, *args, **kwargs):
        queryset = self.get_object().get_all_children_entities
        serializer = EntityTreeSerializer(queryset, many=True)
        return Response(serializer.data)

    def test_func(self):
        return self.request.user.test_func_rights(self.get_object())


class NamsorIndicatorContent(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    APIView,
):
    def display_version_from_slug(self, version):
        if version != "en-cours":
            year, month_slug = version.split("-")
            result = year + "-"

            actual_language = get_language()
            activate("fr")
            for month in MONTHS:
                if slugify(month) == month_slug:
                    return result + month
            activate(actual_language)
        else:
            return "en-cours"

    def get(self, request, **kwargs):
        """
        get permet de récupérer les infos de l'indicateur Namsor de l'évaluation en cours (grâce au display_version)
        """
        params = self.request.GET
        if params.get("version"):
            entity = Evaluation.objects.get(pk=kwargs["pk"]).entity
            display_version = self.display_version_from_slug(params["version"])
            collab = CollaboratorsStatistics.objects.select_related(
                "statistics"
            ).filter(
                evaluation__entity=entity,
                evaluation__display_version=display_version,
                status="finished",
            )
        else:
            collab = CollaboratorsStatistics.objects.select_related(
                "statistics"
            ).filter(
                evaluation=Evaluation.objects.get(pk=kwargs["pk"]), status="finished"
            )
        stats = get_collaborators_statistics(
            list(collab), '{"group_by":["region", "name"]}'
        )
        return Response(json.loads(stats))

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiStructure(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = StructureSerializer

    def get_queryset(self):
        return Structure.objects.filter(slug=self.entity.entity_level.structure.slug)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiEntity(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = EntitySerializer

    def get_queryset(self):
        return Entity.objects.filter(slug=self.entity.slug).prefetch_related("members")

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiEntities(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = EntitySerializer

    def get_queryset(self):
        return self.entity.get_own_entire_tree

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiMembership(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, APIView
):
    def get(self, request, slug=""):
        membership = self.request.user.get_rights(self.entity)
        return Response(
            {
                "user_id": self.request.user.id,
                "is_owner": membership.is_owner,
                "is_reader": membership.is_reader,
                "is_staff": self.request.user.is_staff,
            }
        )

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiUser(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = MixityUserSerializer

    def get_queryset(self):
        return MixityUser.objects.filter(pk=self.request.user.pk)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class RadarDataViewSet(viewsets.ModelViewSet):
    """
    RadarDataViewSet renvois l'objet permettant d'afficher l'empreinte avec la bonne liste de scores par catégories
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evaluations = {}
        self.radar_data = {}

    def list(self, request, *args, **kwargs):
        data = super().list(request, *args, **kwargs)
        for elem in data.data:
            if elem["scores_categories"]:
                if not elem["pk"] in self.radar_data:
                    self.radar_data[elem["pk"]] = self.evaluations[
                        elem["pk"]
                    ].get_radar_data()
                elem["radar_data"] = self.radar_data[elem["pk"]]
        return data


class APIRadarDataFilter(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    """
    APIRadarDataFilter récupère les données permettant d'afficher les scores par catégories tout
    en prenant en compte les filtres si c'est un human
    """

    def get(self, request, slug="", product=""):
        self.evaluations = {}
        self.radar_data = {}
        params = json.loads(self.request.GET["human_filter"])
        if self.assess_evaluation:
            self._evaluation = self.assess_evaluation
        elif (
            not self._evaluation.is_validated_by_admin
            and self.entity.last_validated_by_admin_global_evaluation
            != self._evaluation
        ):
            if self._evaluation is None:
                self._evaluation = (
                    self.entity.entity_level.structure.get_main_entity.last_human_evaluation
                )

        if self._evaluation.scores_categories:
            if "default" in params and "human_criteria" in params:
                self.radar_data = self._evaluation.get_radar_data(human_filter=params)
            else:
                self.radar_data = self._evaluation.get_radar_data()
        return Response(self.radar_data)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiLastDiagEvaluation(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    RadarDataViewSet,
):
    """
    API qui permet de recupérer la dernière évaluation DIAG ou GLOBAL (vieux référentiel de DIAG) à date
    """

    serializer_class = EvaluationSerializer

    def get_queryset(self):
        # Récupérer l'évaluation en cours globale (diag) de l'entité
        last_evaluation = self.entity.en_cours_global_evaluation
        if last_evaluation is None:
            # Récupérer la dernière évaluation globale (diag) validée par l'admin de l'entité
            last_evaluation = self.entity.last_validated_by_admin_global_evaluation
        if last_evaluation is None:
            # Récupérer la dernière évaluation globale (diag) de l'entité
            last_evaluation = self.entity.last_global_evaluation
        # Vérifier si last_evaluation est différent de None
        if last_evaluation is not None:
            # Retourner un queryset contenant la dernière évaluation
            self._evaluation = Evaluation.objects.get(pk=last_evaluation.pk)
            self.evaluations[self._evaluation.pk] = self._evaluation
            return [self._evaluation]
        else:
            return []

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiCategory(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(
            slug__in=MAIN_CATEGORIES_SLUGS + ["your-suggestions"]
        ).order_by("pk")

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiLastHumanEvaluation(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    RadarDataViewSet,
):
    """
    API qui permet de recupérer la dernière évaluation HUMAN à date
    """

    serializer_class = EvaluationSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evaluation = {}

    def get_queryset(self):
        # Récupérer l'évaluation human en cours de l'entité
        last_evaluation = self.entity.en_cours_human_evaluation
        if last_evaluation is None:
            # Récupérer la dernière évaluation human validée par l'admin de l'entité
            last_evaluation = self.entity.last_validated_by_admin_human_evaluation
        if last_evaluation is None:
            # Récupérer la dernière évaluation human de l'entité
            last_evaluation = self.entity.last_human_evaluation
        if last_evaluation is not None:
            # Retourner un queryset contenant la dernière évaluation
            self._evaluation = Evaluation.objects.get(pk=last_evaluation.pk)
            self.evaluations[self._evaluation.pk] = self._evaluation
            return [self._evaluation]
        else:
            # Retourner une liste vide si aucune évaluation n'est disponible
            return []

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiAction(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = ActionSerializer

    def get_queryset(self):
        return LeadAction.objects.filter(
            objective__entity__in=self.entity.get_own_entire_tree
        )

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiFirstFiveAction(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = ActionSerializer

    def get_queryset(self):
        return LeadAction.objects.filter(
            objective__entity__in=self.entity.get_own_entire_tree
        )[:5]

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiSolution(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = SolutionSerializer
    queryset = Solution.objects.all()

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiFirstFiveSolution(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = SolutionSerializer
    queryset = Solution.objects.all()[:5]

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiUrl(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, APIView
):
    """
    API qui permet de recupérer l'URL de base comme localhost:8080 ou mixixty.co
    """

    def get(self, request, slug="", product="", version=""):
        return Response(request.get_host())

    def test_func(self):
        is_collaborator = False
        if "survey" in self.request.path:
            if self.kwargs["product"] == "scan":
                evaluation = Evaluation.objects.get(
                    entity__slug=self.kwargs["slug"],
                    sheet__type__slug="mixity_evaluation_scan",
                    display_version="en-cours",
                )
                is_collaborator = (
                    self.request.user.scan_collaborator
                    in evaluation.scan_collaborators.all()
                )
            elif self.kwargs["product"] == "human":
                evaluation = Evaluation.objects.get(
                    entity__slug=self.kwargs["slug"],
                    sheet__type__slug="evaluation_collaborateurs_360",
                    display_version="en-cours",
                )
                is_collaborator = (
                    self.request.user.scan_collaborator
                    in evaluation.scan_collaborators.all()
                )
        return (
            self.entity is None
            or self.request.user.test_func_rights(self.entity)
            or is_collaborator
        )


class ApiObjective(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = ObjectiveSerializer

    def get_queryset(self):
        return Objective.objects.filter(
            entity__in=self.entity.get_own_entire_tree
        ).order_by("category", "subcategory", "pk")

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


def prepare_aims_to_add_to_objectives(aims, entity):
    """
    This function returns a list of objectives to add
    and aims to update from an initial list of aims
    """
    objectives = list()
    aims_to_update = list()
    for aim in aims:
        if not aim.objective:
            label = aim.description.split("\n")[0]
            if len(label) > 152:
                label = label[:152]
            objective = Objective(
                label=label,
                category=aim.category,
                subcategory=aim.subcategory,
                structure=entity.entity_level.structure,
                entity=entity,
            )
            aims_to_update.append(aim)
            objectives.append(objective)

    return aims_to_update, objectives


def bulk_create_and_update(aims, objectives):
    """
    This function bulk_create objectives
    and then bulk_update the field objective of each aim
    """
    # Creating objectives in one request
    Objective.objects.bulk_create(objectives)
    # Updating aims objectives in one request
    for index, aim in enumerate(aims):
        aim.objective = objectives[index]
    Aim.objects.bulk_update(aims, ["objective"])


class ApiCreateObjectiveFromEvaluation(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = ObjectiveSerializer

    def get_queryset(self):
        aims = []
        if self.entity.last_human_evaluation:
            aims.extend(self.entity.last_human_evaluation.aims.all())
        if self.entity.last_global_evaluation:
            aims.extend(self.entity.last_global_evaluation.aims.all())
        aims_to_update, objectives = prepare_aims_to_add_to_objectives(
            aims, self.entity
        )
        bulk_create_and_update(aims_to_update, objectives)
        return Objective.objects.filter(
            structure=self.entity.entity_level.structure
        ).order_by("category", "subcategory", "pk")

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiKpi(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = KpiSerializer

    def get_queryset(self):
        return ActionKpi.objects.filter(
            action__objective__entity__in=self.entity.get_own_entire_tree
        )

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiGenericKpi(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = GenericKpiSerializer
    queryset = GenericKpi.objects.prefetch_related("subcategories").all()

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiSolutionKeyword(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = SolutionKeywordSerializer
    queryset = SolutionKeyword.objects.all()

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiLanguage(
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = LanguageSerializer
    lang_json = []
    i = 1
    for lang in LANGUAGES:
        lang_json.append(
            {
                "pk": i,
                "label": lang[1],
                "code": lang[0],
                "is_enabled": lang[0] in ENABLED_WEBSITE_LANGUAGES,
                "is_google_sheet_lang": lang[0]
                in str(LANGUAGES_GOOGLE_SHEETS).replace("_", "-").lower(),
            }
        )
        i += 1
    queryset = lang_json


class ApiSolverSolution(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = SolutionSerializer

    def get_queryset(self):
        return Solution.objects.filter(
            solver__structure=self.entity.entity_level.structure
        )

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiSolutionFormats(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = SolutionFormatSerializer
    queryset = SolutionFormat.objects.all()

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiSolver(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = SolverSerializer

    def get_queryset(self):
        return Solver.objects.filter(structure=self.entity.entity_level.structure)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiSolvers(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = SolversSerializer
    queryset = Solver.objects.all()

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiRegion(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, APIView
):
    def get(self, request, slug=""):
        data = {"countries": COUNTRIES_CHOICES, "regions": REGIONS_CHOICES[:-1]}
        return Response(data)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiMixityMembers(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, APIView
):
    def get(self, request, slug=""):
        data = list(
            MixityUser.objects.filter(email__icontains="@mixity.io").values_list(
                "pk", flat=True
            )
        )
        return Response(data)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiCollaboratorsStatistics(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = CollaboratorsStatisticsSerializer

    def display_version_from_slug(self, version):
        if version != "en-cours":
            year, month_slug = version.split("-")
            result = year + "-"

            actual_language = get_language()
            activate("fr")
            for month in MONTHS:
                if slugify(month) == month_slug:
                    return result + month
            activate(actual_language)
        else:
            return "en-cours"

    def get_queryset(self):
        """
        Permet de retourner l'indicateur Namsor
        """
        choices = {key: value for key, value in TYPE_CHOICES}
        params = self.request.GET
        if params.get("version"):
            display_version = self.display_version_from_slug(params["version"])
            queryset = list(
                CollaboratorsStatistics.objects.filter(
                    evaluation__entity=self.entity,
                    evaluation__display_version=display_version,
                ).only("status", "type", "can_delete")
            )
        else:
            queryset = list(
                CollaboratorsStatistics.objects.filter(
                    evaluation=self.entity.last_global_evaluation
                ).only("status", "type", "can_delete")
            )
        for elem in queryset:
            del choices[elem.type]
        for key, choice in choices.items():
            queryset.append(
                CollaboratorsStatistics(type=key, status="nodata", can_delete=True)
            )
        return queryset

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


@job("default")
def compute_namsor_data(csv: str, evaluation_id: int, header: bool, csv_type: str):
    csv = csv.replace(";", ",")
    Namsor.get_instance().compute_ethnicity_from_csv(
        csv, Evaluation.objects.get(id=evaluation_id), ",", header, csv_type
    )


class ApiUploadCSV(ApiCollaboratorsStatistics):
    """
    Endpoint to upload a CSV for the Namsor API
    """

    def create(self, request, *args, **kwargs):
        data = request.data
        response = self.get(request, *args, **kwargs)
        params = self.request.GET
        type_exists = False
        for i in range(len(response.data)):
            if response.data[i]["type"] == data["type"]:
                type_exists = True
                if not response.data[i]["can_delete"]:
                    return JsonResponse(
                        data={"error": "You can't delete these statistics"}, status=400
                    )
                response.data[i]["status"] = "processing"
                response.data[i]["can_delete"] = False
                response.data[i]["status_label"] = COLLABORATOR_STATISTICS_STATUSES[
                    "processing"
                ]
                break
        if not type_exists:
            return JsonResponse(
                data={"error": "You can't upload an unknown type"}, status=400
            )
        compute_namsor_data.delay(
            data["file"].read().decode("utf-8"),
            params.get("eval_id", self.entity.last_global_evaluation),
            data["ignoreFirstLine"] == "true",
            data["type"],
        )
        return response


# Best Practices API views
class ApiBestPractice(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    """This view returns all the best practices, and it's used in favorites page cause this page doesn't take into consideration the status (public/private) of the best practices"""

    serializer_class = BestPracticeSerializer

    def get_queryset(self):
        return BestPractice.objects.all()

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


# Best Practices API views
class ApiPracticer(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    """This view returns all the best practices, and it's used in favorites page cause this page doesn't take into consideration the status (public/private) of the best practices"""

    serializer_class = StructureSerializer
    queryset = Structure.objects.exclude(best_practices=None)

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiBestPracticeManagement(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    """This view returns only the best practices of the connected structure for CRUD operations"""

    serializer_class = BestPracticeSerializer

    def get_queryset(self):
        return BestPractice.objects.filter(structure=self.entity.entity_level.structure)

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiBestPracticeSearch(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    """This view returns all the public best practices and the private ones of the connected structure"""

    serializer_class = BestPracticeSerializer

    def get_queryset(self):
        return (
            BestPractice.objects.filter(
                structure=self.entity.entity_level.structure, is_public=False
            )
            | BestPractice.objects.filter(is_public=True)
        ).distinct()

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiBestPracticeKeyword(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = BestPracticeKeywordSerializer
    queryset = BestPracticeKeyword.objects.all()

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiBestPracticeType(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = BestPracticeTypeSerializer
    queryset = BestPracticeType.objects.all()

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiBestPracticePublic(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = BestPracticePublicSerializer
    queryset = BestPracticePublic.objects.all()

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiOrganizationType(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = OrganizationTypeSerializer
    queryset = BestPracticeOrganizationType.objects.all()

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiBestPracticeSize(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = BestPracticeSizeSerializer
    queryset = BestPracticeSize.objects.all()

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiOpenResponses(
    UserPassesTestMixin,
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    def get(self, request, *args, **kwargs):
        self.assess_evaluation.is_validated_by_user = False
        self.assess_evaluation.save()
        return Response("GET request processed", status=status.HTTP_200_OK)

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiBlockResponses(
    UserPassesTestMixin,
    LoginRequiredMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    def get(self, request, *args, **kwargs):
        self.assess_evaluation.do_user_validation()
        return Response("GET request processed", status=status.HTTP_200_OK)

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


def generate_collaborator_criteria(assess_evaluation, file_content):
    """
    Génère les HumanCriterias présents dans le csv d'import de collaborateurs en début d'évaluation Human ou Scan
    """
    csv_reader = csv.DictReader(file_content.splitlines())
    columns = csv_reader.fieldnames
    mandatory_columns = ["email", "nom", "prenom", "age"]

    for column in columns:
        if column not in mandatory_columns:
            HumanCriteria.objects.get_or_create(
                evaluation=assess_evaluation, label=column, is_csv_imported=True
            )


def generate_user(row, assess_evaluation, request):
    """
    Génère les utilisateurs invités sur la plateforme après avoir vérifier si ils existent déjà en bdd ou non
    """
    try:
        user = MixityUser.objects.get(email=row["email"].lower())
    except MixityUser.DoesNotExist:
        user = MixityUser.objects.create_user(
            first_name=row["prenom"],
            last_name=row["nom"],
            email=row["email"].lower(),
            username=row["email"].lower(),
        )
        from django.contrib.auth.tokens import PasswordResetTokenGenerator

        token = PasswordResetTokenGenerator().make_token(user=user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        send_invitation_mail(
            user,
            request,
            assess_evaluation.entity.entity_level.structure,
            request.user,
            uid,
            token,
        )
    return user


def generate_collaborator(user, assess_evaluation):
    if assess_evaluation.is_scan:
        return ScanCollaborator.objects.get_or_create(
            user=user, evaluation=assess_evaluation
        )[0]
    else:
        return Collaborator.objects.get_or_create(
            user=user, evaluation=assess_evaluation
        )[0]


def fill_collaborator_criteria_choices(assess_evaluation, collaborator, row):
    """
    Permet de mettre automatiquement des choix aux critères human des collaborateurs lorsqu'ils sont importés via csv
    """
    for key, value in row.items():
        if key not in ["email", "nom", "prenom", "age"]:
            human_criteria = HumanCriteria.objects.get(
                label=key, evaluation=assess_evaluation
            )
            try:
                choice = HumanCriteriaChoice.objects.get(
                    label=value,
                    criteria=human_criteria,
                )
            except HumanCriteriaChoice.DoesNotExist:
                choice = HumanCriteriaChoice.objects.create(
                    criteria=human_criteria,
                    label=value,
                )
            if assess_evaluation.is_scan:
                collaborator.scan_criteria_choices.add(choice)
            else:
                collaborator.human_criteria_choices.add(choice)
            collaborator.save()


def generate_collaborator_criteria_choices(assess_evaluation, file_content, request):
    """
    Génère les HumanCriteria en fonction des colonnes présentes dans le csv d'import des collaborateurs
    """
    csv_reader = csv.DictReader(file_content.splitlines())
    rows = list(csv_reader)

    for row in rows:
        user = generate_user(row, assess_evaluation, request)
        collaborator = generate_collaborator(user, assess_evaluation)
        fill_collaborator_criteria_choices(assess_evaluation, collaborator, row)


# @job("default")
def generate_all_collaborators_data(assess_evaluation, file_content, request):
    generate_collaborator_criteria(assess_evaluation, file_content)
    generate_collaborator_criteria_choices(assess_evaluation, file_content, request)


class ApiDeleteFilterChoice(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    def post(self, request, *args, **kwargs):
        data = request.data
        self.assess_evaluation = Evaluation.objects.get(pk=self.kwargs["evaluation_pk"])
        if "human_criteria" in data and "choice" in data:
            HumanCriteriaChoice.objects.filter(
                label=data["choice"],
                criteria=HumanCriteria.objects.get(
                    label=data["human_criteria"], evaluation=self.assess_evaluation
                ),
            )[0].delete()
            return Response(
                _("Le filtre a été supprimé avec succès"), status=status.HTTP_200_OK
            )
        return Response(
            _("Le filtre n'a pas pu être supprimé"), status=status.HTTP_400_BAD_REQUEST
        )

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiModifyFilterChoice(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    def post(self, request, *args, **kwargs):
        data = request.data
        self.assess_evaluation = Evaluation.objects.get(pk=self.kwargs["evaluation_pk"])
        if "human_criteria" in data:
            human_criteria = HumanCriteria.objects.get(
                label=data["human_criteria"], evaluation=self.assess_evaluation
            )
            if "choice" in data and "new_choice" in data:
                HumanCriteriaChoice.objects.update_or_create(
                    label=data["choice"],
                    criteria=human_criteria,
                    defaults={"label": data["new_choice"], "criteria": human_criteria},
                )
                return Response(
                    _("Le filtre a été modifié avec succès"), status=status.HTTP_200_OK
                )
        return Response(
            _("Le filtre n'a pas pu être modifié"), status=status.HTTP_400_BAD_REQUEST
        )

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiDeleteFilter(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    def post(self, request, *args, **kwargs):
        data = request.data
        self.assess_evaluation = Evaluation.objects.get(pk=self.kwargs["evaluation_pk"])
        if "human_criteria" in data:
            HumanCriteria.objects.get(
                label=data["human_criteria"], evaluation=self.assess_evaluation
            ).delete()
            return Response(
                _("Le filtre a été supprimé avec succès"), status=status.HTTP_200_OK
            )
        return Response(
            _("Le filtre n'a pas pu être supprimé"), status=status.HTTP_400_BAD_REQUEST
        )

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiAddFilter(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    def post(self, request, *args, **kwargs):
        data = request.data
        self.assess_evaluation = Evaluation.objects.get(pk=self.kwargs["evaluation_pk"])
        if "human_criteria" in data:
            HumanCriteria.objects.get_or_create(
                label=data["human_criteria"], evaluation=self.assess_evaluation
            )
            return Response(
                _("Le filtre a été ajouté avec succès"), status=status.HTTP_200_OK
            )
        return Response(
            _("Le filtre n'a pas pu être ajouté"), status=status.HTTP_400_BAD_REQUEST
        )

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiHandleCollaboratorsList(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    """
    Cette API permet de gérer l'import du csv contenant les collaborateurs
    """

    def check_mandatory_columns(self, file_content):
        mandatory_columns = ["email", "nom", "prenom"]

        csv_reader = csv.DictReader(file_content.splitlines())
        columns = csv_reader.fieldnames
        for column in mandatory_columns:
            if column not in columns:
                return False
        return True

    def check_emails_format(self, file_content):
        csv_reader = csv.DictReader(file_content.splitlines())
        # regex used to check the email format
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"

        for row in csv_reader:
            if not re.match(regex, row["email"]):
                return False
        return True

    def post(self, request, *args, **kwargs):
        file_content = request.data["file_content"]
        file_content = file_content.replace(";", ",")
        if file_content == "":
            return Response(
                _("Le fichier est vide"), status=status.HTTP_400_BAD_REQUEST
            )
        if not self.check_mandatory_columns(file_content):
            return Response(
                _(
                    "Le fichier doit contenir les colonnes suivantes : email, nom, prenom, age"
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not self.check_emails_format(file_content):
            return Response(
                _("Le fichier doit contenir des adresses email valides"),
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.assess_evaluation = Evaluation.objects.get(pk=self.kwargs["evaluation_pk"])
        generate_all_collaborators_data(self.assess_evaluation, file_content, request)
        return Response(
            _("Les données ont été importées avec succès"),
            status=status.HTTP_200_OK,
        )

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


@job("default")
def send_collaborator_mail(evaluation, host):
    users = MixityUser.objects.filter(collaborator__evaluation=evaluation)
    for user in users:
        send_mail_evaluation_started(
            user,
            evaluation,
            host=host,
        )


def send_scan_collaborator_mail(evaluation, host):
    users = MixityUser.objects.filter(scan_collaborator__evaluation=evaluation)
    for user in users:
        send_mail_evaluation_started(
            user,
            evaluation,
            host=host,
        )


class ApiStartEvaluation(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    """
    Cette API envoie un mail aux personnes présentes dans l'évaluation et ouvre le questionnaire
    """

    def post(self, request, *args, **kwargs):
        self.assess_evaluation = Evaluation.objects.get(pk=self.kwargs["evaluation_pk"])
        if self.assess_evaluation.is_started:
            return Response(
                "L'évaluation a déjà été démarrée", status=status.HTTP_400_BAD_REQUEST
            )
        if self.assess_evaluation.is_human:
            send_collaborator_mail.delay(self.assess_evaluation, request.get_host())
        else:
            send_scan_collaborator_mail(self.assess_evaluation, request.get_host())
        self.assess_evaluation.is_started = True
        self.assess_evaluation.save()
        return Response(
            "POST request processed, Evaluation started.", status=status.HTTP_200_OK
        )

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


class ApiAssessEvaluation(viewsets.ModelViewSet):
    """
    Cette API récupère l'évaluation l'évaluation voulue pour la fiche entreprise (AssessPage)
    """

    def retrieve_evaluation(self, request, slug, product, version):
        if product == "human":
            evaluations = Evaluation.objects.filter(
                entity__slug=slug, sheet__type__slug="evaluation_collaborateurs_360"
            )
        elif product == "scan":
            evaluations = Evaluation.objects.filter(
                entity__slug=slug, sheet__type__slug="mixity_evaluation_scan"
            )
        else:
            evaluations = (
                Evaluation.objects.filter(entity__slug=slug)
                .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                .exclude(sheet__type__slug="mixity_evaluation_scan")
            )
        for evaluation in evaluations:
            if slugify(evaluation.display_version) == version:
                serializer = EvaluationSerializer(evaluation)
                return Response(serializer.data)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)

    @staticmethod
    def test_evol_func(value):
        return str(value)


class ApiSubscriptionOption(APIView):
    """
    Cette API récupère le type d'abonnement qu'a le client
    """

    serializer_class = SubscriptionOptionSerializer
    lookup_field = "evaluation_pk"

    def get(self, request, *args, **kwargs):
        eval_id = self.kwargs.get("evaluation_pk")
        try:
            evaluation = Evaluation.objects.get(id=eval_id)
        except Evaluation.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        subscription_option = evaluation.get_option
        if not subscription_option:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(subscription_option)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApiSubscriptionPack(APIView):
    """
    Cette API permet de récupèrer le pack d'abonnement de la structure voulue
    """

    serializer_class = SubscriptionPackSerializer

    def get(self, request, *args, **kwargs):
        structure_id = self.kwargs.get("structure_id")
        try:
            subscription_pack = (
                SubscriptionPack.objects.filter(structure_id=structure_id)
                .order_by("-start_date")
                .first()
            )
        except SubscriptionPack.DoesNotExist():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(subscription_pack)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApiEvaluationsVersionsList(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    viewsets.ModelViewSet,
):
    """
    Cette API récupère la listes de toutes les évaluations faites par une entité pour un produit donné
    """

    serializer_class = VersionsListSerializer

    def get_queryset(self, *args, **kwargs):
        entity_slug = self.kwargs.get("slug")
        product_slug = self.kwargs.get("product")

        if product_slug == "human":
            evaluations = Evaluation.objects.filter(
                entity__slug=entity_slug,
                sheet__type__slug="evaluation_collaborateurs_360",
            ).order_by("-version")
        elif product_slug == "scan":
            evaluations = Evaluation.objects.filter(
                entity__slug=entity_slug,
                sheet__type__slug="mixity_evaluation_scan",
            ).order_by("-version")
        else:
            evaluations = (
                Evaluation.objects.filter(entity__slug=entity_slug)
                .exclude(sheet__type__slug="evaluation_collaborateurs_360")
                .exclude(sheet__type__slug="mixity_evaluation_scan")
                .order_by("-version")
            )

        return evaluations

    def test_func(self):
        return self.request.user.is_authenticated


class ApiComments(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    viewsets.ModelViewSet,
    StructureDataViewMixin,
):
    """
    Cette API récupère tous les commentaires laissés sur l'évaluation par l'équipe produit
    (Recommandation dans la fiche entreprise)
    """

    serializer_class = CommentSerializer

    def get_queryset(self):
        if self.assess_evaluation is None:
            self.assess_evaluation = (
                self.entity.entity_level.structure.get_main_entity.last_global_evaluation
            )
        else:
            self.assess_evaluation = self.assess_evaluation

        comments = (
            Comment.objects.filter(answers__evaluation=self.assess_evaluation)
            .select_related("question")
            .prefetch_related("question__subcategory", "question__category")
            .only(
                "is_good",
                "description",
                "question__subcategory__slug",
                "question__category",
            )
            .all()
        )
        for comment in comments:
            comment.description = comment.answers.get(
                evaluation=self.assess_evaluation
            ).get_description_display
        return comments

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiGeneralAnalysis(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    viewsets.ModelViewSet,
    StructureDataViewMixin,
):
    """
    Cette API récupère la synthèse de l'évaluation
    """

    serializer_class = GeneralAnalysisSerializer

    def get_queryset(self):
        if self.assess_evaluation is None:
            self.assess_evaluation = (
                self.entity.entity_level.structure.get_main_entity.last_global_evaluation
            )
        else:
            self.assess_evaluation = self.assess_evaluation

        general_analysis = [
            self.assess_evaluation.get_general_analysis,
        ]
        return general_analysis

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiAssessScoreCategories(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    viewsets.ModelViewSet,
):
    """
    This view is used once at the first time mounting of the page to render the tabs dynamically
    """

    serializer_class = AssessScoreCategorySerializer

    def get_queryset(self):
        params = self.request.GET
        if params["eval_pk"]:
            evaluation = Evaluation.objects.prefetch_related("scores_categories").get(
                pk=params["eval_pk"]
            )
        else:
            evaluation = self.assess_evaluation

        if not evaluation.sheet.type.workforce_limit and evaluation.sheet.year < 2020:
            excluded_slug = "all"
        else:
            excluded_slug = "your-suggestions"

        scores_categories = (
            evaluation.scores_categories.exclude(category__slug=excluded_slug)
            .select_related("category")
            .prefetch_related("category__subcategories")
        )

        if evaluation.is_category_evaluation:
            scores_categories = (
                evaluation.scores_categories.filter(
                    category__slug__in=MAIN_CATEGORIES_SLUGS
                )
                .exclude(category__slug="all")
                .exclude(category__slug="csrd")
                .first()
            )

        for sc in scores_categories:
            current_evol = compute_evolution_points(
                current_year=sc.value,
                last_year=None if sc.sibling is None else sc.sibling.value,
                delta=(
                    sc.evolution_delta - 0
                    if sc.sibling is None
                    else sc.sibling.evolution_delta
                ),
                show_evolution=True,
            )
            sc.evolution = current_evol
            sc.inner_percent = sc.display_value()
            sc.between_percent = sc._mean_score_in_business_line()
            sc.outter_percent = sc._mean_score()
        return scores_categories

    @action(detail=False, methods=["POST"])
    def filtered_results_action(self, request, *args, **kwargs):
        if self.assess_evaluation is None:
            self.assess_evaluation = (
                self.entity.entity_level.structure.get_main_entity.last_human_evaluation
            )
        else:
            self.assess_evaluation = self.assess_evaluation
        evaluation = self.assess_evaluation
        filters_data = request.data
        if not evaluation.sheet.type.workforce_limit and evaluation.sheet.year < 2020:
            excluded_slug = "all"
        else:
            excluded_slug = "your-suggestions"
        scores_categories = evaluation.scores_categories.filter(
            category__slug__in=MAIN_CATEGORIES_SLUGS + ["your-suggestions"]
        ).exclude(category__slug=excluded_slug)

        if evaluation.is_category_evaluation:
            scores_categories = (
                evaluation.scores_categories.filter(
                    category__slug__in=MAIN_CATEGORIES_SLUGS
                )
                .exclude(category__slug="all")
                .first()
            )

        def prevent_save(*args, **kwargs):
            pass

        if "default" in filters_data and "human_criteria" in filters_data:
            for sc in scores_categories:
                if evaluation.is_campus and evaluation.is_human:
                    sc.value = sc.compute_score(
                        human_filter={
                            "age": filters_data["default"]["age"],
                            "civility": filters_data["default"]["civility"],
                            "status": filters_data["default"]["status"],
                            "human_criteria": HumanCriteriaChoice.objects.filter(
                                pk__in=filters_data["human_criteria"]
                            ).all(),
                        },
                        in_realtime=True,
                    )
                else:
                    sc.value = sc.compute_score(
                        human_filter={
                            "age": filters_data["default"]["age"],
                            "civility": filters_data["default"]["civility"],
                            "human_criteria": HumanCriteriaChoice.objects.filter(
                                pk__in=filters_data["human_criteria"]
                            ).all(),
                        },
                        in_realtime=True,
                    )
                sc.save = prevent_save
                current_evol = compute_evolution_points(
                    current_year=sc.value,
                    last_year=None if sc.sibling is None else sc.sibling.value,
                    delta=(
                        sc.evolution_delta - 0
                        if sc.sibling is None
                        else sc.sibling.evolution_delta
                    ),
                    show_evolution=True,
                )
                sc.evolution = current_evol
                sc.inner_percent = sc.display_value()

                if evaluation.is_campus and evaluation.is_human:
                    human_filter = (
                        {
                            "age": filters_data["default"]["age"],
                            "civility": filters_data["default"]["civility"],
                            "status": filters_data["default"]["status"],
                            "human_criteria": HumanCriteriaChoice.objects.filter(
                                pk__in=filters_data["human_criteria"]
                            ).all(),
                        },
                    )
                else:
                    human_filter = (
                        {
                            "age": filters_data["default"]["age"],
                            "civility": filters_data["default"]["civility"],
                            "human_criteria": HumanCriteriaChoice.objects.filter(
                                pk__in=filters_data["human_criteria"]
                            ).all(),
                        },
                    )

                sc.between_percent = sc._mean_score_in_business_line(
                    human_filter=human_filter,
                    in_realtime=True,
                )
                sc.outter_percent = sc._mean_score(
                    human_filter=human_filter,
                    in_realtime=True,
                )

        return Response(
            {
                "filtered_scores_categories": AssessScoreCategorySerializer(
                    scores_categories, many=True
                ).data
            }
        )

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiSubCategoryScores(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    """
    Subcategories Block Data
    """

    def get(self, request, slug="", product="", score_cat_pk=""):
        score_cat = ScoreCategory.objects.filter(pk=score_cat_pk).first()

        if product == "human":
            data = {
                "subcategories_scores": score_cat.get_scorecategory_detail(),
            }
        else:
            subcats = score_cat.get_subcategories_values
            subcategories = []
            for subcat in subcats:
                subcategories.append(
                    [
                        subcat["SubCategory"],
                        subcat["Value"],
                        subcat["SubCategorySlug"],
                    ]
                )
            data = {"subcategories_scores": subcategories}
        return Response(data)

    def post(self, request, *args, **kwargs):
        """
        This method is used for the Human Filters
        """
        result = {}
        params = request.data

        if (
            "score_cat_pk" in params
            and "default" in params
            and "human_criteria" in params
        ):
            score_cat = ScoreCategory.objects.filter(
                pk=int(params["score_cat_pk"])
            ).first()
            evaluation = self.assess_evaluation
            if evaluation.is_campus and evaluation.is_human:
                result = {
                    "subcategories_scores": score_cat.get_scorecategory_detail(
                        human_filters={
                            "age": params["default"]["age"],
                            "civility": params["default"]["civility"],
                            "status": params["default"]["status"],
                            "human_criteria": HumanCriteriaChoice.objects.filter(
                                pk__in=params["human_criteria"]
                            ).all(),
                        },
                        in_realtime=True,
                    ),
                }
            else:
                result = {
                    "subcategories_scores": score_cat.get_scorecategory_detail(
                        human_filters={
                            "age": params["default"]["age"],
                            "civility": params["default"]["civility"],
                            "human_criteria": HumanCriteriaChoice.objects.filter(
                                pk__in=params["human_criteria"]
                            ).all(),
                        },
                        in_realtime=True,
                    ),
                }

        return Response(result)

    # old {'collab_filters': {'age': [{'slug': 'under_25', 'label': 'Moins de 25 ans'}]}, 'collab_human_criteria': {}, 'score_cat_pk': 1503}
    # new {'default': {'age': ['under_25'], 'civility': []}, 'human_criteria': [], 'score_cat_pk': 1503}
    # newcomplex : {'default': {'age': ['under_25', '25_39'], 'civility': []}, 'human_criteria': ['195', '201'], 'score_cat_pk': 1503}
    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiHumanFormChoices(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    def get(self, request, slug="", product=""):
        result = {}
        # this is need to be able to use the same script for downloading excel ( static/js/excel_human_filter.js ) on the django page and react
        excel_filters = {}

        # Civility, age and status are default fields
        excel_filters["civility"] = {
            "label": "Genre",
            "choices": [{choice[0]: choice[1]} for choice in CIVILITY_CHOICES],
            "is_human_criteria": False,
        }
        excel_filters["age"] = {
            "label": "Âge",
            "choices": [{choice[0]: choice[1]} for choice in AGE_CHOICES],
            "is_human_criteria": False,
        }

        form_data = {
            "default": {
                "age": {
                    "title": "Âge",
                    "choices": {item[0]: item[1] for item in AGE_CHOICES},
                },
                "civility": {
                    "title": "Genre",
                    "choices": {item[0]: item[1] for item in CIVILITY_CHOICES},
                },
            },
            "human_criteria": {},
        }

        # Campus case choices
        evaluation = self.assess_evaluation
        if evaluation.is_campus and evaluation.is_human:
            form_data["default"]["status"] = {
                "title": "Statut",
                "choices": {item[0]: item[1] for item in CAMPUS_CHOICE},
            }
            excel_filters["status"] = {
                "label": "Statut",
                "choices": [{choice[0]: choice[1]} for choice in CAMPUS_CHOICE],
                "is_human_criteria": False,
            }

        # Preparing Human Criteria choices
        for hc in self.assess_evaluation.human_criteria.all():
            """
            The structure of human criteria data in the form for each criteria is :
            {criteria_id : {"title":criteria_label,"choices":criteria_choices} where each choice has this structure : {choice_id:choice_label}
            """
            form_data["human_criteria"][hc.id] = {"title": hc.label, "choices": {}}
            excel_filters[hc.label] = {
                "label": hc.label,
                "choices": [],
                "is_human_criteria": True,
                "is_csv_imported": hc.is_csv_imported,
            }
            for choice in hc.choices.all():
                form_data["human_criteria"][hc.id]["choices"][choice.id] = choice.label
                excel_filters[hc.label]["choices"].append({choice.label: choice.id})

        result["new"] = form_data
        result["old"] = excel_filters
        return Response(result)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiReevaluationRequest(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    """
    Cette API gère la possibilité de réouverture d'une évaluation des clients
    """

    def post(self, request, *args, **kwargs):
        self.assess_evaluation = get_object_or_404(
            Evaluation, pk=self.kwargs["evaluation_pk"]
        )

        if ReevaluationRequest.objects.filter(
            evaluation=self.assess_evaluation, is_accepted=False
        ).exists():
            return JsonResponse(
                {
                    "message": _(
                        "Une demande de réouverture pour cette évaluation est déjà en cours et n'a pas encore été acceptée."
                    ),
                    "success": False,
                },
                status=status.HTTP_409_CONFLICT,
            )

        if self.test_func():
            reevaluation_request = ReevaluationRequest.objects.create(
                evaluation=self.assess_evaluation,
                request_date=now(),
            )
            alert_reevaluation_request(self.assess_evaluation)
            return JsonResponse(
                {
                    "message": _(
                        "La demande de réouverture de l'évaluation a été transmise avec succès"
                    ),
                    "success": True,
                },
                status=status.HTTP_201_CREATED,
            )

        return JsonResponse(
            {
                "message": _("Vous n'avez pas les autorisations nécessaires."),
                "success": False,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiHumanCollaboratorsCount(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    """
    Cette API récupère des informations générales sur les collaborateurs d'un human ou d'un scan
    """

    def get(self, request, slug="", product=""):
        evaluation = self.assess_evaluation
        if evaluation.is_scan:
            collaborator_form_data = {
                "nb_collaborator_with_filter_min": 5,
                "nb_collaborator_answers": evaluation.scan_collaborators.exclude(
                    answers=None
                ).count(),
                "nb_collaborator": evaluation.scan_collaborators.count(),
                "get_workforce_from_evaluation": evaluation.get_workforce_from_evaluation,
            }
        else:
            collaborator_form_data = {
                "nb_collaborator_with_filter_min": HUMAN_FILTER_LIMIT,
                "nb_collaborator_answers": evaluation.answers.count(),
                "nb_collaborator": None,
                "get_workforce_from_evaluation": evaluation.get_workforce_from_evaluation,
            }
        return Response(collaborator_form_data)

    def post(self, request, *args, **kwargs):
        params = request.data
        collaborator_form_data = {}
        if "default" in params and "human_criteria" in params:
            evaluation = self.assess_evaluation
            human_filters = {
                "age": params["default"]["age"],
                "civility": params["default"]["civility"],
                "human_criteria": HumanCriteriaChoice.objects.filter(
                    pk__in=params["human_criteria"]
                ).all(),
            }
            if evaluation.is_human and evaluation.is_campus:
                human_filters["status"] = params["default"]["status"]
            collaborators = generate_collaborator_filters(
                params["default"], params["human_criteria"], evaluation=evaluation
            )
            collaborator_form_data = {
                "nb_collaborator_with_filters": evaluation.get_filtered_collaborators_count(
                    collaborators
                ),
                "nb_collaborator_answers_with_filters": evaluation.get_filtered_answers_count(
                    human_filters=human_filters
                ),
                "get_workforce_from_evaluation_with_filters": evaluation.get_workforce_from_evaluation,
            }
        return Response(collaborator_form_data)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiHumanCollaboratorsInfos(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    """
    Cette API génère des graphiques de répartition des répondants par âges et par genre pour HUMAN
    """

    def computed_criteria(self, human_criteria, nb_collaborator_with_filter=0):
        res = []
        for choice in human_criteria.choices.all():
            if nb_collaborator_with_filter != 0:
                value = (choice.total / nb_collaborator_with_filter) * 100
            else:
                value = 0
            res.append({"label": choice.label, "value": value})

        # Repartition des criteria_choices en plusieurs colonne si il y en a plus de 10
        return res

    def computed_human_collaborator(
        self, evaluation, value, collaborators_queryset, nb_collaborator_with_filter=0
    ):
        res = []
        try:
            all_data = (
                collaborators_queryset.filter(evaluation=evaluation)
                .values(value)
                .annotate(frequency=Count(value))
            )
            choices = getattr(Collaborator, value).field.choices
            for choice in choices:
                freq = 0
                for data in all_data:
                    if data[value] == choice[0]:
                        freq = data["frequency"]
                if nb_collaborator_with_filter != 0:
                    freq = freq / nb_collaborator_with_filter * 100
                else:
                    freq = 0
                res.append({"label": choice[1], "value": freq})
        except Exception as e:
            return res
        return res

    def get(self, request, slug="", product=""):
        if product == "scan":
            evaluation = (
                self.entity.entity_level.structure.get_main_entity.last_scan_evaluation
            )
        else:
            evaluation = (
                self.entity.entity_level.structure.get_main_entity.last_human_evaluation
            )
        params = json.loads(self.request.GET["filter"])
        if "default" in params and "human_criteria" in params:
            human_filters = {
                "age": params["default"]["age"],
                "civility": params["default"]["civility"],
                "human_criteria": HumanCriteriaChoice.objects.filter(
                    pk__in=params["human_criteria"]
                ).all(),
            }
        if (
            evaluation.is_human
            and evaluation.is_campus
            and "status" in params["default"]
        ):
            human_filters["status"] = params["default"]["status"]

        if product == "scan":
            collab_model = ScanCollaborator
            collaborators_field = "scan_collaborators"
        else:
            collab_model = Collaborator
            collaborators_field = "collaborators"

        exclude_collaborators = (
            collab_model.objects.annotate(num_answers=Count("answers"))
            .filter(
                num_answers=0,
                evaluation=evaluation,
                *prepare_human_filters_queries(
                    human_filters=human_filters, for_collaborators=True, is_human=True
                ),
            )
            .values_list("id")
        )
        if "human_criteria" in human_filters:
            criterias = evaluation.human_criteria.filter(
                choices__id__in=human_filters["human_criteria"]
            ).annotate(
                choice_ids=ArrayAgg(
                    "choices__id",
                    filter=Q(choices__id__in=human_filters["human_criteria"]),
                )
            )
            for criteria in criterias:
                exclude_collaborators = exclude_collaborators.filter(
                    human_criteria_choices__id__in=criteria.choice_ids
                )
        queryset = (
            collab_model.objects.filter(
                evaluation=evaluation,
                *prepare_human_filters_queries(
                    human_filters=human_filters, for_collaborators=True, is_human=True
                ),
            )
            .exclude(id__in=exclude_collaborators)
            .all()
        )
        if "human_criteria" in human_filters:
            criterias = evaluation.human_criteria.filter(
                choices__id__in=human_filters["human_criteria"]
            ).annotate(
                choice_ids=ArrayAgg(
                    "choices__id",
                    filter=Q(choices__id__in=human_filters["human_criteria"]),
                )
            )
            for criteria in criterias:
                queryset = queryset.filter(
                    human_criteria_choices__id__in=criteria.choice_ids
                )
        queryset = queryset.filter(evaluation=evaluation)
        nbCollaboratorFiltered = queryset.count()
        result = []
        ageresult = self.computed_human_collaborator(
            evaluation, "age", queryset, nbCollaboratorFiltered
        )
        result.append(
            {
                "id": 1,
                "indicator_type": "PieChart",
                "title": _("Répartition des répondants (f/h/nb) par âges"),
                "colors": [1, 2, 3, 4, 5],
                "display_params": {
                    "size": 1,
                    "order": 1,
                    "stacked": False,
                    "linked_with": [2],
                },
                "labels": [l["label"] for l in ageresult],
                "selector": False,
                "values": [round(v["value"], 2) for v in ageresult],
                "meanscore_sector_values": [],
                "meanscore_global_values": [],
            }
        )

        civilityresult = self.computed_human_collaborator(
            evaluation, "civility", queryset, nbCollaboratorFiltered
        )
        result.append(
            {
                "id": 2,
                "indicator_type": "PieChart",
                "title": _("Répartition des répondants (f/h/nb) par genres"),
                "colors": [1, 2, 3, 4, 5],
                "display_params": {
                    "size": 1,
                    "order": 1,
                    "stacked": False,
                    "linked_with": [1],
                },
                "labels": [l["label"] for l in civilityresult],
                "selector": False,
                "values": [round(v["value"], 2) for v in civilityresult],
                "meanscore_sector_values": [],
                "meanscore_global_values": [],
            }
        )

        if evaluation.is_campus:
            statusresult = self.computed_human_collaborator(
                evaluation, "status", queryset, nbCollaboratorFiltered
            )
            result.append(
                {
                    "id": 3,
                    "indicator_type": "ProgressBarChart",
                    "title": _("Répartition des répondants (f/h/nb) par status"),
                    "colors": [3],
                    "display_params": {
                        "size": 1,
                        "order": 1,
                        "stacked": False,
                        "linked_with": [],
                    },
                    "labels": [],
                    "selector_labels": [l["label"] for l in statusresult],
                    "selector": False,
                    "values": [round(v["value"], 2) for v in statusresult],
                    "meanscore_sector_values": [],
                    "meanscore_global_values": [],
                }
            )

        criterias = (
            evaluation.human_criteria.all()
            .annotate(count_choice=Count("choices"))
            .order_by("count_choice")
            .select_related("evaluation")
            .prefetch_related(
                Prefetch(
                    "choices",
                    queryset=HumanCriteriaChoice.objects.annotate(
                        total=Count(
                            collaborators_field,
                            filter=Q(**{f"{collaborators_field}__in": queryset}),
                        )
                    ).order_by("-total"),
                )
            )
        )
        i = 4
        for crit in criterias:
            crit_values = self.computed_criteria(crit, nbCollaboratorFiltered)
            result.append(
                {
                    "id": i,
                    "indicator_type": "ProgressBarChart",
                    "title": _("Répartition des répondants (f/h/nb) par ") + crit.label,
                    "colors": [3],
                    "display_params": {
                        "size": 1,
                        "order": 1,
                        "stacked": False,
                        "linked_with": [],
                    },
                    "labels": [],
                    "selector_labels": [l["label"] for l in crit_values],
                    "selector": False,
                    "values": [round(v["value"], 2) for v in crit_values],
                    "meanscore_sector_values": [],
                    "meanscore_global_values": [],
                }
            )
            i += 1

        return Response(result)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiIndicators(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    viewsets.ModelViewSet,
    StructureDataViewMixin,
):
    """
    Cette API permets de récupérer tous les indicateurs et de
    calculer les données pour chacun des ces indicateurs (en fonction des filtres actif si HUMAN)
    """

    serializer_class = IndicatorSerializer

    def display_version_from_slug(self, slug):
        year, month_slug = slug.split("-")
        result = year + "-"

        for month in MONTHS:
            if slugify(month) == month_slug:
                result += month
        return result

    def get_queryset(self, *args, **kwargs):
        params = self.request.GET
        if params["eval_id"]:
            self.assess_evaluation = (
                Evaluation.objects.select_related(
                    "entity__entity_level__structure__business_line"
                )
                .prefetch_related(
                    "entity__entity_level__structure__secondary_business_lines"
                )
                .get(pk=params["eval_id"])
            )
        else:
            self.assess_evaluation = (
                self.entity.entity_level.structure.get_main_entity.last_validated_by_admin_global_evaluation
            )

        evaluation = self.assess_evaluation
        return self.handle_questions_indicators(evaluation, params)

    def handle_questions_indicators(self, evaluation, params):
        def prevent_save(reset_mean_score=True):
            pass

        results = []
        # Evaluation questions with indicators only

        questions = (
            evaluation.get_questions_from_answers.annotate(
                first_ans_display=Subquery(
                    Answer.objects.filter(
                        question_id=OuterRef("id"), evaluation=evaluation, display=True
                    ).values("display")[:1],
                    output_field=BooleanField(),
                ),
                perimeter=Subquery(
                    Answer.objects.filter(
                        question_id=OuterRef("id"), evaluation=evaluation, display=True
                    ).values("perimeter_" + get_language())[:1],
                    output_field=TextField(),
                ),
            )
            .filter(
                indicator__isnull=False,
                category__slug=params.get("page", "all"),
                first_ans_display=True,
            )
            .prefetch_related("mandatory_tags", "forbidden_tags")
            .distinct()
            .order_by("indicator__displaying_params__order")
        )
        campus_tags = ["campus_collaborator", "campus_teacher", "campus_student"]
        if self.entity.entity_level.structure.category == "school":
            forbidden_filter = Q()
            for tag in campus_tags:
                forbidden_filter &= Q(forbidden_tags__name=tag)
            questions = questions.exclude(forbidden_filter)
        #
        # questions = questions.order_by("indicator__order")
        #
        human_limit = HUMAN_FILTER_LIMIT
        if evaluation.is_scan:
            human_limit = 5
        if evaluation.is_human or evaluation.is_scan:
            jsonfilter = json.loads(params["filter"].replace("'", '"'))
            collaborators_queryset = generate_collaborator_filters(
                jsonfilter["default"], jsonfilter["human_criteria"], evaluation
            )
            if (
                collaborators_queryset.filter(evaluation=evaluation).count()
                <= human_limit
            ):
                return results

        for question in questions:
            if evaluation.is_human or evaluation.is_scan:
                current_answer = Answer(
                    id=question.google_sheets_id,
                    question=question,
                    evaluation=evaluation,
                )
                current_answer.save = prevent_save
            else:
                current_answer = (
                    Answer.objects.filter(
                        question=question,
                        evaluation=evaluation,
                    )
                    .select_related("question")
                    .prefetch_related("subanswers")
                    .first()
                )
                if question.type == "date" and current_answer.value is None:
                    continue
            current_indicator = (
                question.indicator.select_related("question", "type")
                .prefetch_related("question__subquestions")
                .first()
            )
            if evaluation.is_human or evaluation.is_scan:
                current_indicator.scores_json = current_indicator.get_json(
                    evaluation=evaluation,
                    answer=current_answer,
                    queryset=collaborators_queryset,
                )
            else:
                current_indicator.scores_json = current_indicator.get_json(
                    evaluation=evaluation,
                    answer=current_answer,
                )
            if question.perimeter:
                current_indicator.scores_json["perimeter"] = question.perimeter
            results.append(current_indicator)
        return results

    def get_excluded_tags(self):
        tag_exclude = []
        if not self.entity.entity_level.structure.is_campus:
            tag_exclude = QuestionTag.objects.filter(
                name__in=["campus_student", "campus_teacher", "campus_collaborator"]
            )
        return tag_exclude

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiScanIndicators(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    """
    Cette API permets de générer tous les indicateurs scan et de calculer les données pour chacun d'entre eux
    """

    def display_version_from_slug(self, slug):
        year, month_slug = slug.split("-")
        result = year + "-"

        for month in MONTHS:
            if slugify(month) == month_slug:
                result += month
        return result

    # def get_queryset(self, *args, **kwargs):
    #     params = self.request.GET
    #     if params["eval_id"]:
    #         self.assess_evaluation = Evaluation.objects.get(pk=params["eval_id"])
    #     else:
    #         self.assess_evaluation = (
    #             self.entity.entity_level.structure.get_main_entity.last_validated_by_admin_global_evaluation
    #         )
    #
    #     evaluation = self.assess_evaluation
    #     return self.handle_questions_indicators(evaluation, params)
    #
    def get(self, request, slug="", product=""):
        params = self.request.GET
        if params["eval_id"]:
            self.assess_evaluation = Evaluation.objects.get(pk=params["eval_id"])
        else:
            self.assess_evaluation = (
                self.entity.entity_level.structure.get_main_entity.last_validated_by_admin_global_evaluation
            )
        evaluation = self.assess_evaluation
        return Response(self.handle_questions_indicators(evaluation, params))

    def handle_questions_indicators(self, evaluation, params):
        def prevent_save(reset_mean_score=True):
            pass

        results = []
        # Evaluation questions with indicators only

        # Agrégation des moyennes par question, en filtrant par évaluation et en utilisant le champ 'value' pour les multiple_qcm
        questions_with_avg = (
            Question.objects.filter(
                sheets=evaluation.sheet,
                category__slug=params.get("page", "general_concept"),
            )
            .annotate(
                # Moyenne des réponses QCM filtrées par évaluation et réponses associées
                qcm_equal_4=Count(
                    "answers__choice__value",
                    filter=Q(
                        type="qcm",
                        answers__evaluation=evaluation,
                        answers__choice__value=4,
                    ),
                ),
                # Moyenne des réponses QCM filtrées par évaluation et réponses associées
                qcm_total=Count(
                    "answers__choice__value",
                    filter=Q(
                        type="qcm",
                        answers__evaluation=evaluation,
                    ),
                ),
                # Ajout des annotations pour les rôles spécifiques dans SCAN_ROLE_CHOICE
                **{
                    f"count_equal_4_{role[0]}": Count(
                        "answers",
                        filter=Q(
                            type="qcm",
                            answers__evaluation=evaluation,
                            answers__scan_collaborator__job=role[0],
                            answers__choice__value=4,
                        ),
                    )
                    for role in SCAN_ROLE_CHOICE
                },
                # Ajout des annotations pour les rôles spécifiques dans SCAN_ROLE_CHOICE
                **{
                    f"count_total_{role[0]}": Count(
                        "answers",
                        filter=Q(
                            type="qcm",
                            answers__evaluation=evaluation,
                            answers__scan_collaborator__job=role[0],
                        ),
                    )
                    for role in SCAN_ROLE_CHOICE
                },
                # Moyenne QCM par secteur
                qcm_equal_4_sector=Count(
                    "answers__choice__value",
                    filter=Q(
                        type="qcm",
                        answers__evaluation__entity__entity_level__structure__business_line=evaluation.entity.entity_level.structure.business_line,
                        answers__evaluation=evaluation,
                        answers__choice__value=4,
                    ),
                ),
                # Moyenne QCM par secteur
                qcm_total_sector=Count(
                    "answers__choice__value",
                    filter=Q(
                        type="qcm",
                        answers__evaluation__entity__entity_level__structure__business_line=evaluation.entity.entity_level.structure.business_line,
                        answers__evaluation=evaluation,
                    ),
                ),
                # Moyenne QCM global
                qcm_equal_4_global=Count(
                    "answers__choice__value",
                    filter=Q(type="qcm", answers__choice__value=4),
                ),
                # Moyenne QCM global
                qcm_total_global=Count("answers__choice__value", filter=Q(type="qcm")),
                # Compte des réponses Multiple QCM ayant une valeur de 4
                mtp_qcm_equal_4=Count(
                    "answers",
                    filter=Q(
                        type="multiple_qcm",
                        answers__evaluation=evaluation,
                        answers__value=4,
                    ),
                ),
                # Moyenne des réponses Multiple QCM ayant une valeur de 0 ou moins
                mtp_qcm_lte_0=Count(
                    "answers",
                    filter=Q(
                        type="multiple_qcm",
                        answers__evaluation=evaluation,
                        answers__value__lte=0,
                    ),
                ),
                # Moyenne des réponses Multiple QCM ayant une valeur entre 0 et 4 (exclus)
                mtp_qcm_1_3=Count(
                    "answers",
                    filter=Q(
                        type="multiple_qcm",
                        answers__evaluation=evaluation,
                        answers__value__gt=0,
                        answers__value__lt=4,
                    ),
                ),
                # Compte total des réponses Multiple QCM
                mtp_qcm_total=Count(
                    "answers",
                    filter=Q(type="multiple_qcm", answers__evaluation=evaluation),
                ),
                # Ajout des annotations pour les rôles spécifiques dans SCAN_ROLE_CHOICE
                **{
                    f"mtp_qcm_equal_4{role[0]}": Count(
                        "answers",
                        filter=Q(
                            type="multiple_qcm",
                            answers__evaluation=evaluation,
                            answers__scan_collaborator__job=role[0],
                            answers__value=4,
                        ),
                    )
                    for role in SCAN_ROLE_CHOICE
                },
                # Ajout des annotations pour les rôles spécifiques dans SCAN_ROLE_CHOICE
                **{
                    f"mtp_qcm_lte_0{role[0]}": Count(
                        "answers",
                        filter=Q(
                            type="multiple_qcm",
                            answers__evaluation=evaluation,
                            answers__scan_collaborator__job=role[0],
                            answers__value__lte=0,
                        ),
                    )
                    for role in SCAN_ROLE_CHOICE
                },
                # Ajout des annotations pour les rôles spécifiques dans SCAN_ROLE_CHOICE
                **{
                    f"mtp_qcm_1_3{role[0]}": Count(
                        "answers",
                        filter=Q(
                            type="multiple_qcm",
                            answers__evaluation=evaluation,
                            answers__scan_collaborator__job=role[0],
                            answers__value__gt=0,
                            answers__value__lt=4,
                        ),
                    )
                    for role in SCAN_ROLE_CHOICE
                },
                # Ajout des annotations pour les rôles spécifiques dans SCAN_ROLE_CHOICE
                **{
                    f"mtp_qcm_total{role[0]}": Count(
                        "answers",
                        filter=Q(
                            type="multiple_qcm",
                            answers__evaluation=evaluation,
                            answers__scan_collaborator__job=role[0],
                        ),
                    )
                    for role in SCAN_ROLE_CHOICE
                },
                # Compte des réponses Multiple QCM ayant une valeur de 4 par secteur
                mtp_qcm_equal_4_sector=Count(
                    "answers",
                    filter=Q(
                        type="multiple_qcm",
                        answers__evaluation__entity__entity_level__structure__business_line=evaluation.entity.entity_level.structure.business_line,
                        answers__evaluation=evaluation,
                        answers__value=4,
                    ),
                ),
                # Moyenne des réponses Multiple QCM ayant une valeur de 0 ou moins par secteur
                mtp_qcm_lte_0_sector=Count(
                    "answers",
                    filter=Q(
                        type="multiple_qcm",
                        answers__evaluation__entity__entity_level__structure__business_line=evaluation.entity.entity_level.structure.business_line,
                        answers__evaluation=evaluation,
                        answers__value__lte=0,
                    ),
                ),
                # Moyenne des réponses Multiple QCM ayant une valeur entre 0 et 4 (exclus) par secteur
                mtp_qcm_1_3_sector=Count(
                    "answers",
                    filter=Q(
                        type="multiple_qcm",
                        answers__evaluation__entity__entity_level__structure__business_line=evaluation.entity.entity_level.structure.business_line,
                        answers__evaluation=evaluation,
                        answers__value__gt=0,
                        answers__value__lt=4,
                    ),
                ),
                # Compte total des réponses Multiple QCM par secteur
                mtp_qcm_total_sector=Count(
                    "answers",
                    filter=Q(
                        type="multiple_qcm",
                        answers__evaluation__entity__entity_level__structure__business_line=evaluation.entity.entity_level.structure.business_line,
                        answers__evaluation=evaluation,
                    ),
                ),
                # Compte des réponses Multiple QCM ayant une valeur de 4 par secteur
                mtp_qcm_equal_4_global=Count(
                    "answers", filter=Q(type="multiple_qcm", answers__value=4)
                ),
                # Moyenne des réponses Multiple QCM ayant une valeur de 0 ou moins par secteur
                mtp_qcm_lte_0_global=Count(
                    "answers", filter=Q(type="multiple_qcm", answers__value__lte=0)
                ),
                # Moyenne des réponses Multiple QCM ayant une valeur entre 0 et 4 (exclus) par secteur
                mtp_qcm_1_3_global=Count(
                    "answers",
                    filter=Q(
                        type="multiple_qcm", answers__value__gt=0, answers__value__lt=4
                    ),
                ),
                # Compte total des réponses Multiple QCM par secteur
                mtp_qcm_total_global=Count("answers", filter=Q(type="multiple_qcm")),
            )
            .values(
                "google_sheets_id",
                "label",
                "scan_indicator_label",
                "qcm_equal_4",
                "qcm_total",
                *[f"count_equal_4_{role[0]}" for role in SCAN_ROLE_CHOICE],
                *[f"count_total_{role[0]}" for role in SCAN_ROLE_CHOICE],
                "qcm_equal_4_sector",
                "qcm_total_sector",
                "qcm_equal_4_global",
                "qcm_total_global",
                "mtp_qcm_equal_4",
                "mtp_qcm_lte_0",
                "mtp_qcm_1_3",
                "mtp_qcm_total",
                *[f"mtp_qcm_equal_4{role[0]}" for role in SCAN_ROLE_CHOICE],
                *[f"mtp_qcm_lte_0{role[0]}" for role in SCAN_ROLE_CHOICE],
                *[f"mtp_qcm_1_3{role[0]}" for role in SCAN_ROLE_CHOICE],
                *[f"mtp_qcm_total{role[0]}" for role in SCAN_ROLE_CHOICE],
                "mtp_qcm_equal_4_sector",
                "mtp_qcm_lte_0_sector",
                "mtp_qcm_1_3_sector",
                "mtp_qcm_total_sector",
                "mtp_qcm_equal_4_global",
                "mtp_qcm_lte_0_global",
                "mtp_qcm_1_3_global",
                "mtp_qcm_total_global",
            )
        )

        for question in questions_with_avg:
            multiple_score = [0, 0, 0]
            multiple_score_by_jobs = []
            multiple_sector_score = None
            multiple_global_score = None
            count_roles_with_values = 0
            need_selector = False
            if question["mtp_qcm_total"] != 0:
                multiple_score = [
                    round(
                        question["mtp_qcm_equal_4"] / question["mtp_qcm_total"] * 100, 2
                    ),
                    round(question["mtp_qcm_1_3"] / question["mtp_qcm_total"] * 100, 2),
                    round(
                        question["mtp_qcm_lte_0"] / question["mtp_qcm_total"] * 100, 2
                    ),
                ]
            for role in SCAN_ROLE_CHOICE:
                if question.get(f"mtp_qcm_total{role[0]}", 0) > 0:
                    count_roles_with_values += 1
                    if count_roles_with_values >= 2:
                        need_selector = True
                        break
            for role in SCAN_ROLE_CHOICE:
                if question.get(f"mtp_qcm_total{role[0]}", 0) != 0:
                    multiple_score_by_jobs.append(
                        [
                            round(
                                question.get(f"mtp_qcm_equal_4{role[0]}", 0)
                                / question.get(f"mtp_qcm_total{role[0]}", 1)
                                * 100,
                                2,
                            ),
                            round(
                                question.get(f"mtp_qcm_1_3{role[0]}", 0)
                                / question.get(f"mtp_qcm_total{role[0]}", 1)
                                * 100,
                                2,
                            ),
                            round(
                                question.get(f"mtp_qcm_lte_0{role[0]}", 0)
                                / question.get(f"mtp_qcm_total{role[0]}", 1)
                                * 100,
                                2,
                            ),
                        ]
                    )
                else:
                    multiple_score_by_jobs.append([0, 0, 0])
            multiple_score_by_jobs = [multiple_score] + multiple_score_by_jobs
            if question["mtp_qcm_total_sector"] != 0:
                multiple_sector_score = [
                    round(
                        question["mtp_qcm_equal_4_sector"]
                        / question["mtp_qcm_total_sector"]
                        * 100,
                        2,
                    ),
                    round(
                        question["mtp_qcm_1_3_sector"]
                        / question["mtp_qcm_total_sector"]
                        * 100,
                        2,
                    ),
                    round(
                        question["mtp_qcm_lte_0_sector"]
                        / question["mtp_qcm_total_sector"]
                        * 100,
                        2,
                    ),
                ]
                multiple_global_score = [
                    round(
                        question["mtp_qcm_equal_4_global"]
                        / question["mtp_qcm_total_global"]
                        * 100,
                        2,
                    ),
                    round(
                        question["mtp_qcm_1_3_global"]
                        / question["mtp_qcm_total_global"]
                        * 100,
                        2,
                    ),
                    round(
                        question["mtp_qcm_lte_0_global"]
                        / question["mtp_qcm_total_global"]
                        * 100,
                        2,
                    ),
                ]
            if question["mtp_qcm_total"]:
                result = {
                    "title": question["label"],
                    "scores_json": {
                        "id": question["google_sheets_id"],
                        "indicator_type": "ScanBarChart",
                        "title": question["label"],
                        "label": question["scan_indicator_label"],
                        "colors": [1, 2, 3, 4, 5],
                        "display_params": {
                            "size": 1,
                            "order": 1,
                            "stacked": False,
                            "linked_with": [],
                        },
                        "labels": [
                            _("Total général"),
                            _("Directeur (f/h/nb)"),
                            _("Manager (f/h/nb)"),
                            _("Recruteur (f/h/nb)"),
                            _("Autres (f/h/nb)"),
                        ],
                        "selector_labels": [_("Global"), _("Détaillé")],
                        "selector": need_selector,
                        "values": [multiple_score, multiple_score_by_jobs],
                        "meanscore_sector_values": [multiple_sector_score, 0],
                        "meanscore_global_values": [multiple_global_score, 0],
                    },
                }
            else:
                score = None
                sector_score = None
                global_score = None
                need_selector = False
                count_roles_with_values = 0
                if question["qcm_total"] != 0:
                    score = [
                        round(question["qcm_equal_4"] / question["qcm_total"] * 100, 2)
                    ]
                scores = [
                    (
                        round(
                            question.get(f"count_equal_4_{role[0]}", 0)
                            / question.get(f"count_total_{role[0]}", 1)
                            * 100,
                            2,
                        )
                        if question.get(f"count_total_{role[0]}", 0) != 0
                        else 0
                    )
                    for role in SCAN_ROLE_CHOICE
                ]
                for role in SCAN_ROLE_CHOICE:
                    if question.get(f"count_total_{role[0]}", 0) > 0:
                        count_roles_with_values += 1
                        if count_roles_with_values >= 2:
                            need_selector = True
                            break
                scores = score + scores
                if question["qcm_total_sector"] != 0:
                    sector_score = [
                        round(
                            question["qcm_equal_4_sector"]
                            / question["qcm_total_sector"]
                            * 100,
                            2,
                        )
                    ]
                    global_score = [
                        round(
                            question["qcm_equal_4_global"]
                            / question["qcm_total_global"]
                            * 100,
                            2,
                        )
                    ]
                result = {
                    "title": question["label"],
                    "scores_json": {
                        "id": question["google_sheets_id"],
                        "indicator_type": "ScanCircularChart",
                        "title": question["label"],
                        "label": question["scan_indicator_label"],
                        "colors": [1, 2, 3, 4, 5],
                        "display_params": {
                            "size": 1,
                            "order": 1,
                            "stacked": False,
                            "linked_with": [],
                        },
                        "labels": [
                            _("Total général"),
                            _("Directeur (f/h/nb)"),
                            _("Manager (f/h/nb)"),
                            _("Recruteur (f/h/nb)"),
                            _("Autres (f/h/nb)"),
                        ],
                        "selector_labels": [_("Global"), _("Détaillé")],
                        "selector": need_selector,
                        "values": [score, scores[::-1]],
                        "meanscore_sector_values": [sector_score, [0]],
                        "meanscore_global_values": [global_score, [0]],
                    },
                }
            results.append(result)
        return results

    def get_excluded_tags(self):
        tag_exclude = []
        if not self.entity.entity_level.structure.is_campus:
            tag_exclude = QuestionTag.objects.filter(
                name__in=["campus_student", "campus_teacher", "campus_collaborator"]
            )
        return tag_exclude

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class DashboardGetAllIndicators(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = AllIndicatorSerializer

    def get_queryset(self, *args, **kwargs):
        return Question.objects.all()

    def test_func(self):
        return self.request.user.is_staff


class DashboardGetOneIndicators(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    viewsets.ModelViewSet,
):
    serializer_class = OneIndicatorSerializer

    def get_queryset(self, *args, **kwargs):
        params = self.request.GET

        return Question.objects.all().filter(google_sheets_id=params["indicator"])

    def test_func(self):
        return self.request.user.is_staff


class ApiDiagCaracteristics(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    DashboardAssessViewMixin,
    APIView,
):
    """
    Cette API renvois les résultats de certaines questions très générales
    """

    def get(self, request, slug="", product=""):
        if self.assess_evaluation is None:
            self.assess_evaluation = (
                self.entity.entity_level.structure.get_main_entity.last_global_evaluation
            )
        else:
            self.assess_evaluation = self.assess_evaluation
        evaluation = self.assess_evaluation
        return Response(self.handle_concerned_questions(evaluation))

    def handle_concerned_questions(self, evaluation):
        questions = [
            {
                "title": _("Effectif total"),
                "id": 20236002,
            },
            {
                "title": _("Nombre de cadres dirigeants (f/h/nb)"),
                "id": 20236003,
            },
            {
                "title": _("Nombre de managers (f/h/nb)"),
                "id": 20236004,
            },
            {
                "title": _("Nombre de personnes en charge du recrutement"),
                "id": 20236005,
            },
            {
                "title": _("Nombre de personnes en charge des achats"),
                "id": 20236006,
            },
            {
                "title": _("Nombre de personnes en alternance"),
                "id": 20236007,
            },
            {
                "title": _("Nombre de personnes en stage"),
                "id": 20236008,
            },
            {
                "title": _("Nombre de personnes recrutées dans les 12 derniers mois"),
                "id": 20236009,
            },
            {
                "title": _(
                    "Nombre de personnes recrutées en alternance dans les 12 derniers mois"
                ),
                "id": 202360081,
            },
            {
                "title": _(
                    "Nombre de personnes recrutées en stage dans les 12 derniers mois"
                ),
                "id": 202360091,
            },
            {
                "title": _("Nombre d'étudiants accueillis dans les 12 derniers mois"),
                "id": 20221003,
            },
            {
                "title": _(
                    "Nombre de personnes en stage et alternance parmi les étudiants (f/h/nb)"
                ),
                "id": 20221007,
            },
        ]
        query = list(
            Answer.objects.filter(
                evaluation=evaluation,
                question__google_sheets_id__in=[
                    questions[i]["id"] for i in range(len(questions))
                ],
            )
            .values("question__google_sheets_id", "value")
            .annotate(subs_values=Sum("subanswers__value"))
        )
        answers = []
        for i in range(len(questions)):
            found = False
            for q in query:
                if q["question__google_sheets_id"] == questions[i]["id"]:
                    q["label"] = questions[i]["title"]
                    answers.append(q)
                    found = True
                    break
            if not found:
                temp = {}
                temp["value"] = None
                temp["question__google_sheets_id"] = questions[i]["id"]
                temp["label"] = questions[i]["title"]
                answers.append(temp)
        return answers

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)


class ApiQuestion(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    APIView,
):
    """
    Cette API retourne les questions nécessaire pour remplir le questionnaire en cours (Diag, Human ou Scan)
    """

    eval_type = {
        "diag": "mixity_evaluation_diag",
        "human": "evaluation_collaborateurs_360",
        "scan": "mixity_evaluation_scan",
    }

    def get(self, request, slug="", product=""):
        evaluation = Evaluation.objects.get(
            entity__slug=self.kwargs["slug"],
            sheet__type__slug=self.eval_type[product],
            display_version="en-cours",
        )
        criterias_list = []
        if self.kwargs["product"] == "diag":
            questions = evaluation.get_questions()
        elif self.kwargs["product"] == "scan":
            questions = Question.objects.filter(sheets=evaluation.sheet).order_by(
                "google_sheets_id"
            )
            # collaborator = self.request.user.scan_collaborator
            # criterias_list.append(collaborator.job)
            # for criteria_choice in collaborator.scan_criteria_choices.all():
            #     criterias_list.append(criteria_choice.label)
            # questions = evaluation.get_questions_human(criteria_tags=criterias_list)
        else:
            collaborator = self.request.user.collaborator
            for criteria_choice in collaborator.human_criteria_choices.all():
                criterias_list.append(criteria_choice.label)
            questions = evaluation.get_questions_human(criteria_tags=criterias_list)
        questions_dict = [
            {
                "google_sheets_id": question.google_sheets_id,
                "label": question.label,
                "type": question.type,
                "choices": list(question.choices.values()),
                "feedback": question.feedback,
                "category": question.category.id,
                "subcategory": question.subcategory.id,
            }
            for question in questions
        ]
        return Response(questions_dict)

    def test_func(self):
        is_collaborator = False
        if self.kwargs["product"] == "scan":
            evaluation = Evaluation.objects.get(
                entity__slug=self.kwargs["slug"],
                sheet__type__slug="mixity_evaluation_scan",
                display_version="en-cours",
            )
            is_collaborator = (
                self.request.user.scan_collaborator
                in evaluation.scan_collaborators.all()
            )
        elif self.kwargs["product"] == "human":
            evaluation = Evaluation.objects.get(
                entity__slug=self.kwargs["slug"],
                sheet__type__slug="evaluation_collaborateurs_360",
                display_version="en-cours",
            )
            is_collaborator = (
                self.request.user.scan_collaborator
                in evaluation.scan_collaborators.all()
            )
        if is_collaborator:
            return is_collaborator
        else:
            return self.request.user.test_func_rights(self.entity)


class ApiAnswer(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DashboardStructureViewMixin,
    APIView,
):
    """
    Cette API permet de récupérer les réponses déjà repondus et de
    sauvegarder les réponses correctement selon le type de leur question
    """

    eval_type = {
        "diag": "mixity_evaluation_diag",
        "human": "evaluation_collaborateurs_360",
        "scan": "mixity_evaluation_scan",
    }

    def create_answer_dict_for_survey(self, answers):
        answers_dict = [
            {
                "id": answer.id,
                "question": answer.question.google_sheets_id,
                "choice": answer.choice.id if answer.choice else None,
                "choices": list(answer.choices.values()),
                "value": answer.value,
                "text_value": answer.text_value,
                "date_answered": answer.date_answered,
            }
            for answer in answers
        ]
        return answers_dict

    def create_answer_dict_for_user_assess(self, answers):
        answers_dict = [
            {
                "label": answer.question.label,
                "choices": list(answer.question.choices.values("id", "label", "value")),
                "feedback": answer.question.feedback,
                "category": answer.question.category.slug,
                "answer_choice": answer.choice.id if answer.choice else None,
                "answer_choices": list(answer.choices.values_list("id", flat=True)),
            }
            for answer in answers
        ]
        return answers_dict

    def get(self, request, slug="", product=""):
        if slug and product:
            evaluation = Evaluation.objects.get(
                entity__slug=slug,
                sheet__type__slug=self.eval_type[product],
                display_version="en-cours",
            )
            answers = Answer.objects.filter(evaluation=evaluation)
            if product == "diag":
                return Response(list(answers))
            else:
                if product == "scan":
                    answers = list(
                        answers.filter(
                            scan_collaborator=self.request.user.scan_collaborator
                        )
                    )
                else:
                    answers = list(
                        answers.filter(collaborator=self.request.user.collaborator)
                    )
                    if evaluation.need_auth and answers.count() != 0:
                        return JsonResponse(
                            {
                                "message": _(
                                    "L'utilisateur a déjà répondu aux questionnaire."
                                ),
                                "success": False,
                            },
                            status=status.HTTP_403_FORBIDDEN,
                        )
                return Response(self.create_answer_dict_for_survey(answers))
        else:
            scan_collaborator_answers = Answer.objects.filter(
                scan_collaborator=self.request.user.scan_collaborator
            ).prefetch_related("question__choices", "choices")
            return Response(
                self.create_answer_dict_for_user_assess(scan_collaborator_answers)
            )

    def post(self, request, *args, **kwargs):
        data = request.data
        evaluation = Evaluation.objects.get(
            entity__slug=self.kwargs["slug"],
            sheet__type__slug=self.eval_type[self.kwargs["product"]],
            display_version="en-cours",
        )
        question = Question.objects.get(google_sheets_id=data["question_id"])
        answer, created = Answer.objects.get_or_create(
            id=data["answer_id"],
            question=question,
            scan_collaborator=self.request.user.scan_collaborator,
            evaluation=evaluation,
        )
        # j'ai fait seulement qcm pour le moment car c'est le seul type de question pour scan
        if question.type == "qcm":
            choice = Choice.objects.select_related("question").get(id=data["choice"])
            answer.choice = choice
            answer.date_answered = timezone.now()
            answer.save()
        elif question.type == "multiple_qcm":
            choices = list(
                Choice.objects.select_related("question").filter(
                    id__in=data["choices"], question=question
                )
            )
            for choice in choices:
                answer.choices.add(choice)
            answer.date_answered = timezone.now()
            answer.save()

        return Response(self.create_answer_dict_for_survey([answer]))

    def test_func(self):
        is_collaborator = False
        if self.kwargs:
            if self.kwargs["product"] == "scan":
                evaluation = Evaluation.objects.get(
                    entity__slug=self.kwargs["slug"],
                    sheet__type__slug="mixity_evaluation_scan",
                    display_version="en-cours",
                )
                is_collaborator = (
                    self.request.user.scan_collaborator
                    in evaluation.scan_collaborators.all()
                )
            elif self.kwargs["product"] == "human":
                evaluation = Evaluation.objects.get(
                    entity__slug=self.kwargs["slug"],
                    sheet__type__slug="evaluation_collaborateurs_360",
                    display_version="en-cours",
                )
                is_collaborator = (
                    self.request.user.scan_collaborator
                    in evaluation.scan_collaborators.all()
                )
            if is_collaborator:
                return is_collaborator
        else:
            if self.request.user.scan_collaborator:
                return True
            else:
                return self.request.user.test_func_rights(self.entity)


class APIAvailableCategoriesAndSubcategories(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, APIView
):
    """
    Cette API permets de récupérer les catégories et sous-catégories contenant des questions sur le questionnaire en cours
    Permet d'avoir un fil d'Ariane dynamique pour les clients pendant le questionnaire
    """

    def get(self, request, slug="", product=""):
        data = request.data
        evaluation = Evaluation.objects.filter(
            evaluation__entity__slug=slug,
            evaluation__entity__product__slug=product,
        ).order_by("-created_date")
        categories_dict = defaultdict(set)

        if product == "diag":
            questions = evaluation.get_questions()
        else:
            questions = evaluation.get_questions_human(
                data["mandatory_tags"], data["forbidden_tags"], data["criteria_tags"]
            )

        for question in questions:
            category_name = question.category.name
            subcategory_name = (
                question.subcategory.name if question.subcategory else None
            )

            if subcategory_name:
                categories_dict[category_name].add(subcategory_name)
            else:
                categories_dict[category_name]

        result = [
            {category: sorted(list(subcategories))}
            for category, subcategories in categories_dict.items()
        ]

        return Response(result)

    def test_func(self):
        return self.request.user in self.entity.entity_level.structure.members.all()


@job("default")
def generate_ia_scan(user_id):
    instance = IAScan.get_instance()
    user = ScanCollaborator.objects.get(id=user_id)
    eval_id = user.evaluation.id
    response = instance.do_scan_analysis(eval_id, user)
    if response["status"] == "error":
        print(response["error"])


class ApiCollaboratorInfo(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, APIView
):
    """
    Cette API permets de récupérer les informations générales du collaborateurs ayant répondus à un SCAN
    Ainsi que de récupérer son profil lorsqu'il a finis de répondre à son Mixity SCAN
    """

    def get(self, request, slug="", product="", version=""):
        collaborator_qs = ScanCollaborator.objects.filter(
            user=request.user
        ).prefetch_related("scan_criteria_choices")
        serializer = ScanCollaboratorSerializer(collaborator_qs, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        data = request.data
        if self.kwargs["product"] == "scan" and data["actiontype"] == "criterias":
            collaborator = self.request.user.scan_collaborator
            collaborator.civility = data["choices"]["civility"]
            collaborator.age = data["choices"]["age"]
            collaborator.job = data["choices"]["job"]
            for criteria, choice in data["choices"].items():

                if criteria not in ["civility", "age", "job"]:
                    collaborator.scan_criteria_choices.add(choice)
            collaborator.save()
            serializer = ScanCollaboratorSerializer([collaborator], many=True)
            return Response(serializer.data)
        elif data["actiontype"] == "profile":
            self.request.user.scan_collaborator.define_collaborator_profile()
            collaborator_qs = ScanCollaborator.objects.filter(
                user=request.user
            ).prefetch_related("scan_criteria_choices")

            response = generate_ia_scan.delay(collaborator_qs.first().id)

            serializer = ScanCollaboratorSerializer(collaborator_qs, many=True)
            return Response(serializer.data)

    def test_func(self):
        is_collaborator = False
        if "survey" in self.request.path:
            if self.kwargs["product"] == "scan":
                evaluation = (
                    self.entity.entity_level.structure.get_main_entity.last_scan_evaluation
                )
                is_collaborator = (
                    self.request.user.scan_collaborator
                    in evaluation.scan_collaborators.all()
                )
            elif self.kwargs["product"] == "human":
                evaluation = Evaluation.objects.get(
                    entity__slug=self.kwargs["slug"],
                    sheet__type__slug="evaluation_collaborateurs_360",
                    display_version="en-cours",
                )
                is_collaborator = (
                    self.request.user.scan_collaborator
                    in evaluation.scan_collaborators.all()
                )
        if is_collaborator:
            return is_collaborator
        else:
            return self.request.user.test_func_rights(self.entity)


class ApiCriterias(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, APIView
):
    """
    Cette API récupère les différents filtres auxquels le colalborateur doit répondre en début de question SCAN et HUMAN
    """

    eval_type = {
        "diag": "mixity_evaluation_diag",
        "human": "evaluation_collaborateurs_360",
        "scan": "mixity_evaluation_scan",
    }

    def get(self, request, slug="", product="", version=""):
        data = {
            "civility": CIVILITY_CHOICES,
            "age": AGE_CHOICES,
        }
        if product == "scan":
            data["job"] = SCAN_ROLE_CHOICE
        evaluation = (
            Evaluation.objects.filter(
                entity__slug=self.kwargs["slug"],
                sheet__type__slug=self.eval_type[product],
                display_version="en-cours",
            )
            .prefetch_related("human_criteria__choices")
            .first()
        )
        for hc in evaluation.human_criteria.all():
            data[hc.label] = [[choice.id, choice.label] for choice in hc.choices.all()]
        return Response(data)

    def test_func(self):
        is_collaborator = False
        if self.kwargs["product"] == "scan":
            evaluation = Evaluation.objects.get(
                entity__slug=self.kwargs["slug"],
                sheet__type__slug="mixity_evaluation_scan",
                display_version="en-cours",
            )
            is_collaborator = (
                self.request.user.scan_collaborator
                in evaluation.scan_collaborators.all()
            )
        elif self.kwargs["product"] == "human":
            evaluation = Evaluation.objects.get(
                entity__slug=self.kwargs["slug"],
                sheet__type__slug="evaluation_collaborateurs_360",
                display_version="en-cours",
            )
            is_collaborator = (
                self.request.user.scan_collaborator
                in evaluation.scan_collaborators.all()
            )
        if is_collaborator:
            return is_collaborator
        else:
            return self.request.user.test_func_rights(self.entity)


class ApiAllCollaboratorScores(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, APIView
):
    """
    Cette API calcul et renvois tous ses scores aggrégés SCAN d'un collaborateur
    """

    def get(self, request, slug="", product="", version=""):
        collaborator = ScanCollaborator.objects.get(user=request.user)
        data = {
            "global": collaborator.get_global_rate(),
            "categories": collaborator.get_categories_rate,
            "subcategories": collaborator.get_subcategories_rate,
            "skills": collaborator.get_skills_rate,
        }
        return Response(data)

    def test_func(self):
        return self.request.user.scan_collaborator


class ApiIAScanAnalysis(
    LoginRequiredMixin, UserPassesTestMixin, DashboardStructureViewMixin, APIView
):
    """
    Cette API appelle la class qui récupère l'analyse perso de Scan.
    """

    def get(self, request):
        user = ScanCollaborator.objects.get(user=request.user)

        result = {
            "general_concept": {"strength": [], "weakness": [], "aim": []},
            "professional_practice": {"strength": [], "weakness": [], "aim": []},
            "cognitive_biases": {"strength": [], "weakness": [], "aim": []},
            "communication": {"strength": [], "weakness": [], "aim": []},
            "professional_engagement": {"strength": [], "weakness": [], "aim": []},
        }

        if not IAScanAnalysis.objects.filter(
            evaluation=user.evaluation, scan_collaborator=user
        ).exists():
            return Response(result)

        analysis = (
            IAScanAnalysis.objects.filter(
                evaluation=user.evaluation, scan_collaborator=user
            )
            .prefetch_related("ia_scan_analysis_elements")
            .first()
        )

        elements: list[IAScanAnalysisElement] = analysis.ia_scan_analysis_elements.all()

        for element in elements:
            result[element.category.slug][element.type].append(element.content)

        return Response(result)

    def test_func(self):
        return self.request.user.test_func_rights(self.entity)
