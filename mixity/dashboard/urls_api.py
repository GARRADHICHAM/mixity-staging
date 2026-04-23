from django.views.decorators.csrf import csrf_exempt

from mixity.dashboard import views_api
from rest_framework import routers
from django.urls import path
from .views_api import ApiAssessEvaluation


urlpatterns = [
    path("membership/", views_api.ApiMembership.as_view(), name="api_membership"),
    path("region/", views_api.ApiRegion.as_view(), name="api_region"),
    path(
        "mixity-members/",
        views_api.ApiMixityMembers.as_view(),
        name="api_mixity_members",
    ),
    path(
        "<int:score_cat_pk>/subcategory-scores/",
        views_api.ApiSubCategoryScores.as_view(),
        name="api_subcategory_scores",
    ),
    path(
        "human-form-choices/",
        views_api.ApiHumanFormChoices.as_view(),
        name="api_human_form_choices",
    ),
    path(
        "<int:evaluation_pk>/reopening-request",
        views_api.ApiReevaluationRequest.as_view(),
        name="api_reevaluation_request",
    ),
    path(
        "human-collaborators-count/",
        views_api.ApiHumanCollaboratorsCount.as_view(),
        name="api_human_collaborators_count",
    ),
    path(
        "human-collaborators-infos/",
        views_api.ApiHumanCollaboratorsInfos.as_view(),
        name="api_human_collaborators_infos",
    ),
    path(
        "scan-indicators/",
        views_api.ApiScanIndicators.as_view(),
        name="api_scan_indicators",
    ),
    path(
        "diag-caracteristics/",
        views_api.ApiDiagCaracteristics.as_view(),
        name="api_diag_caracteristics",
    ),
    path(
        "radar-data/",
        views_api.APIRadarDataFilter.as_view(),
        name="api_radar_data",
    ),
    path(
        "open-responses/",
        views_api.ApiOpenResponses.as_view(),
        name="api_open_responses",
    ),
    path(
        "block-responses/",
        views_api.ApiBlockResponses.as_view(),
        name="api_block_responses",
    ),
    path(
        "<int:evaluation_pk>/handle-collaborators-list/",
        views_api.ApiHandleCollaboratorsList.as_view(),
        name="api_handle_collaborators_list",
    ),
    path(
        "<int:evaluation_pk>/add-filter/",
        views_api.ApiAddFilter.as_view(),
        name="api_add_filter",
    ),
    path(
        "<int:evaluation_pk>/delete-filter/",
        views_api.ApiDeleteFilter.as_view(),
        name="api_delete_filter",
    ),
    path(
        "<int:evaluation_pk>/modify-filter-choice/",
        views_api.ApiModifyFilterChoice.as_view(),
        name="api_modify_filter_choice",
    ),
    path(
        "<int:evaluation_pk>/delete-filter-choice/",
        views_api.ApiDeleteFilterChoice.as_view(),
        name="api_delete_filter_choice",
    ),
    path(
        "<int:evaluation_pk>/start-evaluation/",
        views_api.ApiStartEvaluation.as_view(),
        name="api_start_evaluation",
    ),
    path(
        "assess-evaluation/<str:version>/",
        views_api.ApiAssessEvaluation.as_view({"get": "retrieve_evaluation"}),
        name="api_assess_evaluation",
    ),
    path(
        "<int:evaluation_pk>/subscription-option/",
        views_api.ApiSubscriptionOption.as_view(),
        name="api_subscription_option",
    ),
    path(
        "<int:structure_id>/subscription-pack/",
        views_api.ApiSubscriptionPack.as_view(),
        name="api_subscription_pack",
    ),
    path(
        "<int:pk>/namsor-indicator-content/",
        views_api.NamsorIndicatorContent.as_view(),
        name="namsor_indicator_content",
    ),
    path(
        "<int:pk>/get_children_tree/",
        views_api.EntityTree.as_view(),
        name="entity_children_tree",
    ),
    # path(
    #     "<slug:elearning>/elearning/",
    #     views_api.ApiElearningDetails.as_view(),
    #     name="api_elearning_details",
    # ),
    path(
        "<slug:slug>/<slug:product>/question/",
        views_api.ApiQuestion.as_view(),
        name="api_question",
    ),
    path(
        "available_categories/",
        views_api.APIAvailableCategoriesAndSubcategories.as_view(),
        name="api_available_categories",
    ),
    path(
        "<slug:slug>/<slug:product>/survey/collaborator-info/",
        views_api.ApiCollaboratorInfo.as_view(),
        name="api_collaborator_info",
    ),
    path(
        "all-collaborator-scores/",
        views_api.ApiAllCollaboratorScores.as_view(),
        name="api_all-collaborator-scores",
    ),
    path(
        "<slug:slug>/<slug:product>/answer/",
        views_api.ApiAnswer.as_view(),
        name="api_answers_info",
    ),
    path("answer/", views_api.ApiAnswer.as_view(), name="api_answers_info"),
    path(
        "<slug:slug>/<slug:product>/criterias/",
        views_api.ApiCriterias.as_view(),
        name="api_criterias",
    ),
    path(
        "ia-scan-analysis/",
        views_api.ApiIAScanAnalysis.as_view(),
        name="api_ia_scan_analysis",
    ),
]

