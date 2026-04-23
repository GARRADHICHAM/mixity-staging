import base64
import os
from datetime import datetime

from Crypto.Util.Padding import pad, unpad
from django.core.exceptions import ValidationError
from django.db import models
from Crypto.Cipher import AES
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


def get_random_iv():
    return os.urandom(
        16
    )  # See what's an Initialization Vector in AES-CBC https://fr.wikipedia.org/wiki/Vecteur_d%27initialisation


# Create your models here.
class ADPCredentials(models.Model):
    client_id = models.TextField()  # encrypted
    client_secret = models.TextField()  # encrypted
    entity = models.ForeignKey(
        "accounts.Entity", on_delete=models.PROTECT, null=True, blank=True
    )

    structure = models.ForeignKey(
        "accounts.Structure", on_delete=models.PROTECT, null=True, blank=True
    )
    iv = models.BinaryField(default=get_random_iv)

    class Meta:
        verbose_name = "ADP Credentials"
        verbose_name_plural = "ADP Credentials"
        ordering = ("entity", "structure")

    def get_credentials(self):
        return self.decrypt_data(self.client_id), self.decrypt_data(self.client_secret)

    # client_id and client_secret are encrypted with AES256-CBC mode and then base64 encoded
    def encrypt_data(self, data):
        cipher = AES.new(
            settings.ADP_CREDENTIALS_ENCRYPTION_KEY.encode("utf8"),
            AES.MODE_CBC,
            iv=self.iv,
        )
        encrypted_data = cipher.encrypt(
            pad(data.encode("utf-8"), block_size=AES.block_size)
        )
        encrypted_data = "ENCRYPTED#" + base64.b64encode(encrypted_data).decode("ascii")
        return encrypted_data

    def decrypt_data(self, data):
        decrypted = base64.b64decode(data.split("ENCRYPTED#")[1])
        cipher = AES.new(
            settings.ADP_CREDENTIALS_ENCRYPTION_KEY.encode("utf8"),
            AES.MODE_CBC,
            iv=self.iv,
        )
        return unpad(cipher.decrypt(decrypted), block_size=AES.block_size).decode(
            "utf-8"
        )

    # on save we encrypt the client_id and client_secret. If it's already encrypted, we do nothing
    def clean(self):
        super().clean()
        if not self.client_id.startswith("ENCRYPTED#"):
            self.client_id = self.encrypt_data(self.client_id)
        if not self.client_secret.startswith("ENCRYPTED#"):
            self.client_secret = self.encrypt_data(self.client_secret)
        if self.entity is None and self.structure is None:
            raise ValidationError("Structure and Entity are both None")
        elif self.entity and self.structure:
            raise ValidationError(
                "You need to provide either a structure or an entity, not both !"
            )

    def __str__(self):
        return f"Structure : {self.structure} | Entity : {self.entity}"


class ADPSoftware(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name


class ADPIndicatorType(models.Model):
    name = models.TextField()
    category = models.TextField(default="", blank=True)
    order_num = models.IntegerField(
        verbose_name="Ordre d'affichage",
        null=True,
        blank=True,
        db_index=True,
    )
    questions = models.ManyToManyField(
        to="scoring.Question",
        related_name="indicator_types",
        blank=True,
    )
    softwares = models.ManyToManyField(
        to="ADPSoftware",
        related_name="indicator_types",
    )
    label = models.TextField(default="Indicator title")

    def __str__(self):
        return self.name


class ADPIndicator(models.Model):
    date = models.DateTimeField(default=timezone.now)
    data = models.JSONField()
    type = models.ForeignKey("ADPIndicatorType", on_delete=models.PROTECT)
    entity = models.ForeignKey("accounts.Entity", on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.entity} : {self.type.name} ({self.date})"


# ADPField/ADPFieldValue/ADPFieldMapping are not yet used. Will be used for free field in ADP API in the future in order
# to link more data with Mixity (for instance contracts)
class ADPField(models.Model):
    name = models.TextField()
    softwares = models.ManyToManyField(
        to="ADPSoftware",
        related_name="fields",
    )

    def __str__(self):
        return self.name


class ADPFieldValue(models.Model):
    value = models.TextField()
    field = models.ForeignKey("sirh.ADPField", on_delete=models.PROTECT)

    def __str__(self):
        return self.field.name + " : " + self.value


class ADPFieldMapping(models.Model):
    original_label = models.TextField()
    field_value = models.ForeignKey("sirh.ADPFieldValue", on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.field_value.field.name} : {self.original_label} => {self.field_value.value}"


def steps():
    return {
        "connection": {"status": "ongoing", "date": datetime.now().timestamp()},
        "gathering": {"status": "pending", "date": datetime.now().timestamp()},
        "processing": {"status": "pending", "date": datetime.now().timestamp()},
    }


class ADPStatus(models.Model):
    entity = models.ForeignKey(
        "accounts.Entity",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="adp_status",
    )

    structure = models.ForeignKey(
        "accounts.Structure",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="adp_status",
    )

    processed_indicators = models.ManyToManyField(
        to=ADPIndicator,
        related_name="processed_status",
        verbose_name="Indicateurs traités",
        blank=True,
    )
    partial_indicators = models.ManyToManyField(
        to=ADPIndicator,
        related_name="partial_status",
        verbose_name="Indicateurs traités partiellement",
        blank=True,
    )
    unprocessed_indicator_types = models.ManyToManyField(
        to=ADPIndicatorType,
        related_name="status",
        verbose_name="Indicateurs non-traités",
        blank=True,
    )
    requested_software = models.ForeignKey(
        ADPSoftware, on_delete=models.PROTECT, null=True, blank=True
    )
    request_text = models.TextField()

    steps = models.JSONField(default=steps, blank=True)

    update_frequency = models.IntegerField(
        default=1, verbose_name="Fréquence de MAJ (en mois)"
    )

    last_updated = models.DateTimeField(default=datetime.fromtimestamp(0))

    update_automatically = models.BooleanField(default=True)

    can_update = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.entity is None and self.structure is None:
            raise ValidationError("Structure and Entity are both None")
        elif self.entity and self.structure:
            raise ValidationError(
                "You need to provide either a structure or an entity, not both !"
            )

    def __str__(self):
        return (
            f"Structure : {self.entity.entity_level.structure} | Entity : {self.entity}"
        )
