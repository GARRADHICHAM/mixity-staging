import logging
from django.template.defaulttags import register

logger = logging.getLogger(__name__)


@register.simple_tag
def computed_answer(evaluation, answer, param, collaborators_queryset):
    try:
        data = answer.get_computed_value(evaluation, param, collaborators_queryset)
        return data
    except Exception as e:
        logger.exception(e)
        return None
