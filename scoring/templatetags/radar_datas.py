import logging
from django.template.defaulttags import register

logger = logging.getLogger(__name__)


@register.simple_tag
def radar_datas(evaluation, target=None, score_categories=None, human_filter=None):
    try:
        measures = evaluation.get_radar_data(target, score_categories, human_filter)
        return measures
    except Exception as e:
        print("in exception")
        logger.exception(e)
        return None
