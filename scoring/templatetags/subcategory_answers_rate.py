from django.template.defaulttags import register


@register.filter
def subcategory_answers_rate(score_category, subcategory):
    return score_category.subcategory_answers_rate(subcategory)