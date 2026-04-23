import csv
import os
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction
from django.db import migrations, models


def check(id, row, c):
    return id in c and len(row[c[id]]) >= 1


category_slugs = {
    "Genre": "gender",
    "Handicap": "disability",
    "Multi-culturel": "cultural_diversity",
    "Multi-générationnel": "generational_diversity",
    "LGBT+": "lgbt",
    "Général": "all",
    "Transversal": "all",
}


def revert_questions(apps, sheet_slug="evaluation_collaborateurs_360"):
    Question = apps.get_model("scoring", "Question")
    SubQuestionChoice = apps.get_model("scoring", "SubQuestionChoice")
    QuestionSheet = apps.get_model("scoring", "QuestionSheet")
    Evaluation = apps.get_model("scoring", "Evaluation")
    Evaluation.objects.filter(sheet__type__slug=sheet_slug).delete()
    SubQuestionChoice.objects.filter(
        subquestion__question__sheets__type__slug=sheet_slug
    ).delete()
    Question.objects.filter(sheets__type__slug=sheet_slug).delete()
    QuestionSheet.objects.filter(type__slug=sheet_slug).delete()


def import_questions(apps, file, type):
    QuestionSheetType = apps.get_model("scoring", "QuestionSheetType")
    Category = apps.get_model("scoring", "Category")
    SubCategory = apps.get_model("scoring", "SubCategory")
    Question = apps.get_model("scoring", "Question")
    QuestionSheet = apps.get_model("scoring", "QuestionSheet")
    Choice = apps.get_model("scoring", "Choice")
    Comment = apps.get_model("scoring", "Comment")
    SubQuestion = apps.get_model("scoring", "SubQuestion")
    SubquestionChoice = apps.get_model("scoring", "SubquestionChoice")

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
            type=sheet_type, version=version, slug=sheet_type.slug, year=year
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

                question, _c = Question.objects.get_or_create(
                    google_sheets_id=google_sheets_id,
                    defaults={
                        "label": row[column_indexes["QUESTION_LABEL"]],
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
                question.label = row[column_indexes["QUESTION_LABEL"]].strip()
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
                    question.theme = row[column_indexes["THEME"]]
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
                        question.help_text = old_question.help_text
                        question.sibling = old_question
                if check("HELP_TEXT", row, column_indexes):
                    question.help_text = row[column_indexes["HELP_TEXT"]]
                question.save()
                print("question")
                print(question.google_sheets_id, question.label)

                question.subcategory = subcategory
                question.save()

                print("choices")
                if check("ANSWER_CHOICES", row, column_indexes) and check(
                    "MARK", row, column_indexes
                ):
                    choices = [
                        c.strip()
                        for c in row[column_indexes["ANSWER_CHOICES"]].split("-")
                    ]
                    points = [p.strip() for p in row[column_indexes["MARK"]].split("-")]
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
                        c.label = choice
                        c.value = points[index]
                        c.save()

                if (
                    check("SUBQUESTIONS", row, column_indexes)
                    and "subquestions" in row[column_indexes["QUESTION_TYPE"]]
                ):
                    print("--adding subquestions")
                    subquestions = [
                        s.strip()
                        for s in row[column_indexes["SUBQUESTIONS"]].split("-")
                    ]
                    sq_order = 1
                    for subquestion in subquestions:
                        if "homme" in subquestion:
                            sq_order = 2
                        elif "femme" in subquestion:
                            sq_order = 1
                        elif "binaire" in subquestion:
                            sq_order = 3
                        s, _ = SubQuestion.objects.update_or_create(
                            question=question,
                            label=subquestion,
                            ui_type=row[column_indexes["SUBQUESTIONS_TYPE"]],
                            defaults={"order": sq_order},
                        )
                        sq_order += 1
                        if check("SUBQUESTIONS_CHOICES", row, column_indexes) and check(
                            "SUBQUESTIONS_POINTS", row, column_indexes
                        ):
                            sub_choices = [
                                c.strip()
                                for c in row[
                                    column_indexes["SUBQUESTIONS_CHOICES"]
                                ].split("-")
                            ]
                            sub_choices_values = [
                                c.strip()
                                for c in row[
                                    column_indexes["SUBQUESTIONS_POINTS"]
                                ].split("-")
                            ]
                            order = 0
                            for i in range(
                                min(len(sub_choices), len(sub_choices_values))
                            ):
                                if sub_choices_values[i] == "":
                                    sub_choices_values[i] = -1
                                SubquestionChoice.objects.update_or_create(
                                    subquestion=s,
                                    order=order,
                                    defaults={
                                        "value": sub_choices_values[i],
                                        "label": sub_choices[i],
                                    },
                                )
                                order += 1
                print("comments")
                if check("STRENGTHS", row, column_indexes):  # bonus comments
                    if row[column_indexes["STRENGTHS"]].strip():
                        comment, _c = Comment.objects.get_or_create(
                            question=question, status=True
                        )
                        comment.description = row[column_indexes["STRENGTHS"]].strip()
                        comment.save()
                    else:
                        Comment.objects.filter(question=question).delete()
                else:
                    Comment.objects.filter(question=question).delete()

                if check("WEAKNESSES", row, column_indexes):  # malus comments
                    if row[column_indexes["WEAKNESSES"]].strip():
                        comment, _c = Comment.objects.get_or_create(
                            question=question, status=False
                        )
                        comment.description = row[column_indexes["WEAKNESSES"]].strip()
                        comment.save()
                    else:
                        Comment.objects.filter(question=question).delete()
                else:
                    Comment.objects.filter(question=question).delete()

        print(
            "Categories deleted", Category.objects.filter(subcategories=None).delete()
        )
        print(
            "SubCategories deleted", SubCategory.objects.filter(questions=None).delete()
        )
        # raise Exception('END')
        questionnaire.google_sheet = rows.__str__()
        questionnaire.save()
