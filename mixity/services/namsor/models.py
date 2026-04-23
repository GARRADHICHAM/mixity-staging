from django.db import models
from django.utils.translation import ugettext_lazy as _


class NamsorEthnicity(models.Model):
    key = models.CharField(unique=True, max_length=128)
    name = models.CharField(unique=True, max_length=128)
    country = models.ForeignKey(
        "address.Country",
        verbose_name=_("Pays"),
        on_delete=models.PROTECT,
        related_name="namsor_ethnicities",
    )
    region = models.CharField(max_length=128)
    region2 = models.CharField(max_length=128)
    sub_region = models.CharField(max_length=128)
