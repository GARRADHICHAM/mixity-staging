from django import template

register = template.Library()


@register.filter
def allow_evaluation(user, subscription):
    return user.allow_evaluation(subscription)
