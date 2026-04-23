import datetime

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django_countries import countries

# COUNTRIES_CHOICES used in hold migration
# scoring/migrations/0132_import_countries.py
COUNTRIES_CHOICES = list(countries)
COUNTRIES_CHOICES.insert(0, ["EV", _("International")])

# https://www23.statcan.gc.ca/imdb/p3VD_f.pl?Function=getVD&TVD=141329
EUROPEAN_COUNTRY_CODE = [
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "GR",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
]


DPT_CHOICES = (
    ("01", "Ain"),
    ("02", "Aisne"),
    ("03", "Allier"),
    ("04", "Alpes-de-Haute-Provence"),
    ("05", "Hautes-Alpes"),
    ("06", "Alpes-Maritimes"),
    ("07", "Ardèche"),
    ("08", "Ardennes"),
    ("09", "Ariège"),
    ("10", "Aube"),
    ("11", "Aude"),
    ("12", "Aveyron"),
    ("13", "Bouches-du-Rhône"),
    ("14", "Calvados"),
    ("15", "Cantal"),
    ("16", "Charente"),
    ("17", "Charente-Maritime"),
    ("18", "Cher"),
    ("19", "Corrèze"),
    ("2A", "Corse-du-Sud"),
    ("2B", "Haute-Corse"),
    ("21", "Côte-d'Or"),
    ("22", "Côtes-d'Armor"),
    ("23", "Creuse"),
    ("24", "Dordogne"),
    ("25", "Doubs"),
    ("26", "Drôme"),
    ("27", "Eure"),
    ("28", "Eure-et-Loir"),
    ("29", "Finistère"),
    ("30", "Gard"),
    ("31", "Haute-Garonne"),
    ("32", "Gers"),
    ("33", "Gironde"),
    ("34", "Hérault"),
    ("35", "Ille-et-Vilaine"),
    ("36", "Indre"),
    ("37", "Indre-et-Loire"),
    ("38", "Isère"),
    ("39", "Jura"),
    ("40", "Landes"),
    ("41", "Loir-et-Cher"),
    ("42", "Loire"),
    ("43", "Haute-Loire"),
    ("44", "Loire-Atlantique"),
    ("45", "Loiret"),
    ("46", "Lot"),
    ("47", "Lot-et-Garonne"),
    ("48", "Lozère"),
    ("49", "Maine-et-Loire"),
    ("50", "Manche"),
    ("51", "Marne"),
    ("52", "Haute-Marne"),
    ("53", "Mayenne"),
    ("54", "Meurthe-et-Moselle"),
    ("55", "Meuse"),
    ("56", "Morbihan"),
    ("57", "Moselle"),
    ("58", "Nièvre"),
    ("59", "Nord"),
    ("60", "Oise"),
    ("61", "Orne"),
    ("62", "Pas-de-Calais"),
    ("63", "Puy-de-Dôme"),
    ("64", "Pyrénées-Atlantiques"),
    ("65", "Hautes-Pyrénées"),
    ("66", "Pyrénées-Orientales"),
    ("67", "Bas-Rhin"),
    ("68", "Haut-Rhin"),
    ("69", "Rhône"),
    ("70", "Haute-Saône"),
    ("71", "Saône-et-Loire"),
    ("72", "Sarthe"),
    ("73", "Savoie"),
    ("74", "Haute-Savoie"),
    ("75", "Paris"),
    ("76", "Seine-Maritime"),
    ("77", "Seine-et-Marne"),
    ("78", "Yvelines"),
    ("79", "Deux-Sèvres"),
    ("80", "Somme"),
    ("81", "Tarn"),
    ("82", "Tarn-et-Garonne"),
    ("83", "Var"),
    ("84", "Vaucluse"),
    ("85", "Vendée"),
    ("86", "Vienne"),
    ("87", "Haute-Vienne"),
    ("88", "Vosges"),
    ("89", "Yonne"),
    ("90", "Territoire de Belfort"),
    ("91", "Essonne"),
    ("92", "Hauts-de-Seine"),
    ("93", "Seine-Saint-Denis"),
    ("94", "Val-de-Marne"),
    ("95", "Val-d'Oise"),
    ("971", "Guadeloupe"),
    ("972", "Martinique"),
    ("973", "Guyane"),
    ("974", "La Réunion"),
    ("975", "Saint-Pierre-et-Miquelon"),
    ("976", "Mayotte"),
    ("977", "Saint-Barthélémy"),
    ("978", "Saint-Martin"),
    ("986", "Wallis-et-Futuna"),
    ("987", "Polynésie française"),
    ("988", "Nouvelle-Calédonie"),
)

