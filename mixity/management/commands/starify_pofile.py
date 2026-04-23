# encoding: utf-8
import re
import os
import logging

import polib
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

PODIR = "mixity/locale/{lang}/LC_MESSAGES/"
WORD = re.compile("\w+")

# regular expressions for parts of msgstr that should be kept as is :
PY_FORMAT = re.compile("%.")
PY_NBR_FORMAT = re.compile("%\.\d*.")
CURLY_FORMAT = re.compile(r"{\w+}")
DJANGO_FORMAT = re.compile("%\([^)]+\)[sd]")
XML_BRAKET = re.compile("<[^>]+>")


def replace_chain(match, replace_chain="*"):
    length = match.end() - match.start()
    lchain = len(replace_chain)
    return replace_chain * (length // lchain) + replace_chain[: length % lchain]


def starify_po(pofilepath):
    print("- " + pofilepath + "-----------------------")
    pof = polib.pofile(pofilepath)
    for poentry in pof:
        msg = poentry.msgid
        if not msg:
            continue
        new = WORD.sub(replace_chain, msg)
        for pattern in (
            PY_FORMAT,
            PY_NBR_FORMAT,
            CURLY_FORMAT,
            DJANGO_FORMAT,
            XML_BRAKET,
        ):
            for match in pattern.finditer(msg):
                start, end = match.span()
                new = new[:start] + msg[start:end] + new[end:]

        poentry.msgstr = new
        if poentry.msgid_plural:
            for key in poentry.msgstr_plural:
                poentry.msgstr_plural[key] = new
    for fuzzy in pof.fuzzy_entries():
        fuzzy.flags.remove("fuzzy")
    pof.save()
    print("generated", pofilepath)


class Command(BaseCommand):
    help = "Check translations for HTML and format errors."

    def handle(self, *args, **options):
        locale = PODIR.format(lang="fr")
        for filename in os.listdir(locale):
            if filename.endswith(".po"):
                starify_po(os.path.join(locale, filename))
