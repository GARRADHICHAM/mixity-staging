import json
from copy import deepcopy

from django.template.defaulttags import register
from django.utils.translation import ugettext_lazy as _
from mixity.services.namsor.api import Namsor
from scoring.models import CollaboratorsStatistics
from accounts.vocabularies import TYPE_CHOICES

EMPTY_VALUE = 0.0000001  # ChartJS doesn't allow 0 on charts


def group_results(results: list[dict], group_by: list) -> dict[dict]:
    groups = {}
    for result in results:
        if isinstance(result, str):
            continue
        group = Namsor.get_ethnicity_choices().get(result["name"])
        if group and group_by:
            group = str(_(getattr(group, group_by[0])))
        else:
            group = result["name"]
        if group not in groups:
            groups[group] = []
        groups[group].append(result)
    if group_by and group_by[0] == "region":
        for region in Namsor.get_regions():
            if region not in groups:
                groups[region] = [{"name": region, "value": EMPTY_VALUE}]
    if group_by and len(group_by) > 1:
        group_by = group_by[1:]
        for key, group in groups.items():
            groups[key] = group_results(group, group_by)
    return groups


def compute_labels_and_results(results, total):
    labels = []
    data = []
    for key, result in results.items():
        if isinstance(result, dict):
            children_labels, children_result = compute_labels_and_results(result, total)
            data.append(
                {
                    "value": sum([obj["value"] for obj in children_result]),
                    "children": children_result,
                }
            )
        else:
            for obj in result:
                if Namsor.get_ethnicity_choices().get(key):
                    key = str(_(Namsor.get_ethnicity_choices().get(key).name))
                group_obj = Namsor.get_ethnicity_choices().get(obj["name"])
                if group_obj:
                    obj["name"] = str(_(group_obj.name))
            children_labels = [obj["name"] for obj in result]
            children_result = [obj["value"] * 100 / total for obj in result]
            data.append({"value": sum(children_result), "children": children_result})
        labels.append({"label": key, "children": children_labels})
    return labels, data


def compute_array(obj: CollaboratorsStatistics, group_by, total):
    results = group_results(
        deepcopy(obj.statistics and obj.statistics.computed_data or []), group_by
    )
    return compute_labels_and_results(results, total)

def get_name(obj: CollaboratorsStatistics):
    for key, choice in TYPE_CHOICES:
        if key == obj.type:
            return choice

# Scopes : us, world, all
@register.filter(name="get_collaborators_statistics")
def get_collaborators_statistics(
    objs: [CollaboratorsStatistics],
    params="{}",
):
    data_array = []
    params = json.loads(params)
    group_by = params.get("group_by", ["name"])
    for obj in objs:
        total = obj.statistics and obj.statistics.processed_collaborators or 1
        total_unprocessed = (
            obj.statistics and obj.statistics.unprocessed_collaborators or 0
        )
        confidence = obj.statistics and obj.statistics.confidence or 0
        if obj.has_one_sub_region:
            group_by_individual = None
        else:
            group_by_individual = group_by
        labels, data = compute_array(obj, group_by_individual, total)
        data = {
            "confidence": confidence * 100,
            "data": data,
            "labels": labels,
            "label": str(obj.label),
            "name": str(get_name(obj)),
            "processed_collaborators": total,
            "unprocessed_collaborators": total_unprocessed,
        }
        data_array.append(data)
    return json.dumps(data_array)
