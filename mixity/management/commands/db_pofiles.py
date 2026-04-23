# encoding: utf-8
import datetime
import logging
import os
import os.path as osp

import polib
from django.conf import settings
from django.core.management.base import BaseCommand

from accounts.vocabularies import LANGUAGE_CHOICES
from mixity.services.namsor.models import NamsorEthnicity
from scoring.models import Category, SubCategory, Question
from mixity.models import FAQCategory
from subscriptions.models import Product

logger = logging.getLogger(__name__)

LOCALE_DIR = "mixity/locale/%s/LC_MESSAGES/"
LOCALE_POFILE = LOCALE_DIR + "django.po"

METADATA = {
    "Project-Id-Version": settings.VERSION,
    "Report-Msgid-Bugs-To": settings.MIXITY_EMAIL_SUPPORT,
    "POT-Creation-Date": str(datetime.datetime.now()),
    "PO-Revision-Date": str(datetime.datetime.now()),
    "Language": "",
    "Last-Translator": "",
    "Language-Team": "",
    "MIME-Version": "1.0",
    "Content-Type": "text/plain; charset=utf-8",
    "Content-Transfer-Encoding": "8bit",
    "X-Generator": "db_pofiles.py",
}


class MessageCollector:
    def __init__(self, pofile):
        self.pofile = pofile

    def add_msg(self, msg, instance=None, translation=""):
        origin = instance.__class__.__name__, instance.id if instance else None
        if not msg:
            logger.warning(f"Empty message (origin: {instance})")
            return
        entry = self.pofile.find(msg, include_obsolete_entries=True)
        if entry:
            entry.obsolete = False
            if origin:
                entry.occurrences.append(origin)
            return
        entry = polib.POEntry(msgid=msg, msgstr=translation)
        if origin:
            entry.occurrences = [origin]
        self.pofile.append(entry)

    def load_db_data(self):
        i18n_data = {
            # queryset, attribute
            (Category.objects.all(), "name"),
            (SubCategory.objects.all(), "name,short_name"),
            (Product.objects.all(), "label"),
            (FAQCategory.objects.all(), "name"),
            (Question.objects.all(), "theme"),
            (
                NamsorEthnicity.objects.all(),
                "name,region,region2,sub_region",
            ),
        }
        for queryset, attribute in i18n_data:
            for instance in queryset:
                for att in attribute.split(","):
                    self.add_msg(getattr(instance, att), instance=instance)


class Command(BaseCommand):
    help = "Generates database translations."

    def handle(self, *args, **options):
        try:
            # Save a locale file for all languages
            for lcode, language in LANGUAGE_CHOICES:
                logger.info(
                    "\n\nGenerating DB Po file for %r (%s)\n%s",
                    lcode,
                    language,
                    "-" * 50,
                )
                lcode = (
                    settings.LANGUAGES_CODES_DJANGO[lcode]
                    if lcode in settings.LANGUAGES_CODES_DJANGO
                    else lcode
                )
                target_dir = LOCALE_DIR % lcode
                if not osp.isdir(target_dir):
                    os.makedirs(target_dir)
                target_file = LOCALE_POFILE % lcode
                if not osp.isfile(target_file):
                    os.close(os.open(target_file, os.O_CREAT))
                db_po = polib.pofile(target_file)
                collector = MessageCollector(db_po)
                collector.load_db_data()
                # db_po.metadata = METADATA.copy()
                # db_po.metadata["Language"] = lcode
                # db_po.merge(collector.pofile)
                db_po.save(target_file)
                logger.info("generated POFile %s" % target_file)
        except Exception as e:
            logger.exception(e)
