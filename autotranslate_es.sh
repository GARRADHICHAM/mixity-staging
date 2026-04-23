#!/bin/bash
#
# Procedure:
# 1. Créer une nouvelle migration d'import par type de formulaire (il faudra aussi un nouveau script d'import qui tient compte de l'espagnol)
# 2. Ajouter les fichiers correspondant à chaque type de formulaire (vous pouvez copier le dernier s'il n'a pas changé, mais mettez à jour le nom)
# 3. Mettre à jour les lignes ci-dessous pour chaque fichier (il faut 1 appel par colonne à traduire)
# 4. Commiter les fichiers
# 5. Appeler `make I18N` pour actualiser les traductions des pofiles

# Mixity international
# python autotranslate_csv_es.py mixity/static/csv/international/questionnaire_international_20211025_1035.csv QUESTION_LABEL QUESTION_LABEL_ES
# python autotranslate_csv_es.py mixity/static/csv/international/questionnaire_international_20211025_1035.csv HELP_TEXT HELP_TEXT_ES
# python autotranslate_csv_es.py mixity/static/csv/international/questionnaire_international_20211025_1035.csv STRENGTHS_FR STRENGTHS_ES
# python autotranslate_csv_es.py mixity/static/csv/international/questionnaire_international_20211025_1035.csv WEAKNESSES_FR WEAKNESSES_ES

# Mixity startup/PME
# python autotranslate_csv_es.py mixity/static/csv/startup2021/questionnaire_start2021_20211203_1205.csv QUESTION_LABEL QUESTION_LABEL_ES
# python autotranslate_csv_es.py mixity/static/csv/startup2021/questionnaire_start2021_20211203_1205.csv HELP_TEXT HELP_TEXT_ES
# python autotranslate_csv_es.py mixity/static/csv/startup2021/questionnaire_start2021_20211203_1205.csv STRENGTHS_FR STRENGTHS_ES
# python autotranslate_csv_es.py mixity/static/csv/startup2021/questionnaire_start2021_20211203_1205.csv WEAKNESSES_FR WEAKNESSES_ES

# Mixity start/flash
python autotranslate_csv_es.py mixity/static/csv/startflash/questionnaire_startflash_20220131_1642.csv QUESTION_LABEL QUESTION_LABEL_ES
python autotranslate_csv_es.py mixity/static/csv/startflash/questionnaire_startflash_20220131_1642.csv HELP_TEXT HELP_TEXT_ES
python autotranslate_csv_es.py mixity/static/csv/startflash/questionnaire_startflash_20220131_1642.csv STRENGTHS_FR STRENGTHS_ES
python autotranslate_csv_es.py mixity/static/csv/startflash/questionnaire_startflash_20220131_1642.csv WEAKNESSES_FR WEAKNESSES_ES
python autotranslate_csv_es.py mixity/static/csv/startflash/questionnaire_startflash_20220131_1642.csv RECOMMANDATION RECOMMANDATION_ES
python autotranslate_csv_es.py mixity/static/csv/startflash/questionnaire_startflash_20220131_1642.csv INDICATORS INDICATORS_ES

# Mixity society
# python autotranslate_csv_es.py mixity/static/csv/society2021/questionnaire_society2021_20211025_1025.csv QUESTION_LABEL QUESTION_LABEL_ES
# python autotranslate_csv_es.py mixity/static/csv/society2021/questionnaire_society2021_20211025_1025.csv HELP_TEXT HELP_TEXT_ES
# python autotranslate_csv_es.py mixity/static/csv/society2021/questionnaire_society2021_20211025_1025.csv STRENGTHS_FR STRENGTHS_ES
# python autotranslate_csv_es.py mixity/static/csv/society2021/questionnaire_society2021_20211025_1025.csv WEAKNESSES_FR WEAKNESSES_ES

# Mixity Human / collaborateurs360
python autotranslate_csv_es.py mixity/static/csv/collaborateurs360/questionnaire_collaborateurs360_20220131_1642.csv QUESTION_LABEL QUESTION_LABEL_ES
python autotranslate_csv_es.py mixity/static/csv/collaborateurs360/questionnaire_collaborateurs360_20220131_1642.csv HELP_TEXT HELP_TEXT_ES
python autotranslate_csv_es.py mixity/static/csv/collaborateurs360/questionnaire_collaborateurs360_20220131_1642.csv STRENGTHS_FR STRENGTHS_ES
python autotranslate_csv_es.py mixity/static/csv/collaborateurs360/questionnaire_collaborateurs360_20220131_1642.csv WEAKNESSES_FR WEAKNESSES_ES

# PO file
# make I18N
