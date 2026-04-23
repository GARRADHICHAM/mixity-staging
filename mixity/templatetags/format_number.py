import logging
from decimal import ROUND_HALF_UP, Decimal, localcontext

from django import template
from django.conf import settings
from django.template import TemplateSyntaxError
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from accounts.vocabularies import CURRENCY_CHOICES

logger = logging.getLogger(__name__)
register = template.Library()


def generic_round(
    value=None, current_year=None, last_year=None, delta=0, show_decimal=True
):
    """
    Apply Mixity round nomber rules
    """
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP

        if value is not None:
            if show_decimal and abs(value) < 10:
                value = Decimal(value).quantize(Decimal(".11"))
            else:
                value = Decimal(value)

        else:
            current_year_round = Decimal(current_year).to_integral_value()
            last_year_round = Decimal(last_year).to_integral_value()
            delta_round = Decimal(delta).to_integral_value()

            value = current_year_round - last_year_round + delta_round

        if not show_decimal or abs(value) >= 10 or value == value.to_integral_value():
            value = value.to_integral_value()

        return value


def normalize_input(input):
    if input is None:
        return None
    if type(input) in (int, float, Decimal):
        return input
    if isinstance(input, str):
        try:
            return float(input.replace(",", "."))
        except Exception:
            pass
    return None


def generic_to_string(
    value=None,
    current_year=None,
    last_year=None,
    delta=0,
    show_decimal=True,
    show_evolution=False,
):
    """
    Convert value to string and add evolution if needed
    """
    value = normalize_input(value)
    current_year = normalize_input(current_year)
    last_year = normalize_input(last_year)
    delta = normalize_input(delta)

    if value is None and current_year is None or value is None and last_year is None:
        return False, _("ND*")

    value = generic_round(value, current_year, last_year, delta, show_decimal)

    string = ""

    if show_evolution:
        if value == 0:
            string = settings.EVOLUTION_EQU_SYMBOL + " "

        elif value > 0:
            string = settings.EVOLUTION_POS_SYMBOL + " "

        elif value < 0:
            string = settings.EVOLUTION_NEG_SYMBOL + " "

    string += str(formats.localize(value, use_l10n=True))
    if string == "-0":
        string = "0"
    return True, string


# These functions are redefined to be used in the React-Django communication process and as a template tag also
def compute_evolution_points(
    value=None, current_year=None, last_year=None, delta=0, show_evolution=False
):
    """
    Format evolution between two years
    Usage::
        {% load format_number %}
        {% points value=10 %}
        or {% points value=10 show_evolution=True %}
        or {% points current_year=1.3 last_year=1.2 delta=0.2 %}
        or {% points current_year=1.3 last_year=1.2 delta=0.2 show_evolution=True %}
    """

    if type(value) == str:
        return value

    format_ok, str_value = generic_to_string(
        value=value,
        current_year=current_year,
        last_year=last_year,
        delta=delta,
        show_evolution=show_evolution,
    )

    if not format_ok:
        if None in (current_year, last_year):
            logger.warning(
                "Template tag points: current_year={current_year}, last_year={last_year}".format(
                    current_year=current_year, last_year=last_year
                )
            )

        return str_value

    return _("{number_of_points} pts").format(number_of_points=str_value)


def get_simple_number(value):
    """
    Format simple number
    Usage::
        {% load format_number %}
        {% simple_number value=simple_number_value %}
    """

    if type(value) == str:
        return value

    format_ok, str_value = generic_to_string(
        value=value, show_evolution=False, show_decimal=False
    )

    return str_value


@register.simple_tag(name="points")
def do_points(
    value=None, current_year=None, last_year=None, delta=0, show_evolution=False
):
    return compute_evolution_points(
        value=value,
        current_year=current_year,
        last_year=last_year,
        delta=delta,
        show_evolution=show_evolution,
    )


@register.simple_tag(name="percentage")
def do_percentage(
    value=None, current_year=None, last_year=None, delta=0, show_evolution=False
):
    """
    Format percentage evolution between two years
    Usage::
        {% load format_number %}
        {% percentage value=10 %}
        or {% percentage value=10 show_evolution=True %}
        or {% percentage current_year=1.3 last_year=1.2 delta=0.2 %}
        or {% percentage current_year=1.3 last_year=1.2 delta=0.2 show_evolution=True %}
    """

    if type(value) == str:
        if value == "":
            value = None
        else:
            return value
    format_ok, str_value = generic_to_string(
        value=value,
        current_year=current_year,
        last_year=last_year,
        delta=delta,
        show_evolution=show_evolution,
    )

    if not format_ok:
        return str_value

    return _("{percentage} %").format(percentage=str_value)


@register.filter("currency")
def filter_currency(value, currency_symbol):
    context = {"request": currency_symbol}
    return do_currency(context, value=value, currency_symbol=currency_symbol)


@register.simple_tag(name="currency", takes_context=True)
def do_currency(
    context,
    value=None,
    current_year=None,
    last_year=None,
    delta=0,
    show_evolution=False,
    currency_symbol=None,
):
    """
    Format currency
    Usage::
        {% load format_number %}
        {% currency value=10 %}
        or {% currency value=10 show_evolution=True %}
        or {% currency current_year=1.3 last_year=1.2 delta=0.2 %}
        or {% currency current_year=1.3 last_year=1.2 delta=0.2 show_evolution=True %}
    """
    # TODO Convert value

    if type(value) == str:
        return value

    format_ok, str_value = generic_to_string(
        value=value,
        current_year=current_year,
        last_year=last_year,
        delta=delta,
        show_evolution=show_evolution,
    )

    if not format_ok:
        if None in (current_year, last_year):
            logger.warning(
                "Template tag currency: current_year={current_year}, last_year={last_year}".format(
                    current_year=current_year, last_year=last_year
                )
            )

        return str_value

    if currency_symbol:
        # Test if we get symbol or currency code
        if len(currency_symbol) > 1:
            symbol = dict(CURRENCY_CHOICES)[currency_symbol]
        else:
            symbol = currency_symbol
    else:
        symbol = context["request"].CURRENCY_SYMBOL

    if not symbol:
        logger.warning(f"Template tag currency: No currency symbol provided")
        return _("ND*")

    return str_value + " " + symbol


@register.simple_tag(name="simple_number")
def do_simple_number(value):
    return get_simple_number(value=value)


@register.filter(name="to_int")
def do_to_int(value):
    return int(value)
