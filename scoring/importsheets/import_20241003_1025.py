import csv
import json
import logging
from collections import defaultdict
from operator import attrgetter

from django.apps import apps
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings


def check(id, row, column_indexes):
    return id in column_indexes and len(row[column_indexes[id]])


logger = logging.getLogger(__name__)
category_slugs = {
    "Genre": "gender",
    "Handicap": "disability",
    "Origines": "cultural_diversity",
    "Générations": "generational_diversity",
    "LGBTQIA+": "lgbt",
    "Transversal": "all",
    "Notions générales": "general_concept",
    "Communication": "communication",
    "Engagement professionnel": "professional_engagement",
    "Pratique professionnelle": "professional_practice",
    "Biais cognitifs": "cognitive_biases",
    "Bonus - Attitude": "bonus_posture",
    "CSRD": "csrd",
}

autofail = False
autopass = False


def delete_if_consent(the_list, label, attrs):
    """
    Delete objects in the database only with consent of the dev.
    Input to continue :
        - y : yes
        - n : no
        - a : autofail. Will answer yes to every delete case and fail the script at the end
              (Useful if you want to see everything at once)
        - p : autopass. Will answer yes to every delete case
    @param the_list: List or QuerySet of objects to delete
    @param label: Label to designate objects
    @param attrs: attributes of each object to display in the print
    """
    global autofail, autopass
    if len(the_list) > 0 and settings.ENVIRONMENT_NAME == "Developement":
        print(
            f"\n\u001b[31m/!\ WARNING : These {label} would be deleted if you continue.\u001b[0m"
        )
        for elem in the_list:
            result = {}
            for attr in attrs:
                result[attr] = attrgetter(attr)(elem)
            print(result)
        print("\u001b[33mWould you like to continue (y/n/a/p) ?\u001b[0m")
        if not autopass:
            answer = input("").split(" ")[0].lower()
            autofail = answer == "a"
            autopass = autofail or answer == "p"
            if answer != "y" and not autopass:
                raise ValueError(f"Import aborted because of unwanted {label} deletion")
        print("\u001b[32mPASSED\u001b[0m")
    for elem in the_list:
        elem.delete()


def clean_database(apps):
    Category = apps.get_model("scoring", "Category")
    SubCategory = apps.get_model("scoring", "SubCategory")
    Question = apps.get_model("scoring", "Question")

    before = defaultdict(int)
    # Starting stats
    for model in apps.get_models():
        name = model.__name__
        before[name] = model.objects.all().count()

    questions_to_delete = []
    for question in Question.objects.all():
        if question.sheets.count() == 0:
            questions_to_delete.append(question)
    delete_if_consent(questions_to_delete, "questions", ["google_sheets_id", "label"])
    subcategory_to_delete = []
    for subcategory in SubCategory.objects.all():
        if subcategory.questions.count() == 0:
            subcategory_to_delete.append(subcategory)
    delete_if_consent(subcategory_to_delete, "subcategories", ["category.name", "name"])
    category_to_delete = []
    for category in Category.objects.all():
        if category.subcategories.count() == 0:
            category_to_delete.append(category)

    delete_if_consent(category_to_delete, "categories", ["name"])

    # Ending stats
    for model in apps.get_models():
        name = model.__name__
        count = model.objects.all().count()
        diff = count - before[name]
        if diff == 0:
            diff = ""
        else:
            sign = "+" if diff > 0 else ""
            diff = f"({sign}{diff})"
        print(f"{name} rows: {count} {diff}")


