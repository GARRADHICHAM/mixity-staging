# encoding: utf-8
import re
import os.path as osp
import logging

import polib
from django.core.management.base import BaseCommand, CommandError
from accounts.vocabularies import LANGUAGE_CHOICES
from mixity import settings

logger = logging.getLogger(__name__)

POFILE = "mixity/locale/{lang}/LC_MESSAGES/{domain}.po"


def clarify(entry):
    max_length = 50
    msgid = str(entry.msgid[:max_length])
    if len(entry.msgid) > max_length:
        msgid += "[...]"
    return msgid.strip().replace("\n", "\\n").replace("\t", "\\t")


class Validator(object):
    def __init__(self, filepath, lcode, language):
        self.filepath = filepath
        self.lcode = (
            settings.LANGUAGES_CODES_DJANGO[lcode]
            if lcode in settings.LANGUAGES_CODES_DJANGO
            else lcode
        )
        self.language = language
        self.failures = 0

    def run(self):
        self.log("info", "validating Po file for %s (%s)", self.language, self.filepath)
        self.pofile = polib.pofile(self.filepath)
        for entry in self.pofile.translated_entries():
            self.check_pattern(
                entry,
                r"<[^>]+>",
                "HTML tag changed",
                exclusions=["""title=['"].+['"]""", "<br ?/?>"],
            )
            self.check_pattern(entry, r"\{\{[^}]+\}\}", "Template variable changed")
            self.check_pattern(entry, r"\{[^}]+\}", "Variable changed")
            self.check_pattern(entry, r"%\([^)]+\)\w", "Format changed")
            self.check_pattern(entry, r"%[\w]", "Percent changed")
        # Checking missing and fuzzy translations
        if self.lcode in ["fr", "it", "zh_Hans", "zh_Hant", "ja"]:
            return  # No check in French
        fuzzy_entries = [
            repr(entry.msgid)
            for entry in self.pofile.fuzzy_entries()
            if not entry.obsolete
        ]
        untranslated_entries = [
            repr(entry.msgid)
            for entry in self.pofile.untranslated_entries()
            if not entry.obsolete
        ]
        nb_fuzzy = len(fuzzy_entries)
        nb_missing = len(untranslated_entries)
        if nb_fuzzy + nb_missing > 0:
            msg = "This file contains %i missing translations and %i fuzzy translations. Those will appear in French."
            if fuzzy_entries:
                msg += " Fuzzy examples: " + ", ".join(fuzzy_entries[:3]) + "."
            if untranslated_entries:
                msg += (
                    " Untranslated examples: "
                    + ", ".join(untranslated_entries[:3])
                    + "."
                )
            self.log("error", msg % (nb_missing, nb_fuzzy))

    def extract(self, text, regex, exclusions):
        results = regex.findall(text)
        if exclusions and len(exclusions):
            clean = []
            for res in results:
                for e in exclusions:
                    res = re.sub(e, "", res)
                if res:
                    clean.append(res)
            results = clean
        return results

    def check_pattern(self, entry, pattern, label="", exclusions=None):
        regex = re.compile(pattern)
        ref = self.extract(entry.msgid, regex, exclusions)
        ref_plural = self.extract(entry.msgid_plural, regex, exclusions)
        if len(ref) or len(ref_plural):
            if not len(entry.msgstr_plural):
                trans = self.extract(entry.msgstr, regex, exclusions)
                if trans != ref and trans != ref_plural:
                    self.log(
                        "error",
                        "********** %s - line %i **********\n"
                        + "Ref:   %s\n"
                        + "Trans: %s\n"
                        + "ID:    %s\n",
                        label,
                        entry.linenum,
                        ref,
                        trans,
                        clarify(entry),
                    )
                return
            for num, msg in entry.msgstr_plural.items():
                trans = self.extract(msg, regex, exclusions)
                if trans != ref and trans != ref_plural:
                    self.log(
                        "error",
                        "********** %s - line %i **********\n"
                        + "Ref:    %s\n"
                        + "Plural: %s\n"
                        + "Num:    %s\n"
                        + "Trans:  %s\n"
                        + "ID:     %s\n",
                        label,
                        entry.linenum,
                        ref,
                        ref_plural,
                        num,
                        trans,
                        clarify(entry),
                    )

    def log(self, level, msg, *args, **kwargs):
        func = getattr(logger, level)
        if level == "error":
            print(f"{self.filepath}: {msg}")
            self.failures += 1
        func(msg, *args, **kwargs)


class Command(BaseCommand):
    help = "Check translations for HTML and format errors."

    def iter_pofiles(self):
        for lcode, language in LANGUAGE_CHOICES:
            for domain in ("django", "djangojs"):
                target_file = POFILE.format(lang=lcode, domain=domain)
                if not osp.isfile(target_file):
                    logger.warning(f"Skipping file {target_file} (missing)")
                    continue
                yield target_file, lcode, language

    def handle(self, *args, **options):
        failures = 0
        for target_file, lcode, language in self.iter_pofiles():
            v = Validator(target_file, lcode, language)
            try:
                v.run()
            except Exception as e:
                print(f"{target_file}: {e}")
                logger.exception(e)
                failures += 1
            failures += v.failures
        if failures:
            raise CommandError("terminated with %s errors" % failures)
