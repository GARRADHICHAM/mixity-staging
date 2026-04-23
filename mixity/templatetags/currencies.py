import collections

from django.template import Library, Node, TemplateSyntaxError

from accounts.vocabularies import CURRENCY_CHOICES

register = Library()

Currency = collections.namedtuple("Currency", ["code", "symbol"])


class GetAvailableCurrenciesNode(Node):
    def __init__(self, variable):
        self.variable = variable

    def render(self, context):
        context[self.variable] = [Currency(k, v) for k, v in CURRENCY_CHOICES]
        return ""


@register.tag("get_currency_list")
def do_get_currency_list(parser, token):
    """
    Store a list of available currencies in the context.
    Usage::
        {% get_currency_list as CURRENCIES %}
        {% for currency in CURRENCIES %}
        ...
        {% endfor %}
    This puts CURRENCY_CHOICES into the named variable.
    """
    args = token.contents.split()
    if len(args) != 3 or args[1] != "as":
        raise TemplateSyntaxError(
            "'get_currency_list' requires 'as variable' (got %r)" % args
        )
    return GetAvailableCurrenciesNode(args[2])