def import_questions(apps, file, type, sheet_name=None):
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    Category = apps.get_model("scoring", "Category")
    SubCategory = apps.get_model("scoring", "SubCategory")
    Question = apps.get_model("scoring", "Question")
    QuestionSheet = apps.get_model("scoring", "QuestionSheet")
    QuestionTag = apps.get_model("scoring", "QuestionTag")
    Choice = apps.get_model("scoring", "Choice")
    Comment = apps.get_model("scoring", "Comment")
    SubQuestion = apps.get_model("scoring", "SubQuestion")
    SubquestionChoice = apps.get_model("scoring", "SubquestionChoice")
    Indicator = apps.get_model("scoring", "indicator")
    IndicatorType = apps.get_model("scoring", "IndicatorType")
    Skill = apps.get_model("scoring", "Skill")

    if not sheet_name:
        sheet_name = type

    column_indexes = {}
    MANDATORY_COLUMNS = [
        "QUESTION_ID",
        "CATEGORY",
        "SUBCATEGORY",
        "QUESTION_LABEL",
        "QUESTION_TYPE",
    ]
    LANGUAGES = settings.LANGUAGES_GOOGLE_SHEETS
    with open(file, newline="") as csvfile:
        rows = list(csv.reader(csvfile, delimiter=","))
        if rows[0][0] != type:
            raise ValueError(
                "Wrong CSV. Expected a '"
                + type
                + "' questions sheet but got '"
                + rows[0][0]
                + "'"
            )
        for index, column_name in enumerate(rows[1]):
            if column_name:
                column_indexes[column_name] = index
        for column in MANDATORY_COLUMNS:
            if column not in column_indexes:
                raise ValueError("La colonne " + column + " manque à l'appel")
        sheet_type = QuestionSheetType.objects.filter(slug=type).first()
        if not sheet_type:
            raise ValueError("Le questionnaire " + type + " n'existe pas")
        last_sheet = QuestionSheet.objects.filter(type=sheet_type).last()
        version = 0.1
        if last_sheet:
            version += last_sheet.version
        year = timezone.now().year
        questionnaire = QuestionSheet.objects.create(
            type=sheet_type, version=version, slug=sheet_name, year=year
        )
        logger.debug(questionnaire.type, questionnaire.version)
        logger.debug(f"{questionnaire}")

        for index, row in enumerate(rows[2:]):
            if len(row) == 0 or row[column_indexes["QUESTION_ID"]] == "":
                continue
            google_sheets_id = (
                int(row[column_indexes["QUESTION_ID"]])
                if row[column_indexes["QUESTION_ID"]]
                else None
            )

            category_name = row[column_indexes["CATEGORY"]].strip()
            category = Category.objects.filter(name__iexact=category_name).first()
            if not category:
                raise ValueError(
                    f"Missing category {category_name} for question {google_sheets_id}"
                )
            subcategory_name = row[column_indexes["SUBCATEGORY"]].strip()
            subcategory = SubCategory.objects.filter(
                name__iexact=subcategory_name
            ).first()
            if not subcategory:
                raise ValueError(f"Missing subcategory {subcategory_name}")
            if row[column_indexes["WEIGHT"]] == "":
                raise ValueError(f"Missing subcategory {google_sheets_id}")
            weight_index = float(row[column_indexes["WEIGHT"]].replace(",", "."))
            if (
                not questionnaire.google_sheet
                or questionnaire.google_sheet[index] != row
            ):
                logger.debug("--adding")
                labels = {}
                for language in LANGUAGES.values():
                    if check(f"QUESTION_LABEL", row, column_indexes):
                        labels["label_" + language] = row[
                            column_indexes["QUESTION_LABEL"]
                        ].strip()
                    else:
                        raise ValueError(
                            f"QUESTION_LABEL missing for Question {google_sheets_id}"
                        )

                for sheet_lang, django_lang in LANGUAGES.items():
                    if check(f"QUESTION_LABEL_{sheet_lang}", row, column_indexes):
                        labels["label_" + django_lang] = row[
                            column_indexes[f"QUESTION_LABEL_{sheet_lang}"]
                        ].strip()

                question, _c = Question.objects.get_or_create(
                    google_sheets_id=google_sheets_id,
                    defaults={
                        **labels,
                        "weight_index": weight_index,
                        "subcategory": subcategory,
                        "category": category,
                    },
                )
            else:
                logger.debug("--updating")
                question = Question.objects.filter(
                    google_sheets_id=google_sheets_id
                ).first()

            if question:
                if "MANDATORY_TAGS" in column_indexes:
                    tags = [
                        c.strip()
                        for c in row[column_indexes["MANDATORY_TAGS"]].split(";")
                    ]
                    question.mandatory_tags.clear()  # if tag removed. Only relation removed, not object
                    for tag in tags:
                        if len(tag) > 1:
                            t, _ = QuestionTag.objects.get_or_create(name=tag)
                            if t not in question.mandatory_tags.all():
                                question.mandatory_tags.add(t)

                if "FORBIDDEN_TAGS" in column_indexes:
                    tags = [
                        c.strip()
                        for c in row[column_indexes["FORBIDDEN_TAGS"]].split(";")
                    ]
                    question.forbidden_tags.clear()  # if tag removed. Only relation removed, not object
                    for tag in tags:
                        if len(tag) > 1:
                            t, _ = QuestionTag.objects.get_or_create(name=tag)
                            if t not in question.forbidden_tags.all():
                                question.forbidden_tags.add(t)

                if "TARGET" in column_indexes:
                    question.target = row[column_indexes["TARGET"]].strip().lower()

                if (
                    "NOT_APPLICABLE" in column_indexes
                    and row[column_indexes["NOT_APPLICABLE"]] == "1"
                ):
                    question.display_not_applicable = True

                if (
                    "NOT_FOLLOWED" in column_indexes
                    and row[column_indexes["NOT_FOLLOWED"]] == "1"
                ):
                    question.is_indicator = True

                if (
                    "CUSTOM_LABEL" in column_indexes
                    and row[column_indexes["CUSTOM_LABEL"]] == "1"
                ):
                    question.display_custom_question_label = True

                for language in LANGUAGES.values():
                    if check(f"QUESTION_LABEL", row, column_indexes):
                        setattr(
                            question,
                            "label_" + language,
                            row[column_indexes["QUESTION_LABEL"]].strip(),
                        )
                    else:
                        raise ValueError(
                            f"QUESTION_LABEL missing for Question {google_sheets_id}"
                        )

                for sheet_lang, django_lang in LANGUAGES.items():
                    if check(f"QUESTION_LABEL_{sheet_lang}", row, column_indexes):
                        setattr(
                            question,
                            "label_" + django_lang,
                            row[column_indexes[f"QUESTION_LABEL_{sheet_lang}"]].strip(),
                        )

                question.weight_index = weight_index
                question.order_num = index
                # TODO question.ui_type = ?
                question.type = row[column_indexes["QUESTION_TYPE"]]
                if question.type == "text":
                    question.ui_type = "text"
                elif question.type == "qcm":
                    question.ui_type = "select"
                elif question.type == "subquestions":
                    question.ui_type = "sq_select"
                elif question.type == "subquestions_dual":
                    question.ui_type = "sq_dual"
                elif "subquestions_qcm" in question.type:
                    question.ui_type = "sq_qcm"
                else:
                    question.ui_type = "slider"
                question.sheets.add(questionnaire)
                if check("EMPTY_ANSWER_MARK", row, column_indexes):
                    question.none_answer_value = int(
                        row[column_indexes["EMPTY_ANSWER_MARK"]]
                    )

                if check("THEME", row, column_indexes):
                    question.theme = row[column_indexes["THEME"]]

                columns = {
                    "INDICATORS": {"default": False, "field": "indicators"},
                    "RECOMMANDATION": {"default": False, "field": "recommandation"},
                    "HELP_TEXT": {"default": False, "field": "help_text"},
                }

                for language in LANGUAGES.values():
                    for column, content in columns.items():
                        if check(column, row, column_indexes):
                            columns[column]["default"] = True
                            setattr(
                                question,
                                f"{content['field']}_" + language,
                                row[column_indexes[column]].strip(),
                            )

                for sheet_lang, django_lang in LANGUAGES.items():
                    for column, content in columns.items():
                        if check(f"{column}_{sheet_lang}", row, column_indexes):
                            if not content["default"]:
                                raise ValueError(
                                    f"No default lang for column {column} (Question : {question.google_sheets_id})"
                                )
                            setattr(
                                question,
                                f"{content['field']}_" + django_lang,
                                row[column_indexes[f"{column}_{sheet_lang}"]].strip(),
                            )

                if check("PRIORITY_ORDER", row, column_indexes):
                    question.priority_order = int(row[column_indexes["PRIORITY_ORDER"]])
                if check("AGGREGATE_MODE", row, column_indexes):
                    question.aggregate_mode = (
                        row[column_indexes["AGGREGATE_MODE"]].lower().strip()
                    )
                if check("ORDER_STAT_SUBCATEGORY", row, column_indexes):
                    question.order_stat_subcategory = int(
                        row[column_indexes["ORDER_STAT_SUBCATEGORY"]]
                    )
                if check("ASK_MORE_BOOLEAN", row, column_indexes):
                    question.ask_detail = bool(
                        int(row[column_indexes["ASK_MORE_BOOLEAN"]])
                    )
                if check("SKILLS_SCAN", row, column_indexes):
                    skills = Skill.objects.all()
                    skills_list = [
                        c.strip() for c in row[column_indexes["SKILLS_SCAN"]].split(";")
                    ]
                    for skill_name in skills_list:
                        if skills.get(name=skill_name) is not None:
                            question.skills.add(skills.get(name=skill_name))
                        else:
                            raise ValueError(
                                f"The skill {skill_name} doesn't exist, for question {google_sheets_id})"
                            )
                    if check("SKILLS_WEIGHT", row, column_indexes):
                        skills_weight_list = [
                            c.strip()
                            for c in row[column_indexes["SKILLS_WEIGHT"]].split(";")
                        ]
                        if len(skills_weight_list) != len(skills_list):
                            raise ValueError(
                                f"There isn't the same numbers of skills and skills_weight for question {google_sheets_id})"
                            )
                        if question.skills_weight is None:
                            question.skills_weight = {}
                        for i, skill_weight in enumerate(skills_weight_list):
                            skill_name = skills_list[i]
                            skill_slug = skills.get(name=skill_name).slug
                            question.skills_weight[skill_slug] = float(
                                skill_weight.replace(",", ".")
                            )
                        # Faire l'ajout des skils_weight aux questions ici
                if check("FEEDBACK", row, column_indexes):
                    question.feedback = row[column_indexes["FEEDBACK"]]
                if check("SIBLING_QUESTION", row, column_indexes):
                    sibling_id = int(row[column_indexes["SIBLING_QUESTION"]])
                    if sibling_id:
                        old_question = Question.objects.filter(
                            google_sheets_id=sibling_id
                        ).first()
                        if old_question:
                            question.sibling = old_question
                        else:
                            question.sibling = None
                    else:
                        question.sibling = None
                else:
                    question.sibling = None

                question.save()
                logger.debug("question")
                logger.debug(question.google_sheets_id, question.label)

                question.category = category
                question.subcategory = subcategory
                if check(
                    "PUBLIC_DISPLAY_DEFAULT", row, column_indexes
                ):  # malus comments
                    pb_d_d = row[column_indexes["PUBLIC_DISPLAY_DEFAULT"]].strip()
                    if pb_d_d == "1":
                        question.public_display_default = True
                    else:
                        question.public_display_default = False
                question.save()

                logger.debug("choices")

                answer_choices = {}

                for sheet_lang, django_lang in LANGUAGES.items():
                    if check(f"ANSWER_CHOICES_{sheet_lang}", row, column_indexes):
                        answer_choices[django_lang] = row[
                            column_indexes[f"ANSWER_CHOICES_{sheet_lang}"]
                        ].split(";")

                answer_choices_list = list(answer_choices.values())
                logger.debug(answer_choices_list)
                if len(answer_choices_list) > 0:
                    the_len = len(answer_choices_list[0])
                    if not all(len(l) == the_len for l in answer_choices_list):
                        raise ValueError(
                            f"not all lists have same length! (choices Question {google_sheets_id})"
                        )
                choices = []
                if len(answer_choices_list) > 0:
                    choices = answer_choices[list(answer_choices.keys())[0]]
                    if check("MARK", row, column_indexes):
                        points = [
                            p.strip() for p in row[column_indexes["MARK"]].split(";")
                        ]
                    else:
                        if question.weight_index:
                            raise ValueError(
                                f"La question {question.google_sheets_id} a un poids de {question.weight_index} mais n'a pas de notes ! (colonne {column_indexes['MARK']} vide)"
                            )
                        points = [0] * len(choices)
                    logger.debug(choices)
                    logger.debug(points)
                    for index, choice in enumerate(choices):
                        logger.debug(index)
                        logger.debug(choice)
                        logger.debug(points[index])
                        if points[index] == "":
                            points[index] = 3
                        c, _c = Choice.objects.get_or_create(
                            question=question,
                            order=index + 1,
                            defaults={"value": points[index]},
                        )
                        for language in LANGUAGES.values():
                            setattr(c, "label_" + language, choice.strip())
                            if language in answer_choices:
                                setattr(
                                    c,
                                    "label_" + language,
                                    answer_choices[language][index].strip(),
                                )
                        c.value = points[index]
                        c.save()
                    if len(points) != len(choices):
                        raise ValueError(
                            "There are not the same number of points and choices for question "
                            + str(question.google_sheets_id)
                        )
                choices_count = len(Choice.objects.filter(question=question))
                if len(choices) < choices_count:
                    delete_if_consent(
                        Choice.objects.filter(question=question)[
                            len(choices) : choices_count
                        ],
                        f"choices (Question : {question.google_sheets_id})",
                        attrs=["label_fr"],
                    )
                subquestions = {}
                for sheet_lang, django_lang in LANGUAGES.items():
                    if check(f"SUBQUESTIONS_{sheet_lang}", row, column_indexes):
                        subquestions[django_lang] = row[
                            column_indexes[f"SUBQUESTIONS_{sheet_lang}"]
                        ].split(";")

                subquestions_list = list(subquestions.values())
                logger.debug([f"{len(i)} " for i in subquestions_list])
                if len(subquestions_list) > 0:
                    the_len = len(subquestions_list[0])
                    if not all(len(l) == the_len for l in subquestions_list):
                        raise ValueError(
                            f"not all lists have same length! (subquestions Question {google_sheets_id})"
                        )

                if "subquestions" in row[column_indexes["QUESTION_TYPE"]]:
                    logger.debug("--adding subquestions")
                    sq_order = 1
                    subquestions_obj = SubQuestion.objects.filter(
                        question=question
                    ).order_by("order")
                    first_sq_language = subquestions[list(subquestions.keys())[0]]
                    for index, subquestion in enumerate(first_sq_language):
                        if len(subquestions_obj) >= sq_order:
                            s = subquestions_obj[sq_order - 1]
                            for language in LANGUAGES.values():
                                setattr(s, "label_" + language, subquestion.strip())
                                if language in subquestions:
                                    setattr(
                                        s,
                                        "label_" + language,
                                        subquestions[language][index].strip(),
                                    )
                            s.order = sq_order
                            s.ui_type = row[column_indexes["SUBQUESTIONS_TYPE"]]
                            s.save()
                        else:
                            labels = {}
                            for language in LANGUAGES.values():
                                labels["label_" + language] = subquestion.strip()
                                if language in subquestions:
                                    labels["label_" + language] = subquestions[
                                        language
                                    ][index].strip()
                            s = SubQuestion.objects.create(
                                question=question,
                                order=sq_order,
                                **labels,
                                ui_type=row[column_indexes["SUBQUESTIONS_TYPE"]],
                            )

                        subquestions_choices = {}
                        for sheet_lang, django_lang in LANGUAGES.items():
                            if check(
                                f"SUBQUESTIONS_CHOICES_{sheet_lang}",
                                row,
                                column_indexes,
                            ):
                                subquestions_choices[django_lang] = row[
                                    column_indexes[f"SUBQUESTIONS_CHOICES_{sheet_lang}"]
                                ].split(";")

                        subquestions_choices_list = list(subquestions_choices.values())
                        if len(subquestions_choices_list) > 0:
                            the_len = len(subquestions_choices_list[0])
                            if not all(
                                len(l) == the_len for l in subquestions_choices_list
                            ):
                                raise ValueError(
                                    f"not all lists have same length! (sub_choices Question {google_sheets_id}, Subquestion {s.label_fr})"
                                )
                        sq_order += 1
                        if len(subquestions_choices) > 0:
                            sub_choices = subquestions_choices[
                                list(subquestions_choices.keys())[0]
                            ]
                            sub_choices_values = [
                                c.strip()
                                for c in row[
                                    column_indexes["SUBQUESTIONS_POINTS"]
                                ].split(";")
                            ]
                            if len(sub_choices_values) == 0:
                                sub_choices_values = [-1] * len(sub_choices)
                            elif len(sub_choices_values) != len(sub_choices):
                                raise ValueError(
                                    f"Question {question.google_sheets_id}: Number of subquestion points is different of number of subquestion choices",
                                )
                            order = 0
                            for i in range(
                                min(len(sub_choices), len(sub_choices_values))
                            ):
                                if sub_choices_values[i] == "":
                                    sub_choices_values[i] = -1
                                sub_choice = sub_choices[i]
                                labels = {}
                                for language in LANGUAGES.values():
                                    labels["label_" + language] = sub_choice.strip()
                                    if language in subquestions_choices:
                                        labels[
                                            "label_" + language
                                        ] = subquestions_choices[language][i].strip()

                                SubquestionChoice.objects.update_or_create(
                                    subquestion=s,
                                    order=order,
                                    defaults={"value": sub_choices_values[i], **labels},
                                )
                                order += 1
                        else:
                            assert s.choices.count() == 0, (
                                "Question %i no longer have choices" % question.id
                            )
                        choices_count = len(
                            SubquestionChoice.objects.filter(subquestion=s)
                        )
                        if (
                            len(subquestions_choices_list) > 0
                            and len(subquestions_choices_list[0]) < choices_count
                        ):
                            delete_if_consent(
                                SubquestionChoice.objects.filter(subquestion=s)[
                                    len(subquestions_choices_list[0]) : choices_count
                                ],
                                f"sub_choices (Question : {question.google_sheets_id}, Subquestion : {s.label_fr})",
                                attrs=["label_fr"],
                            )
                    if len(first_sq_language) < len(subquestions_obj):
                        delete_if_consent(
                            subquestions_obj[
                                len(first_sq_language) : len(subquestions_obj)
                            ],
                            f"subquestions (Question : {question.google_sheets_id})",
                            attrs=["label_fr"],
                        )

                logger.debug("comments")
                # if strengths comment
                if check("STRENGTHS", row, column_indexes) or check(
                    "STRENGTHS_FR", row, column_indexes
                ):
                    comment, _c = Comment.objects.get_or_create(
                        question=question, is_good=True
                    )

                    for language in LANGUAGES.values():
                        if check(f"STRENGTHS", row, column_indexes):
                            setattr(
                                comment,
                                "description_" + language,
                                row[column_indexes["STRENGTHS"]].strip(),
                            )

                    for sheet_lang, django_lang in LANGUAGES.items():
                        if check(f"STRENGTHS_{sheet_lang}", row, column_indexes):
                            setattr(
                                comment,
                                "description_" + django_lang,
                                row[column_indexes[f"STRENGTHS_{sheet_lang}"]].strip(),
                            )

                    comment.save()
                else:
                    comment = Comment.objects.filter(question=question, is_good=True)
                    if comment.count() > 0:
                        delete_if_consent(
                            comment,
                            f"(+) comments (Question {question.google_sheets_id})",
                            ["description"],
                        )

                # If weaknesses comment
                if check("WEAKNESSES", row, column_indexes) or check(
                    "WEAKNESSES_FR", row, column_indexes
                ):
                    comment, _c = Comment.objects.get_or_create(
                        question=question, is_good=False
                    )

                    for language in LANGUAGES.values():
                        if check(f"WEAKNESSES", row, column_indexes):
                            setattr(
                                comment,
                                "description_" + language,
                                row[column_indexes["WEAKNESSES"]].strip(),
                            )

                    for sheet_lang, django_lang in LANGUAGES.items():
                        if check(f"WEAKNESSES_{sheet_lang}", row, column_indexes):
                            setattr(
                                comment,
                                "description_" + django_lang,
                                row[column_indexes[f"WEAKNESSES_{sheet_lang}"]].strip(),
                            )
                    comment.save()
                else:
                    comment = Comment.objects.filter(question=question, is_good=False)
                    if comment.count() > 0:
                        delete_if_consent(
                            comment,
                            f"(-) comments (Question {question.google_sheets_id})",
                            ["description"],
                        )
                # if indicator info given
                if check(f"INDICATORS_INFOS", row, column_indexes):
                    question_indicator, _i = Indicator.objects.get_or_create(
                        question=question
                    )
                    elemindicator = json.loads(row[column_indexes["INDICATORS_INFOS"]])
                    indicatorparamlist = ""

                    question_indicator.displaying_params = elemindicator[
                        "display_params"
                    ]

                    for param in elemindicator["params"]:
                        indicatorparamlist = (
                            indicatorparamlist + str(param).replace("'", '"') + "\n"
                        )
                    question_indicator.params = indicatorparamlist

                    question_indicator.type = IndicatorType.objects.filter(
                        slug=elemindicator["indicator_type"]
                    ).first()
                    question_indicator.title_fr = elemindicator.get("title_fr")
                    question_indicator.title_en = elemindicator.get("title_en")
                    question_indicator.title_es = elemindicator.get("title_es")
                    question_indicator.selector_labels_fr = elemindicator.get(
                        "selector_title_fr"
                    )
                    question_indicator.selector_labels_en = elemindicator.get(
                        "selector_title_en"
                    )
                    question_indicator.selector_labels_es = elemindicator.get(
                        "selector_title_es"
                    )
                    question_indicator.colors = elemindicator["colors"]
                    question_indicator.selector = elemindicator["selector"]
                    question_indicator.selector_link = elemindicator["selector_link"]
                    question_indicator.save()

        questionnaire.google_sheet = rows.__str__()
        questionnaire.save()
        if autofail:
            raise ValueError("AUTOFAIL")
