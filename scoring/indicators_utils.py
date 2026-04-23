from copy import deepcopy

from django.db.models import Q, F, QuerySet
from django.db.models.aggregates import Count, Sum
from django.utils.translation import get_language

from mixity.utils import DictCache
from scoring.models import Answer, Choice, Evaluation, SubquestionChoice


class HumanResultsPerIndicator:
    cache = DictCache()  # static cache. Faster than django cache.

    def __init__(
        self,
        param: dict,
        question_id: int,
        evaluation: Evaluation,
        collaborators_queryset,
    ):
        """

        @param param: Dict which contains the required info such as collaboratocollaborators_querysetr_filters, indicator_type or field to
        sort
        Ex : {"type":"rate_choice_total", "combine":"0,1", "sort":"combined_value", "collaborator_filters":{
        "civility":"woman"}}
        type : The way the results are computed (call the calculation method of the same name
        in this model)
        combine: indexes of the list of choices/subanswers/subanswerchoices to combine the results. 0,
        1 => do a sum of first and second element
        sort : key which will sort the elements
        collaborator_filters : list
        of collaborator filters (properties of Collaborator models). value can be string (ex "woman") or list (ex [
        "woman","man"]). List allows multiple values for the same field (if you want to display men and women for
        example) Answers will be filtered with these elements
        @param question_id: Id of the current question
        @param evaluation: instance of the current evaluation
        """
        self.param = param
        self.question_id = question_id
        self.evaluation = evaluation
        self.collaborators_queryset = collaborators_queryset
        self.answers = Answer.objects.filter(question=self.question_id,).filter(
            Q(
                evaluation__is_validated_by_user=True,
                evaluation__include_in_human_benchmark=True,
            )
            | Q(evaluation_id=evaluation.id)
        )
        if self.param["type"] == "rate_choice_total":
            self.answers_count_global_no_forced_filter = {
                a["evaluation_id"]: a["value"]
                for a in self.answers.filter(
                    collaborator__in=self.collaborators_queryset
                )
                .values("evaluation_id")
                .annotate(value=Count("id"))
            }  # compute the answers count for each evaluation as a dict {id:count, id2:count2}
        self.answers_count_global = {
            a["evaluation_id"]: a["value"]
            for a in self.answers.filter(collaborator__in=self.collaborator_filters())
            .values("evaluation_id")
            .annotate(value=Count("id"))
        }  # compute the answers count for each evaluation as a dict {id:count, id2:count2}
        self.answers = self.answers.filter(
            collaborator__in=self.collaborator_filters()
        )  # we filter the current answers with collaborator filters
        self.evaluations_sector_list = self.cache.get_or_set(
            f"evaluations_sector_list_{evaluation.id}",
            self.get_evaluations_ids_from_sector,
        )

    def get_evaluations_ids_from_sector(self):
        """
        Get a set of evaluation ids in the same sector as current evaluation (with same version of human)
        @return:
        """
        return set(
            Evaluation.objects.filter(sheet__type__slug="evaluation_collaborateurs_360")
            .filter(
                Q(
                    entity__entity_level__structure__business_line=self.evaluation.entity.entity_level.structure.business_line
                )
                | Q(
                    entity__entity_level__structure__secondary_business_lines=self.evaluation.entity.entity_level.structure.business_line
                )
            )
            .values_list(
                "id", flat=True
            )  # we gather the ids from evaluations of the current sector
        )

    def collaborator_filters(self):
        """
        Filter elements according to collaborator filters provided in __init__
        @param prefix: prefix of the django
        filter lookup (depending on which model you filter and the depth relation with collaborators). If you filter
        on an object with a direct relation with Collaborator model, no prefix needed. If you do a filter on an
        object with SubAnswer for example (who has a depth 1 relation with Collaborator), you need to had the prefix
        "answer__" which represent the relation to link with the Collaborator model
        @return: QuerySet of answers/subanswers/subanswerschoice
        """
        queryset = self.collaborators_queryset
        if "collaborator_filters" in self.param:
            for key, value in self.param["collaborator_filters"].items():
                if type(value) == list:
                    queryset = queryset.filter(**{f"{key}__in": value})
                else:
                    queryset = queryset.filter(**{f"{key}": value})
        return queryset

    def get_evaluation_answers_count(self, evaluation_id=None, total=False):
        """
        Get number of answers of an evaluation (current one by default)
        @param evaluation_id: Id of the evaluation
        @return: int : number of answers
        """
        if total:
            return self.answers_count_global_no_forced_filter[
                evaluation_id or self.evaluation.id
            ]
        return self.answers_count_global[evaluation_id or self.evaluation.id]

    def evaluation_exists(self, evaluation_id=None):
        """
        Check if the evaluation exists in our case
        @param evaluation_id: id of the evaluation
        @return:
        """
        return (evaluation_id or self.evaluation.id) in self.answers_count_global

    def group_by(
        self,
        queryset: QuerySet,
        id_to_group: str,
        next_value_field: str,
        value_field: str,
    ):
        """
        Group answers together and copy empty answers to all evaluations who haven't these answers.
        @param queryset: Queryset of computed results
        @param id_to_group: key of the list dict which will generate the keys of the result dict and group every element who has the same value of the key together.
        @param next_value_field: key of the field that indicate we change answer/subanswer/subanswerchoice (id)
        @param value_field: key of the field which represents the value of the answer/subanswer/subanswerchoice
        @return: grouped results {id1:[{myitem}, {myitem2}],id2:[{myitem3},{myitem4}]}
        """
        queryset = queryset.order_by(next_value_field)
        returned_dict = {}
        for elem in queryset:
            returned_dict[elem[id_to_group]] = []
        current_element = None
        added_to_evaluation = []
        elem = None
        for elem in queryset:
            if current_element is None:
                current_element = deepcopy(elem)
            if elem[next_value_field] != current_element[next_value_field]:
                for non_added in returned_dict.keys():
                    if non_added not in added_to_evaluation:
                        elem_copy = current_element
                        elem_copy[value_field] = 0
                        returned_dict[non_added].append(elem_copy)
                added_to_evaluation = []
            current_element = deepcopy(elem)
            if elem[id_to_group]:
                added_to_evaluation.append(elem[id_to_group])
                returned_dict[elem[id_to_group]].append(elem)

        if elem:
            for non_added in returned_dict.keys():
                if non_added not in added_to_evaluation:
                    elem_copy = current_element
                    elem_copy[value_field] = 0
                    returned_dict[non_added].append(elem_copy)
        if None in returned_dict:
            del returned_dict[None]
        return returned_dict

    def get_results(self):
        """
        Get the results of the current question for this evaluation, as well as results for the sector and globally according to the parameters sent in __init__.
        @return: list [company_results,sector_results,global_results]
        """
        attr = getattr(
            self, "compute_results_with__" + self.param["type"].lower(), None
        )
        results = attr() if callable(attr) else []

        if len(results) > 0:
            if self.param["type"] != "rate_subanswers_choice_count":
                if results.get(self.evaluation.id):
                    results = [
                        deepcopy(results[self.evaluation.id]),
                        self.simple_mean(
                            self.filter_results_with_sector(results), "value"
                        ),
                        self.simple_mean(results, "value"),
                    ]
            else:
                results = [
                    deepcopy(list(results[self.evaluation.id].values())),
                    self.subchoice_mean(
                        deepcopy(self.filter_results_with_sector(results))
                    ),
                    self.subchoice_mean(results),
                ]

        if "combine" in self.param:
            results = self.combine(results)

        if "sort" in self.param:
            results = self.sort_obj(results)
        return results

    def combine(self, results):
        """
        Combine results of two or more elements according to parameters sent in __init__. If the value provided of
        "combine" is 0,1,3. A new element named "combined_value" will be created in the first answer element
        containing the sum of first, second and fourth answers.
        @param results: list [company_results,sector_results,global_results]
        @return: list [company_results,sector_results,global_results] (but combined)
        """
        for key in range(len(results)):
            list_combines = self.param["combine"].split("|")
            for list_combine in list_combines:
                list_combine = list_combine.split(",")
                initial_index = int(list_combine[0])
                if "choices" in results[key][initial_index]:
                    for i in range(len(results[key])):
                        results[key][i]["choices"][initial_index][
                            "combined_value"
                        ] = results[key][i]["choices"][initial_index]["value"]
                        for j in range(1, len(list_combine)):
                            index = int(list_combine[j])
                            if len(results[key]) > index:
                                results[key][i]["choices"][initial_index][
                                    "combined_value"
                                ] += results[key][i]["choices"][index]["value"]
                else:
                    results[key][initial_index]["combined_value"] = results[key][
                        initial_index
                    ]["value"]
                    for i in range(1, len(list_combine)):
                        index = int(list_combine[i])
                        if len(results[key]) > index:
                            results[key][initial_index]["combined_value"] += results[
                                key
                            ][index]["value"]
        return results

    def sort_obj(self, results):
        """
        Sort results according to params sent in __init__
        @param results: list [company_results,sector_results,global_results]
        @return: list [company_results,sector_results,global_results] (but sorted)
        """
        for index in range(len(results)):
            if self.param["sort"] == "value" or self.param["sort"] == "combined_value":
                if len(results[index]) > 0 and "choices" in results[index][0]:
                    results[index].sort(
                        key=lambda x: x["choices"][0][self.param["sort"]], reverse=True
                    )
                else:
                    results[index].sort(
                        key=lambda x: x[self.param["sort"]], reverse=True
                    )
            elif self.param["sort"] == "reverse":
                results[index].reverse()
        return results

    def compute_results_with__count_choice(self):
        """
        Count the number of time a choice has been selected in the evaluation
        @return: dict {evaluationID1:[results], evaluationID2:[results],...}
        """
        return self.filter_results_with_validated(
            self.group_by(
                Choice.objects.filter(question_id=self.question_id)
                .annotate(choice_id=F("id"))
                .values("choice_id")
                .annotate(
                    value=Count(
                        "choice_id",
                        filter=Q(answers__collaborator__in=self.collaborator_filters()),
                    ),
                    evaluation_id=F("answers__evaluation_id"),
                    label=F("label_" + get_language()),
                ),
                "evaluation_id",
                "choice_id",
                "value",
            )
        )

    def compute_results_with__count_subanswers(self):
        """
        Will count the number of time each subanswer is present is the questionnaire (how many times a collaborator choose an option)
        @return: dict {evaluationID1:[results], evaluationID2:[results],...}
        """
        return self.group_by(
            self.answers.annotate(subquestion_id=F("subanswers__subquestion_id"))
            .values("subquestion_id")
            .annotate(
                value=Sum("subanswers__value"),
                evaluation_id=F("subanswers__answer__evaluation_id"),
                label=F("subanswers__subquestion__label_" + get_language()),
            ),
            "evaluation_id",
            "subquestion_id",
            "value",
        )

    def compute_results_with__rate_subanswers(self):
        """
        Same as compute_results_with__count_subanswers but with a ratio instead of a sum
        @return: dict {evaluationID1:[results], evaluationID2:[results],...}
        """
        results_grouped = self.compute_results_with__count_subanswers()
        return self.do_rate(results_grouped)

    def do_rate(self, results_grouped, total=False):
        """
        Calculate a ratio with the value of the answer and the number of answers
        @return: dict {evaluationID1:[results], evaluationID2:[results],...}
        """
        for evaluation_id, items in results_grouped.items():
            if self.get_evaluation_answers_count(evaluation_id, total) > 0:
                for key in range(len(results_grouped[evaluation_id])):
                    results_grouped[evaluation_id][key]["value"] = (
                        results_grouped[evaluation_id][key]["value"]
                        * 100
                        / self.get_evaluation_answers_count(evaluation_id, total)
                    )
        return results_grouped

    def compute_results_with__rate_choice_total(self):
        """
        Same as compute_results_with__count_choice but with a ratio on number of answers
        @return: dict {evaluationID1:[results], evaluationID2:[results],...}
        """
        results_grouped = self.compute_results_with__count_choice()
        return self.do_rate(results_grouped, total=True)

    def compute_results_with__rate_subanswers_count(self):
        """
        Will count how many subanswers have been selected in a question and calculate a ratio depending on number of answers
        @return: dict {evaluationID1:[results], evaluationID2:[results],...}
        """
        results_grouped = self.group_by(
            self.answers.annotate(
                subquestion_id=F("subanswers__subquestion_id"),
            )
            .values("subquestion_id", "evaluation_id")
            .annotate(
                value=Count("subquestion_id"),
                label=F("subanswers__subquestion__label_" + get_language()),
            ),
            "evaluation_id",
            "subquestion_id",
            "value",
        )
        return self.do_rate(results_grouped)

    def compute_results_with__rate_subanswers_choice_count(self):
        """
        Will count how many times each subanswers choice has been selected in a question and calculate a ratio depending on number of answers
        @return: dict {evaluationID1:[results], evaluationID2:[results],...}
        """
        results_grouped = self.filter_results_with_validated(
            self.group_by(
                (
                    SubquestionChoice.objects.filter(
                        subquestion__question_id=self.question_id
                    )
                    .values(
                        "id",
                        "subquestion_id",
                    )
                    .annotate(
                        id__count=Count(
                            "id",
                            filter=Q(
                                subanswers__answer__collaborator__in=self.collaborator_filters()
                            ),
                        ),
                        evaluation_id=F("subanswers__answer__evaluation_id"),
                        subquestion_label=F("subquestion__label_" + get_language()),
                    )
                ),
                "evaluation_id",
                "id",
                "id__count",
            )
        )
        return_value = {}
        for evaluation_id, items in results_grouped.items():
            return_value[evaluation_id] = {}
            for item in results_grouped[evaluation_id]:
                if item["subquestion_id"]:
                    if not item["subquestion_id"] in return_value[evaluation_id]:
                        return_value[evaluation_id][item["subquestion_id"]] = {
                            "subquestion_id": item["subquestion_id"],
                            "label": item["subquestion_label"],
                            "choices": [],
                        }
                    if self.get_evaluation_answers_count(evaluation_id) > 0:
                        return_value[evaluation_id][item["subquestion_id"]][
                            "choices"
                        ].append(
                            {
                                "sub_choice_id": item["id"],
                                "value": item["id__count"]
                                * 100
                                / self.get_evaluation_answers_count(evaluation_id),
                            }
                        )
        return return_value

    def compute_results_with__rate_choice(self):
        """
        Same as compute_results_with__rate_choice_total but with a ratio on total value of the choices (points) and not the number of answers
        @return: dict {evaluationID1:[results], evaluationID2:[results],...}
        """
        results_grouped = self.compute_results_with__count_choice()
        for evaluation_id, items in results_grouped.items():
            if self.get_evaluation_answers_count(evaluation_id) > 0:
                choice_sum = sum(
                    choice["value"] for choice in results_grouped[evaluation_id]
                )
                if choice_sum > 0:
                    for key in range(len(results_grouped[evaluation_id])):
                        results_grouped[evaluation_id][key]["value"] = (
                            results_grouped[evaluation_id][key]["value"]
                            * 100
                            / choice_sum
                        )
        return results_grouped

    def simple_mean(self, results, field_to_mean):
        """
        Create a mean on a field for each answer/subanswer
        @param results: dict {evaluationID1:[results], evaluationID2:[results],...}
        @param field_to_mean: key of the field to mean
        @return: [results] (but aggregated)
        """
        final_results = results[self.evaluation.id]
        number_of_questions = len(final_results)
        for key in range(number_of_questions):
            tmp_result = 0
            for evaluation_results in results.values():
                tmp_result += evaluation_results[key][field_to_mean]
            final_results[key][field_to_mean] = tmp_result / len(results)
        return final_results

    def subchoice_mean(self, results):
        """
        Same as simple_mean but for subanswerchoice
        @param results: dict {evaluationID1:[results], evaluationID2:[results],...}
        @param field_to_mean: key of the field to mean
        @return: [results] (but aggregated)
        """
        final_results = list(results[self.evaluation.id].values())
        number_of_questions = len(final_results)
        for key in range(number_of_questions):
            number_of_choices = len(final_results[key]["choices"])
            for choice_index in range(number_of_choices):
                tmp_result = 0
                for evaluation_results in results.values():
                    tmp_result += list(evaluation_results.values())[key]["choices"][
                        choice_index
                    ]["value"]
                final_results[key]["choices"][choice_index]["value"] = tmp_result / len(
                    results
                )
        return final_results

    def filter_results_with_sector(self, results):
        """
        filter results to only select those from the sector
        @param results: dict {evaluationID1:[results], evaluationID2:[results],...}
        @return: dict {evaluationID1:[results], evaluationID2:[results],...} (with evaluations from sector only)
        """
        sector_results = {}
        for evaluation_id, result in results.items():
            if evaluation_id in self.evaluations_sector_list:
                sector_results[evaluation_id] = deepcopy(result)
        return sector_results

    def filter_results_with_validated(self, results):
        """
        Only select answers from validated evaluations
        @param results: dict {evaluationID1:[results], evaluationID2:[results],...}
        @return: dict {evaluationID1:[results], evaluationID2:[results],...} (with validated evaluations only)
        """
        for evaluation_id in list(results.keys()):
            if not self.evaluation_exists(evaluation_id):
                del results[evaluation_id]
        return results
