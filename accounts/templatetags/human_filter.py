import logging

from django import template
from django.db.models import Q, Count
from scoring.models import Collaborator

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag
def computed_human_collaborator(
    evaluation, value, collaborators_queryset, nb_collaborator_with_filter=0
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
        logger.exception(e)
        return [res]
    return [res]


@register.simple_tag
def computed_criteria(human_criteria, nb_collaborator_with_filter=0):
    res = []
    for choice in human_criteria.choices.all():
        if nb_collaborator_with_filter != 0:
            value = (choice.total / nb_collaborator_with_filter) * 100
        else:
            value = 0
        res.append({"label": choice.label, "value": value})

    # Repartition des criteria_choices en plusieurs colonne si il y en a plus de 10
    size_res = len(res)
    if size_res > 10:
        size_1 = int(size_res / 3) + int(size_res % 3 / 2)
        size_2 = size_1 * 2
        if size_res % 3 == 1:
            size_1 += 1
            size_2 += 1
        return [False, [[res[:size_1]], [res[size_1:size_2]], [res[size_2:]]]]
    return [True, [res]]
