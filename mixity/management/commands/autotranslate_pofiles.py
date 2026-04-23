# encoding: utf-8
import logging

import polib
from django.core.management.base import BaseCommand
from fast_i18n.translations import generate_translator

from accounts.vocabularies import LANGUAGE_CHOICES

logger = logging.getLogger(__name__)

LOCALE_DIR = "mixity/locale/%s/LC_MESSAGES/"
LOCALE_POFILE = LOCALE_DIR + "django.po"
LOCALE_JS_POFILE = LOCALE_DIR + "djangojs.po"


class Command(BaseCommand):
    help = "Generates database translations. Use --autotranslate to use GoogleTranslate to initialize empty translations."
    TARGET_CODES = {
        "fr": "french",
        "en": "english",
        "es": "spanish",
    }

    def normalize_first_letter_case(self, entry):
        if not entry.msgid or not entry.msgstr:
            return
        if entry.msgid[0].islower() == entry.msgstr[0].islower():
            return
        if entry.msgid[0].isupper():
            entry.msgstr = entry.msgstr[0].upper() + entry.msgstr[1:]
        else:
            entry.msgstr = entry.msgstr[0].lower() + entry.msgstr[1:]

    def autotranslate_file(self, filepath, lcode, target_language):
        logger.info("-" * 50)
        logger.info("Auto-translating empty '%s:%s' wordings", lcode, target_language)
        db_po = polib.pofile(filepath)
        count = 0
        translator = generate_translator(
            "GoogleTranslator",
            source_codes=("fr", "french"),
            target_codes=(target_language, lcode),
        )
        for entry in db_po:
            # TODO: handle msgid_plural/msgstr_plural
            if entry.msgstr or not entry.msgid:
                self.normalize_first_letter_case(entry)
                continue
            logger.info("  * Translating %r" % entry.msgid)
            entry.msgstr = translator.translate(entry.msgid)
            self.normalize_first_letter_case(entry)
            entry.flags.append("fuzzy")
            count += 1
        db_po.save(filepath)
        logger.info("Finished! %i entries auto-translated in %s" % (count, filepath))

    def handle(self, *args, **options):
        for lcode, language in LANGUAGE_CHOICES:
            if lcode == "fr":
                # Do not autotranslate French !
                continue
            target_language = self.TARGET_CODES[lcode]
            self.autotranslate_file(LOCALE_POFILE % lcode, lcode, target_language)
            self.autotranslate_file(LOCALE_JS_POFILE % lcode, lcode, target_language)