REGIONS_CHOICES = (
    ("FR-ALL", "Toute la France"),
    ("FR-ARA", "Auvergne-Rhône-Alpes"),
    ("FR-BFC", "Bourgogne-Franche-Comté"),
    ("FR-BRE", "Bretagne"),
    ("FR-CVL", "Centre-Val de Loire"),
    ("FR-COR", "Corse"),
    ("FR-GES", "Grand Est"),
    ("FR-HDF", "Hauts-de-France"),
    ("FR-IDF", "Île-de-France"),
    ("FR-NOR", "Normandie"),
    ("FR-NAQ", "Nouvelle-Aquitaine"),
    ("FR-OCC", "Occitanie"),
    ("FR-PDL", "Pays de la Loire"),
    ("FR-PAC", "Provence-Alpes-Côte d'Azur"),
    ("FR-GUA", "Guadeloupe"),
    ("FR-GUF", "Guyane"),
    ("FR-MTQ", "Martinique"),
    ("FR-LRE", "Réunion"),
    ("FR-MAY", "Mayotte"),
    ("other", "Autre - précisez"),
)

WORKFORCE_CHOICES = (
    (11001, "0"),
    (1, _("1 à 2 salariés")),
    (3, _("3 à 5 salariés")),
    (6, _("6 à 9 salariés")),
    (10, _("10 à 19 salariés")),
    (20, _("20 à 49 salariés")),
    (50, _("50 à 99 salariés")),
    (100, _("100 à 199 salariés")),
    (200, _("200 à 499 salariés")),
    (500, _("500 à 999 salariés")),
    (1000, _("1000 à 1999 salariés")),
    (2000, _("2000 à 4999 salariés")),
    (5000, _("5000 salariés")),
    (5001, _("5000 et plus salariés")),
    (10001, _("inconnu")),
)

TURNOVER_CHOICES = (
    (100, "0 - 100 K€"),
    (101, "100 - 250 K€"),
    (251, "250 - 500 K€"),
    (501, "500 - 1 M€"),
    (1001, "1 M€ - 2.5 M€"),
    (2501, "2.5 M€ - 5 M€"),
    (5001, "5 M€ - 10 M€"),
    (10001, "Supérieur à 10 M€"),
    (20001, "Autre - précisez"),
)

CATEGORY_CHOICES = (
    ("enterprise", _("Entreprise")),
    ("event", _("Événement")),
    ("non_profit_organization", _("Association")),
    ("school", _("École")),
    ("public_institution", _("Collectivité locale")),
)

SERVICE_CHOICES = (
    ("comptability", _("Comptabilité")),
    ("administrative", _("Aministratif")),
    ("marketing_communication", _("Marketing/Communication")),
    ("production", _("Exploitation/Production")),
    ("hr", _("Ressources Humaines")),
    ("sells", _("Ventes")),
    ("finances", _("Finances")),
    ("juridic", _("Juridique")),
    ("digital", _("Informatique/Digital")),
    ("engineer", _("Ingénieurie")),
    ("international", _("International")),
)

CIVILITY_CHOICES = (
    ("woman", _("Femme")),
    ("man", _("Homme")),
    ("non-binary", _("Non-binaire")),
    ("prefer-not-to-say", _("Je ne souhaite pas répondre")),
    ("other-gender-identity", _("Autre identité de genre")),
)

SCAN_ROLE_CHOICE = (("drh", _("Directeur")), ("manage", _("Manager")), ("recruit", _("Recruteur")), ("others", _("Autres")))

TYPE_CHOICES = (
    ("contracts", _("Présents contrats (CDD/CDI)")),
    ("interns", _("Présents alternants/stagiaires (f/h/nb)")),
    ("hired_contracts", _("Recrutements contrats (CDD/CDI)")),
    ("hired_interns", _("Recrutements alternants/stagiaires (f/h/nb)")),
)

INDICATOR_LABELS = {
    "contracts": _(
        "Répartition des origines ethniques perçues des personnes en CDD/CDI"
    ),
    "interns": _(
        "Répartition des origines ethniques perçues des personnes en stage/alternance"
    ),
    "hired_contracts": _(
        "Répartition des origines ethniques perçues des personnes recrutées en CDD/CDI dans les 12 derniers mois"
    ),
    "hired_interns": _(
        "Répartition des origines ethniques perçues des personnes recrutées en stage/alternance dans les 12 derniers mois"
    ),
}

COLLABORATOR_STATISTICS_STATUSES = {
    "nodata": _("Données non-collectées"),
    "processing": _("En cours de traitement"),
    "finished": _("Terminé"),
}

WRONG_CSV = _("La structure du fichier CSV n'est pas bonne.")
TOO_MANY_COLLABORATORS = f"Il y a trop de collaborateurs dans votre fichier CSV. Il doit être inférieur à 2x l'effectif indiqué dans l'évaluation."

