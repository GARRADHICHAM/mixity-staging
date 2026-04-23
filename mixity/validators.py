from datetime import date

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def year_validator(value):
    if value < 1700 or value > date.today().year + 1:
        raise ValidationError(
            _("L'année {value} n'est pas comprise entre 1700 et {year}").format(
                value=value,
                year=date.today().year + 1,
            )
        )
