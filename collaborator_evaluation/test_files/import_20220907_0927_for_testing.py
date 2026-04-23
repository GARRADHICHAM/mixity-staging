# allow category creation for testing purposes only. IT, ZH, ZH-CHT disabled for now (until language tests are updated)
import csv
from collections import defaultdict

from django.apps import apps
from django.utils import timezone
from django.utils.text import slugify


def check(id, row, column_indexes):
    return id in column_indexes and len(row[column_indexes[id]])


category_slugs = {
    "Genre": "gender",
    "Handicap": "disability",
    "Multi-culturel": "cultural_diversity",
    "Multi-générationnel": "generational_diversity",
    "LGBT+": "lgbt",
    "Transversal": "all",
}


def clean_database(apps):
    Category = apps.get_model("scoring", "Category")
    SubCategory = apps.get_model("scoring", "SubCategory")
    Question = apps.get_model("scoring", "Question")

    before = defaultdict(int)
    # Starting stats
    for model in apps.get_models():
        name = model.__name__
        before[name] = model.objects.all().count()

    for question in Question.objects.all():
        if question.sheets.count() == 0:
            question.delete()
    for subcategory in SubCategory.objects.all():
        if subcategory.questions.count() == 0:
            subcategory.delete()
    for category in Category.objects.all():
        if category.subcategories.count() == 0:
            category.delete()

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
            if category:
                category.name = category_name
                category.slug = category_slugs.get(
                    category_name, slugify(category_name)
                )
                category.order = index
                category.save()
            else:
                category = Category.objects.create(
                    name=category_name[0:50],
                    slug=slugify(category_name)[0:50],
                    weight_index=1,
                )

            subcategory_name = row[column_indexes["SUBCATEGORY"]].strip()
            subcategory = SubCategory.objects.filter(
                category=category, name__iexact=subcategory_name
            ).first()
            if subcategory:
                subcategory.name = subcategory_name
                if not subcategory.short_name:
                    subcategory.short_name = subcategory_name[0:14]
                subcategory.order = index
                subcategory.save()
            else:
                subcategory = SubCategory.objects.create(
                    category=category,
                    name=subcategory_name,
                    order=index,
                    slug=slugify(subcategory_name),
                )

            weight_index = float(row[column_indexes["WEIGHT"]].replace(",", "."))
            if (
                not questionnaire.google_sheet
                or questionnaire.google_sheet[index] != row
            ):
                print("--adding")

                label_fr = (
                    label_en
                ) = label_es = label_it = label_zh_hans = label_zh_hant = row[
                    column_indexes["QUESTION_LABEL"]
                ]
                if check("QUESTION_LABEL_EN", row, column_indexes):
                    label_en = row[column_indexes["QUESTION_LABEL_EN"]]
                if check("QUESTION_LABEL_ES", row, column_indexes):
                    label_es = row[column_indexes["QUESTION_LABEL_ES"]]
                if check("QUESTION_LABEL_IT", row, column_indexes):
                    label_it = row[column_indexes["QUESTION_LABEL_IT"]]
                if check("QUESTION_LABEL_ZH", row, column_indexes):
                    label_zh_hans = row[column_indexes["QUESTION_LABEL_ZH"]]
                if check("QUESTION_LABEL_ZH-CHT", row, column_indexes):
                    label_zh_hant = row[column_indexes["QUESTION_LABEL_ZH-CHT"]]
                question, _c = Question.objects.get_or_create(
                    google_sheets_id=google_sheets_id,
                    defaults={
                        "label_fr": label_fr,
                        "label_en": label_en,
                        "label_es": label_es,
                        # "label_it": label_it,
                        # "label_zh_hans": label_zh_hans,
                        # "label_zh_hant": label_zh_hant,
                        "weight_index": weight_index,
                        "subcategory": subcategory,
                    },
                )
            else:
                print("--updating")
                question = Question.objects.filter(
                    google_sheets_id=google_sheets_id
                ).first()

            if question:
                if "MANDATORY_TAGS" in column_indexes:
                    tags = [
                        c.strip()
                        for c in row[column_indexes["MANDATORY_TAGS"]].split(";")
                    ]
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
                    for tag in tags:
                        if len(tag) > 1:
                            t, _ = QuestionTag.objects.get_or_create(name=tag)
                            if t not in question.forbidden_tags.all():
                                question.forbidden_tags.add(t)

                if "TARGET" in column_indexes:
                    question.target = row[column_indexes["TARGET"]].strip().lower()

                label_fr = (
                    label_en
                ) = label_es = label_it = label_zh_hant = label_zh_hans = row[
                    column_indexes["QUESTION_LABEL"]
                ].strip()
                if check("QUESTION_LABEL_EN", row, column_indexes):
                    label_en = row[column_indexes["QUESTION_LABEL_EN"]].strip()
                if check("QUESTION_LABEL_ES", row, column_indexes):
                    label_es = row[column_indexes["QUESTION_LABEL_ES"]].strip()
                if check("QUESTION_LABEL_IT", row, column_indexes):
                    label_it = row[column_indexes["QUESTION_LABEL_IT"]].strip()
                if check("QUESTION_LABEL_ZH", row, column_indexes):
                    label_zh_hans = row[column_indexes["QUESTION_LABEL_ZH"]].strip()
                if check("QUESTION_LABEL_ZH-CHT", row, column_indexes):
                    label_zh_hant = row[column_indexes["QUESTION_LABEL_ZH-CHT"]].strip()

                question.label_fr = label_fr
                question.label_en = label_en
                question.label_es = label_es
                # question.label_it = label_it
                # question.label_zh_hans = label_zh_hans
                # question.label_zh_hant = label_zh_hant
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
                    question.theme_fr = row[column_indexes["THEME"]]
                if check("THEME_EN", row, column_indexes):
                    question.theme_en = row[column_indexes["THEME_EN"]]
                if check("THEME_ES", row, column_indexes):
                    question.theme_es = row[column_indexes["THEME_ES"]]
                # if check("THEME_IT", row, column_indexes):
                #     question.theme_it = row[column_indexes["THEME_IT"]]
                # if check("THEME_ZH", row, column_indexes):
                #     question.theme_zh_hans = row[column_indexes["THEME_ZH"]]
                # if check("THEME_ZH-CHT", row, column_indexes):
                #     question.theme_zh_hant = row[column_indexes["THEME_ZH-CHT"]]
                if check("INDICATORS", row, column_indexes):
                    question.indicators_fr = row[column_indexes["INDICATORS"]]
                if check("INDICATORS_EN", row, column_indexes):
                    question.indicators_en = row[column_indexes["INDICATORS_EN"]]
                if check("INDICATORS_ES", row, column_indexes):
                    question.indicators_es = row[column_indexes["INDICATORS_ES"]]
                # if check("INDICATORS_IT", row, column_indexes):
                #     question.indicators_it = row[column_indexes["INDICATORS_IT"]]
                # if check("INDICATORS_ZH", row, column_indexes):
                #     question.indicators_zh_hans = row[column_indexes["INDICATORS_ZH"]]
                # if check("INDICATORS_ZH-CHT", row, column_indexes):
                #     question.indicators_zh_hant = row[
                #         column_indexes["INDICATORS_ZH-CHT"]
                #     ]
                if check("RECOMMANDATION", row, column_indexes):
                    question.recommandation_fr = row[column_indexes["RECOMMANDATION"]]
                if check("RECOMMANDATION_EN", row, column_indexes):
                    question.recommandation_en = row[
                        column_indexes["RECOMMANDATION_EN"]
                    ]
                if check("RECOMMANDATION_ES", row, column_indexes):
                    question.recommandation_es = row[
                        column_indexes["RECOMMANDATION_ES"]
                    ]
                # if check("RECOMMANDATION_IT", row, column_indexes):
                #     question.recommandation_it = row[
                #         column_indexes["RECOMMANDATION_IT"]
                #     ]
                # if check("RECOMMANDATION_ZH", row, column_indexes):
                #     question.recommandation_zh_hans = row[
                #         column_indexes["RECOMMANDATION_ZH"]
                #     ]
                # if check("RECOMMANDATION_ZH-CHT", row, column_indexes):
                #     question.recommandation_zh_hant = row[
                #         column_indexes["RECOMMANDATION_ZH-CHT"]
                #     ]
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
                question.help_text_en = (
                    question.help_text_es
                ) = (
                    question.help_text_it
                ) = question.help_text_zh_hans = question.help_text_zh_hant = None
                if check("HELP_TEXT", row, column_indexes):
                    question.help_text_fr = row[column_indexes["HELP_TEXT"]]
                if check("HELP_TEXT_EN", row, column_indexes):
                    question.help_text_en = row[column_indexes["HELP_TEXT_EN"]]
                if check("HELP_TEXT_ES", row, column_indexes):
                    question.help_text_es = row[column_indexes["HELP_TEXT_ES"]]
                # if check("HELP_TEXT_IT", row, column_indexes):
                #     question.help_text_it = row[column_indexes["HELP_TEXT_IT"]]
                # if check("HELP_TEXT_ZH", row, column_indexes):
                #     question.help_text_zh_hans = row[column_indexes["HELP_TEXT_ZH"]]
                # if check("HELP_TEXT_ZH-CHT", row, column_indexes):
                #     question.help_text_zh_hant = row[column_indexes["HELP_TEXT_ZH-CHT"]]
                question.save()
                print("question")
                print(question.google_sheets_id, question.label)

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

                print("choices")

                answer_choices = {}
                if check("ANSWER_CHOICES_FR", row, column_indexes):
                    answer_choices["fr"] = row[
                        column_indexes["ANSWER_CHOICES_FR"]
                    ].split(";")
                if check("ANSWER_CHOICES_EN", row, column_indexes):
                    answer_choices["en"] = row[
                        column_indexes["ANSWER_CHOICES_EN"]
                    ].split(";")
                if check("ANSWER_CHOICES_ES", row, column_indexes):
                    answer_choices["es"] = row[
                        column_indexes["ANSWER_CHOICES_ES"]
                    ].split(";")
                # if check("ANSWER_CHOICES_IT", row, column_indexes):
                #     answer_choices["it"] = row[
                #         column_indexes["ANSWER_CHOICES_IT"]
                #     ].split(";")
                # if check("ANSWER_CHOICES_ZH", row, column_indexes):
                #     answer_choices["zh-hans"] = row[
                #         column_indexes["ANSWER_CHOICES_ZH"]
                #     ].split(";")
                # if check("ANSWER_CHOICES_ZH-CHT", row, column_indexes):
                #     answer_choices["zh-hant"] = row[
                #         column_indexes["ANSWER_CHOICES_ZH-CHT"]
                #     ].split(";")

                answer_choices_list = list(answer_choices.values())
                print(answer_choices_list)
                if len(answer_choices_list) > 0:
                    the_len = len(answer_choices_list[0])
                    if not all(len(l) == the_len for l in answer_choices_list):
                        raise ValueError("not all lists have same length!")
                if len(answer_choices_list) > 0:
                    choices = answer_choices["fr"]
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
                    print(choices)
                    print(points)
                    for index, choice in enumerate(choices):
                        print(index)
                        print(choice)
                        print(points[index])
                        if points[index] == "":
                            points[index] = 3
                        c, _c = Choice.objects.get_or_create(
                            question=question,
                            order=index + 1,
                            defaults={"value": points[index]},
                        )
                        c.label_fr = c.label_en = c.label_es = choice.strip()
                        # ) = (
                        #     c.label_it
                        # ) = c.label_zh_hans = c.label_zh_hant
                        if "en" in answer_choices:
                            c.label_en = answer_choices["en"][index].strip()
                        if "es" in answer_choices:
                            c.label_es = answer_choices["es"][index].strip()
                        # if "it" in answer_choices:
                        #     c.label_it = answer_choices["it"][index].strip()
                        # if "zh-hans" in answer_choices:
                        #     c.label_zh_hans = answer_choices["zh-hans"][index].strip()
                        # if "zh-hant" in answer_choices:
                        #     c.label_zh_hant = answer_choices["zh-hant"][index].strip()
                        c.value = points[index]
                        c.save()

                subquestions = {}
                if check("SUBQUESTIONS_FR", row, column_indexes):
                    subquestions["fr"] = row[column_indexes["SUBQUESTIONS_FR"]].split(
                        ";"
                    )
                if check("SUBQUESTIONS_EN", row, column_indexes):
                    subquestions["en"] = row[column_indexes["SUBQUESTIONS_EN"]].split(
                        ";"
                    )
                if check("SUBQUESTIONS_ES", row, column_indexes):
                    subquestions["es"] = row[column_indexes["SUBQUESTIONS_ES"]].split(
                        ";"
                    )
                if check("SUBQUESTIONS_IT", row, column_indexes):
                    subquestions["it"] = row[column_indexes["SUBQUESTIONS_IT"]].split(
                        ";"
                    )
                if check("SUBQUESTIONS_ZH", row, column_indexes):
                    subquestions["zh-hans"] = row[
                        column_indexes["SUBQUESTIONS_ZH"]
                    ].split(";")
                if check("SUBQUESTIONS_ZH-CHT", row, column_indexes):
                    subquestions["zh-hant"] = row[
                        column_indexes["SUBQUESTIONS_ZH-CHT"]
                    ].split(";")

                subquestions_list = list(subquestions.values())
                print([f"{len(i)} " for i in subquestions_list])
                if len(subquestions_list) > 0:
                    the_len = len(subquestions_list[0])
                    if not all(len(l) == the_len for l in subquestions_list):
                        raise ValueError("not all lists have same length!")

                if "subquestions" in row[column_indexes["QUESTION_TYPE"]]:
                    if not "fr" in subquestions:
                        raise ValueError("Need at least french translation !")
                    print("--adding subquestions")
                    sq_order = 1
                    subquestions_obj = SubQuestion.objects.filter(
                        question=question
                    ).order_by("order")
                    for index, subquestion in enumerate(subquestions["fr"]):
                        label_fr = (
                            label_en
                        ) = (
                            label_es
                        ) = (
                            label_it
                        ) = label_zh_hans = label_zh_hant = subquestion.strip()
                        if "en" in subquestions:
                            label_en = subquestions["en"][index].strip()
                        if "es" in subquestions:
                            label_es = subquestions["es"][index].strip()
                        if "it" in subquestions:
                            label_it = subquestions["it"][index].strip()
                        if "zh-hans" in subquestions:
                            label_zh_hans = subquestions["zh-hans"][index].strip()
                        if "zh-hant" in subquestions:
                            label_zh_hant = subquestions["zh-hant"][index].strip()
                        if len(subquestions_obj) >= sq_order:
                            s = subquestions_obj[sq_order - 1]
                            s.label_fr = label_fr
                            s.label_en = label_en
                            s.label_es = label_es
                            # s.label_it = label_it
                            # s.label_zh_hans = label_zh_hans
                            # s.label_zh_hant = label_zh_hant
                            s.order = sq_order
                            s.ui_type = row[column_indexes["SUBQUESTIONS_TYPE"]]
                            s.save()
                        else:
                            s = SubQuestion.objects.create(
                                question=question,
                                order=sq_order,
                                label_fr=label_fr,
                                label_en=label_en,
                                label_es=label_es,
                                # label_it=label_it,
                                # label_zh_hans=label_zh_hans,
                                # label_zh_hant=label_zh_hant,
                                ui_type=row[column_indexes["SUBQUESTIONS_TYPE"]],
                            )

                        subquestions_choices = {}
                        if check("SUBQUESTIONS_CHOICES_FR", row, column_indexes):
                            subquestions_choices["fr"] = row[
                                column_indexes["SUBQUESTIONS_CHOICES_FR"]
                            ].split(";")
                        if check("SUBQUESTIONS_CHOICES_EN", row, column_indexes):
                            subquestions_choices["en"] = row[
                                column_indexes["SUBQUESTIONS_CHOICES_EN"]
                            ].split(";")
                        if check("SUBQUESTIONS_CHOICES_ES", row, column_indexes):
                            subquestions_choices["es"] = row[
                                column_indexes["SUBQUESTIONS_CHOICES_ES"]
                            ].split(";")
                        if check("SUBQUESTIONS_CHOICES_IT", row, column_indexes):
                            subquestions_choices["it"] = row[
                                column_indexes["SUBQUESTIONS_CHOICES_IT"]
                            ].split(";")
                        if check("SUBQUESTIONS_CHOICES_ZH", row, column_indexes):
                            subquestions_choices["zh-hans"] = row[
                                column_indexes["SUBQUESTIONS_CHOICES_ZH"]
                            ].split(";")
                        if check("SUBQUESTIONS_CHOICES_ZH-CHT", row, column_indexes):
                            subquestions_choices["zh-hant"] = row[
                                column_indexes["SUBQUESTIONS_CHOICES_ZH-CHT"]
                            ].split(";")

                        subquestions_choices_list = list(subquestions_choices.values())
                        if len(subquestions_choices_list) > 0:
                            the_len = len(subquestions_choices_list[0])
                            if not all(
                                len(l) == the_len for l in subquestions_choices_list
                            ):
                                raise ValueError("not all lists have same length!")
                        sq_order += 1
                        if len(subquestions_choices) > 0:
                            if not "fr" in subquestions_choices:
                                raise ValueError("Need at least french translation !")
                            sub_choices = subquestions_choices["fr"]
                            sub_choices_values = [
                                c.strip()
                                for c in row[
                                    column_indexes["SUBQUESTIONS_POINTS"]
                                ].split(";")
                            ]
                            if len(sub_choices_values) < 2:
                                sub_choices_values = [-1] * len(sub_choices)
                            order = 0
                            for i in range(
                                min(len(sub_choices), len(sub_choices_values))
                            ):
                                if sub_choices_values[i] == "":
                                    sub_choices_values[i] = -1
                                sub_choice = sub_choices[i]
                                label_fr = (
                                    label_en
                                ) = (
                                    label_es
                                ) = (
                                    label_it
                                ) = label_zh_hans = label_zh_hant = sub_choice.strip()
                                if "en" in subquestions_choices:
                                    label_en = subquestions_choices["en"][i].strip()
                                if "es" in subquestions_choices:
                                    label_es = subquestions_choices["es"][i].strip()
                                if "it" in subquestions_choices:
                                    label_it = subquestions_choices["it"][i].strip()
                                if "zh-hans" in subquestions_choices:
                                    label_zh_hans = subquestions_choices["zh-hans"][
                                        i
                                    ].strip()
                                if "zh-hant" in subquestions_choices:
                                    label_zh_hant = subquestions_choices["zh-hant"][
                                        i
                                    ].strip()
                                SubquestionChoice.objects.update_or_create(
                                    subquestion=s,
                                    order=order,
                                    defaults={
                                        "value": sub_choices_values[i],
                                        "label_fr": label_fr,
                                        "label_en": label_en,
                                        "label_es": label_es,
                                        # "label_it": label_it,
                                        # "label_zh_hans": label_zh_hans,
                                        # "label_zh_hant": label_zh_hant,
                                    },
                                )
                                order += 1
                        else:
                            assert s.choices.count() == 0, (
                                "Question %i no longer have choices" % question.id
                            )
                    if len(subquestions["fr"]) < len(subquestions_obj):
                        for i in range(len(subquestions), len(subquestions_obj)):
                            subquestions_obj[i].delete()

                print("comments")
                # if strengths comment
                if check("STRENGTHS", row, column_indexes) or check(
                    "STRENGTHS_FR", row, column_indexes
                ):
                    comment, _c = Comment.objects.get_or_create(
                        question=question, is_good=True
                    )

                    try:
                        comment.description_en = row[
                            column_indexes["STRENGTHS"]
                        ].strip()
                    except KeyError:
                        pass

                    try:
                        comment.description_es = row[
                            column_indexes["STRENGTHS_ES"]
                        ].strip()
                    except KeyError:
                        pass
                    #
                    # try:
                    #     comment.description_it = row[
                    #         column_indexes["STRENGTHS_IT"]
                    #     ].strip()
                    # except KeyError:
                    #     pass
                    try:
                        comment.description_fr = row[
                            column_indexes["STRENGTHS_FR"]
                        ].strip()
                    except KeyError:
                        pass
                    # try:
                    #     comment.description_zh_hans = row[
                    #         column_indexes["STRENGTHS_ZH"]
                    #     ].strip()
                    # except KeyError:
                    #     pass
                    # try:
                    #     comment.description_zh_hant = row[
                    #         column_indexes["STRENGTHS_ZH-CHT"]
                    #     ].strip()
                    # except KeyError:
                    #     pass

                    comment.save()
                else:
                    Comment.objects.filter(question=question, is_good=True).delete()

                # If weaknesses comment
                if check("WEAKNESSES", row, column_indexes) or check(
                    "WEAKNESSES_FR", row, column_indexes
                ):
                    comment, _c = Comment.objects.get_or_create(
                        question=question, is_good=False
                    )

                    try:
                        comment.description_en = row[
                            column_indexes["WEAKNESSES"]
                        ].strip()
                    except KeyError:
                        pass

                    try:
                        comment.description_es = row[
                            column_indexes["WEAKNESSES_ES"]
                        ].strip()
                    except KeyError:
                        pass

                    # try:
                    #     comment.description_it = row[
                    #         column_indexes["WEAKNESSES_IT"]
                    #     ].strip()
                    # except KeyError:
                    #     pass
                    try:
                        comment.description_fr = row[
                            column_indexes["WEAKNESSES_FR"]
                        ].strip()
                    except KeyError:
                        pass
                    # try:
                    #     comment.description_zh_hans = row[
                    #         column_indexes["WEAKNESSES_ZH"]
                    #     ].strip()
                    # except KeyError:
                    #     pass
                    #
                    # try:
                    #     comment.description_zh_hant = row[
                    #         column_indexes["WEAKNESSES_ZH-CHT"]
                    #     ].strip()
                    # except KeyError:
                    #     pass
                    comment.save()
                else:
                    Comment.objects.filter(question=question, is_good=False).delete()

        # print(
        #     "Categories deleted", Category.objects.filter(subcategories=None).delete()
        # )
        # print(
        #     "SubCategories deleted", SubCategory.objects.filter(questions=None).delete()
        # )
        # raise Exception('END')
        questionnaire.google_sheet = rows.__str__()
        questionnaire.save()
