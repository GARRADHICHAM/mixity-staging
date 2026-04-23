from collections import defaultdict

from django.apps import apps
from django.core.management import BaseCommand

from scoring.models import Category, Question, QuestionSheet, SubCategory


class Command(BaseCommand):
    """
    This command remove unused question sheets (and orphan questions) from the database.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-unused-obsolete-sheets", action="store_true", default=False
        )

    def handle(self, *args, **options):
        """
        Remove orphan questions and categories.
        Optionnaly delete unused obsolete sheets
        """
        before = defaultdict(int)
        # Starting stats
        for model in apps.get_models():
            name = model.__name__
            before[name] = model.objects.all().count()
        # Deleting obsolete sheets
        if options["delete_unused_obsolete_sheets"]:
            print("\n===== Deleting unused obsolete sheets =====")
            current_sheets = dict()
            unused_sheets = set()
            for sheet in QuestionSheet.objects.all().order_by("-version"):
                nb_evals = sheet.evaluations.count()
                if (sheet.year, sheet.type) not in current_sheets:
                    current_sheets[sheet.year, sheet.type] = sheet
                    continue
                elif nb_evals == 0:
                    unused_sheets.add(sheet)
                assert current_sheets[sheet.year, sheet.type].version > sheet.version
            for sheet in unused_sheets:
                last_version = current_sheets[sheet.year, sheet.type].version
                print(
                    f" * {sheet.year} - {sheet.type.name:40} - v{sheet.version:.1f} (last version: {last_version})"
                )
                sheet.delete()
        # Infos
        print("\n===== Deleting unused obsolete questions =====")
        for sheet in QuestionSheet.objects.all().order_by("year", "type", "version"):
            nb_evals = sheet.evaluations.count()
            print(
                f" * {sheet.year} - {sheet.type.name:40} - v{sheet.version:.1f} ({nb_evals} evaluations)"
            )
        # Cleaning questions ans categories
        for question in Question.objects.all():
            if question.sheets.count() == 0:
                question.delete()
        # Ending stats
        print("\n===== Database models stats =====")
        all_models = sorted(apps.get_models(), key=lambda m: m.__name__)
        total_rows = 0
        for model in all_models:
            name = model.__name__
            count = model.objects.all().count()
            total_rows += count
            diff = count - before[name]
            if diff == 0:
                diff = ""
            else:
                sign = "+" if diff > 0 else ""
                diff = f"({sign}{diff})"
            print(f" * {name} rows: {count} {diff}")
        print(f"\nTotal: {total_rows}")