router = routers.DefaultRouter()
router.register("structure", views_api.ApiStructure, "api_structure")
router.register("entity", views_api.ApiEntity, "api_entity")
router.register("user", views_api.ApiUser, "api_user")
router.register("entities", views_api.ApiEntities, "api_entities")
router.register("category", views_api.ApiCategory, "api_category")
# router.register(
#     "global-evaluation", views_api.ApiGlobalEvaluation, "api_global_evaluation"
# )
router.register(
    "last-diag-evaluation", views_api.ApiLastDiagEvaluation, "api_last_diag_evaluation"
)
router.register(
    "get-indicators", views_api.DashboardGetAllIndicators, "api_get_all_indicators"
),
router.register(
    "info-indicators",
    views_api.DashboardGetOneIndicators,
    "api_count_indicators",
),
# router.register(
#     "human-evaluation", views_api.ApiHumanEvaluation, "api_human_evaluation"
# )
router.register(
    "last-human-evaluation",
    views_api.ApiLastHumanEvaluation,
    "api_last_human_evaluation",
)

router.register(
    "evaluations-versions-list",
    views_api.ApiEvaluationsVersionsList,
    "api_evaluations_versions_list",
)
router.register("action", views_api.ApiAction, "api_action")
router.register("first-five-actions", views_api.ApiFirstFiveAction, "api_action")
router.register("solution", views_api.ApiSolution, "api_solution")
router.register(
    "first-five-solutions", views_api.ApiFirstFiveSolution, "api_five_solutions"
)
router.register("objective", views_api.ApiObjective, "api_objective")
router.register(
    "aims_to_objectives",
    views_api.ApiCreateObjectiveFromEvaluation,
    "api_aims_to_objectives",
)
router.register("kpi", views_api.ApiKpi, "api_kpi")
router.register("generickpi", views_api.ApiGenericKpi, "api_generickpi")
router.register("solutionkeyword", views_api.ApiSolutionKeyword, "api_solutionkeyword")
router.register("solvers", views_api.ApiSolvers, "api_solvers")
router.register("language", views_api.ApiLanguage, "api_language")
router.register("solver", views_api.ApiSolver, "api_solver")
router.register("solver-solution", views_api.ApiSolverSolution, "api_solution_solver")
router.register("formats", views_api.ApiSolutionFormats, "api_format")
router.register(
    "collaboratorstatistics",
    views_api.ApiCollaboratorsStatistics,
    "api_collaboratorstatistics",
)
router.register("upload-csv", views_api.ApiUploadCSV, "api_uploadcsv")
# Best Practices routers
router.register(
    "best-practice",
    views_api.ApiBestPractice,
    "api_best_practice",
)
router.register(
    "practicer",
    views_api.ApiPracticer,
    "api_practicer",
)
router.register(
    "best-practice-management",
    views_api.ApiBestPracticeManagement,
    "api_best_practice_management",
)
router.register(
    "best-practice-search",
    views_api.ApiBestPracticeSearch,
    "api_best_practice_search",
)
router.register(
    "bestpractice-keyword", views_api.ApiBestPracticeKeyword, "api_bestpractice_keyword"
)
router.register(
    "bestpractice-type", views_api.ApiBestPracticeType, "api_bestpractice_type"
)
router.register(
    "bestpractice-public", views_api.ApiBestPracticePublic, "api_bestpractice_public"
)
router.register(
    "organization-type", views_api.ApiOrganizationType, "api_organization_type"
)
router.register(
    "bestpractice-size", views_api.ApiBestPracticeSize, "api_bestpractice_size"
)
router.register(
    "assess-score-categories",
    views_api.ApiAssessScoreCategories,
    "api_assess_score_categories",
)
router.register(
    "indicators",
    views_api.ApiIndicators,
    "api_indicators",
)
router.register(
    "get_indicators", views_api.DashboardGetAllIndicators, "api_get_all_indicators"
),
router.register("comments", views_api.ApiComments, "api_comments"),
router.register(
    "general-analysis", views_api.ApiGeneralAnalysis, "api_general_analysis"
),
# router.register(r"elearning", views_api.ApiElearning, basename="api_elearning"),


urlpatterns += router.urls