SUMMARY_TYPE = {
    "contracts": _(
        "Les données doivent correspondre aux collaborateurs (f/h/nb) en contrat (CDD/CDI) depuis plus d'un an."
    ),
    "interns": _(
        "Les données doivent correspondre aux collaborateurs (f/h/nb) en contrat de stage ou d'alternance depuis plus d'un an."
    ),
    "hired_contracts": _(
        "Les données doivent correspondre aux collaborateurs (f/h/nb) en contrat (CDD/CDI) depuis plus d'un an."
    ),
    "hired_interns": _(
        "Les données doivent correspondre aux collaborateurs (f/h/nb) en contrat de stage ou d'alternance depuis moins d'un an."
    ),
}

AGE_CHOICES = (
    ("under_25", _("Moins de 25 ans")),
    ("25_39", _("Entre 25 et 39 ans")),
    ("40_54", _("Entre 40 et 54 ans")),
    ("more_55", _("Plus de 55 ans")),
)

POSITION_CHOICES = (
    ("agent", _("Agent de maîtrise")),
    ("technical", _("Technicien.ne")),
    ("associate", _("Associé.e")),
    ("executive", _("Cadre")),
    ("employee", _("Employé.e")),
    ("other", _("Autre")),
)

# ISO 639-1 (https://fr.wikipedia.org/wiki/Liste_des_codes_ISO_639-1)
LANGUAGE_CHOICES = settings.LANGUAGES

# structure creation
BOOLEANS_ELEMENTS = (
    (
        "lgbt_allowed",
        _(
            "Je déclare que l'orientation sexuelle ou identité de genre est culturellement reconnue et/ou autorisée par la loi dans mon pays"
        ),
    ),
    (
        "ethnicity_allowed",
        _(
            "Je déclare que la collecte et le traitement de données statistiques par ethnie sont autorisés par la loi de mon pays"
        ),
    ),
)

# ISO 4217 (https://fr.wikipedia.org/wiki/ISO_4217)
EURO_CODE = "EUR"
DOLLARD_CODE = "USD"

CURRENCY_CHOICES = (
    (EURO_CODE, "€"),
    (DOLLARD_CODE, "$"),
)

CAMPUS_CHOICE = (
    ("campus_student", _("Etudiant.e")),
    ("campus_teacher__no_cadre", _("Collaborateur.trice - enseignant.e - non cadre")),
    ("campus_teacher__cadre", _("Collaborateur.trice - enseignant.e - cadre")),
    (
        "campus_collaborator__no_cadre",
        _("Collaborateur.trice - administratif - non cadre"),
    ),
    ("campus_collaborator__cadre", _("Collaborateur.trice - administratif - cadre")),
)

TARGET_CHOICE = (
    ("collaborator", _("Collaborateur")),
    ("student", _("Etudiant")),
)

KEYWORDS_CHOICES = (
    ("accessibility", _("Accessibilité")),
    ("purchases", _("Achats")),
    ("caregivers", _("Aidants")),
    ("cognitive-biases", _("Biais Cognitifs")),
    ("gender-equality-index", _("Index égalité")),
    ("young-people", _("Jeunes")),
    ("label-and-certification", _("Label et certification")),
    ("chronic-condition", _("Maladie chronique")),
    ("neurodiversity", _("Neurodiversité")),
    ("parenthood", _("Parentalité")),
    ("mental-health", _("Santé mentale")),
    ("older-people", _("Seniors")),
)

ACTION_STATUS = (
    ("reflection", _("Action en réflexion")),
    ("planned", _("Action planifiée")),
    ("in_progress", _("Action en cours")),
    ("operation", _("Action pilote")),
    ("deployed", _("Action déployée")),
)

EVALUATION_STATUS = [
    "not_started",
    "in_progress",
    "validate_by_user",
    "validate_by_admin",
]

UNIT_CHOICE = (("value", _("Valeur")), ("percent", _("Pourcentage")))

ORGANIZATION_TYPE_CHOICES = (
    ("community", _("Collectivité")),
    ("association", _("Association")),
    ("sme", _("PME")),
    ("midcaps", _("ETI")),
    ("large-company", _("Grande entreprise")),
    ("school", _("École")),
)

ADP_FILTERS = {
    "age": _("Age"),
    "gender": _("Genre"),
    "global": _("Global"),
    "classification": _("Classification"),
    "contract": _("Contrat"),
    "business_unit": _("Pôle"),
    "less_26": _("- de 26 ans"),
    "26_39": _("26 à 39 ans"),
    "40_54": _("40 à 54 ans"),
    "from_55": "55 ans et +",
    "F": _("Femmes"),
    "H": _("Hommes"),
    "M": _("Hommes"),
    "NA": _("Non-binaires"),
    "seniority": _("Ancienneté"),
    "job": _("Poste"),
    "department": _("Département"),
    "citizenship": _("Nationalité"),
}

MONTHS = [
    _("Janvier"),
    _("Février"),
    _("Mars"),
    _("Avril"),
    _("Mai"),
    _("Juin"),
    _("Juillet"),
    _("Août"),
    _("Septembre"),
    _("Octobre"),
    _("Novembre"),
    _("Décembre"),
]
