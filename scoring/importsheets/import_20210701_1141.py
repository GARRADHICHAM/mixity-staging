import csv
from collections import defaultdict

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
        print(questionnaire.type, questionnaire.version)
        print(f"{questionnaire}")

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

                if check("QUESTION_LABEL_EN", row, column_indexes):
                    label_en = row[column_indexes["QUESTION_LABEL_EN"]]
                else:
                    label_en = row[column_indexes["QUESTION_LABEL"]]
                question, _c = Question.objects.get_or_create(
                    google_sheets_id=google_sheets_id,
                    defaults={
                        "label_fr": row[column_indexes["QUESTION_LABEL"]],
                        "label_en": label_en,
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
                question.label_fr = row[column_indexes["QUESTION_LABEL"]].strip()

                if check("QUESTION_LABEL_EN", row, column_indexes):
                    label_en = row[column_indexes["QUESTION_LABEL_EN"]]
                else:
                    label_en = row[column_indexes["QUESTION_LABEL"]]

                question.label_en = label_en
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
                if check("THEME", row, column_indexes):
                    question.theme_fr = row[column_indexes["THEME"]]
                if check("THEME_EN", row, column_indexes):
                    question.theme_en = row[column_indexes["THEME_EN"]]
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
                    old_question = Question.objects.filter(
                        google_sheets_id=int(row[column_indexes["SIBLING_QUESTION"]])
                    ).first()
                    if old_question:
                        question.sibling = old_question
                if check("HELP_TEXT", row, column_indexes):
                    question.help_text_fr = row[column_indexes["HELP_TEXT"]]
                if check("HELP_TEXT_EN", row, column_indexes):
                    question.help_text_en = row[column_indexes["HELP_TEXT_EN"]]
                else:
                    question.help_text_en = None
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
                if check("ANSWER_CHOICES", row, column_indexes) and check(
                    "MARK", row, column_indexes
                ):
                    choices = [
                        c.strip()
                        for c in row[column_indexes["ANSWER_CHOICES"]].split(";")
                    ]
                    points = [p.strip() for p in row[column_indexes["MARK"]].split(";")]
                    print(choices)
                    print(points)
                    for index, choice in enumerate(choices):
                        print(index)
                        print(choice)
                        print(points[index])
                        choice = choice.split("|")
                        if points[index] == "":
                            points[index] = 3
                        c, _c = Choice.objects.get_or_create(
                            question=question,
                            order=index + 1,
                            defaults={"value": points[index]},
                        )
                        c.label_fr = choice[0]
                        if len(choice) > 1:
                            c.label_en = choice[1]
                        else:
                            c.label_en = choice[0]
                        c.value = points[index]
                        c.save()

                if (
                    check("SUBQUESTIONS", row, column_indexes)
                    and "subquestions" in row[column_indexes["QUESTION_TYPE"]]
                ):
                    print("--adding subquestions")
                    subquestions = [
                        s.strip()
                        for s in row[column_indexes["SUBQUESTIONS"]].split(";")
                    ]
                    sq_order = 1
                    subquestions_obj = SubQuestion.objects.filter(
                        question=question
                    ).order_by("order")
                    for subquestion in subquestions:
                        subquestion = subquestion.split("|")
                        if len(subquestion) > 1:
                            label_en = subquestion[1]
                        else:
                            label_en = subquestion[0]
                        if len(subquestions_obj) >= sq_order:
                            s = subquestions_obj[sq_order - 1]
                            s.label_fr = subquestion[0]
                            s.label_en = label_en
                            s.order = sq_order
                            s.ui_type = row[column_indexes["SUBQUESTIONS_TYPE"]]
                            s.save()
                        else:
                            s = SubQuestion.objects.create(
                                question=question,
                                order=sq_order,
                                label_fr=subquestion[0],
                                label_en=label_en,
                                ui_type=row[column_indexes["SUBQUESTIONS_TYPE"]],
                            )

                        sq_order += 1
                        if check("SUBQUESTIONS_CHOICES", row, column_indexes) and check(
                            "SUBQUESTIONS_POINTS", row, column_indexes
                        ):
                            sub_choices = [
                                c.strip()
                                for c in row[
                                    column_indexes["SUBQUESTIONS_CHOICES"]
                                ].split(";")
                            ]
                            sub_choices_values = [
                                c.strip()
                                for c in row[
                                    column_indexes["SUBQUESTIONS_POINTS"]
                                ].split(";")
                            ]
                            order = 0
                            for i in range(
                                min(len(sub_choices), len(sub_choices_values))
                            ):
                                if sub_choices_values[i] == "":
                                    sub_choices_values[i] = -1
                                sub_choice = sub_choices[i].split("|")
                                if len(sub_choice) > 1:
                                    label_en = sub_choice[1]
                                else:
                                    label_en = sub_choice[0]
                                SubquestionChoice.objects.update_or_create(
                                    subquestion=s,
                                    order=order,
                                    defaults={
                                        "value": sub_choices_values[i],
                                        "label_fr": sub_choice[0],
                                        "label_en": label_en,
                                    },
                                )
                                order += 1
                    if len(subquestions) < len(subquestions_obj):
                        for i in range(len(subquestions), len(subquestions_obj)):
                            subquestions_obj[i].delete()

                print("comments")
                # if strengths comment
                if check("STRENGTHS", row, column_indexes) or check(
                    "STRENGTHS_FR", row, column_indexes
                ):
                    comment, _c = Comment.objects.get_or_create(
                        question=question, status=True
                    )

                    try:
                        comment.description_en = row[
                            column_indexes["STRENGTHS"]
                        ].strip()
                    except KeyError:
                        pass

                    try:
                        comment.description_fr = row[
                            column_indexes["STRENGTHS_FR"]
                        ].strip()
                    except KeyError:
                        pass

                    comment.save()
                else:
                    Comment.objects.filter(question=question, status=True).delete()

                # If weaknesses comment
                if check("WEAKNESSES", row, column_indexes) or check(
                    "WEAKNESSES_FR", row, column_indexes
                ):
                    comment, _c = Comment.objects.get_or_create(
                        question=question, status=False
                    )

                    try:
                        comment.description_en = row[
                            column_indexes["WEAKNESSES"]
                        ].strip()
                    except KeyError:
                        pass

                    try:
                        comment.description_fr = row[
                            column_indexes["WEAKNESSES_FR"]
                        ].strip()
                    except KeyError:
                        pass

                    comment.save()
                else:
                    Comment.objects.filter(question=question, status=False).delete()

        print(
            "Categories deleted", Category.objects.filter(subcategories=None).delete()
        )
        print(
            "SubCategories deleted", SubCategory.objects.filter(questions=None).delete()
        )
        # raise Exception('END')
        questionnaire.google_sheet = rows.__str__()
        questionnaire.save()
