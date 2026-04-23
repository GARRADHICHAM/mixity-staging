#!/usr/bin/env python

import csv
import os
import sys
from fast_i18n.translations import generate_translator


class CsvLoader:
    HEADER_ROW_POSITION = 1
    SEPARATOR = ","
    INNER_SEPARATOR = "|"

    def __init__(self):
        self.translation_count = 0
        self.translator = generate_translator(
            "GoogleTranslator",
            source_codes=("fr", "french"),
            target_codes=("spanish", "es"),
        )

    def find_column(self, headers, name, get_or_create=False):
        try:
            return headers.index(name), False
        except ValueError as e:
            if not get_or_create:
                raise e
            return len(headers), True

    def initialize_headers(self, origin, target):
        self.headers = self.rows[self.HEADER_ROW_POSITION]
        self.french_col, created = self.find_column(self.headers, origin)
        self.spanish_col, created = self.find_column(
            self.headers, target, get_or_create=True
        )
        if created:
            print(" ! Creating column %r" % target)
            self.headers.append(target)
            for i, row in enumerate(self.rows):
                if i == self.spanish_col:
                    # We already added the name
                    continue
                assert len(row) == self.spanish_col, (
                    f"Row {i} has invalid size (%r)" % row
                )
                row.append("")
        else:
            print(" ! Translating in column %i" % self.spanish_col)

    def load(self, filepath):
        if not filepath or not os.path.exists(filepath):
            raise Exception(f"Invalid input file '{filepath}'")
        print(" # Opening file %r" % filepath)
        with open(filepath, newline="") as csvfile:
            self.rows = list(csv.reader(csvfile, delimiter=self.SEPARATOR))

    def translate(self):
        for i in range(self.HEADER_ROW_POSITION + 1, len(self.rows)):
            row = self.rows[i]
            if row[self.spanish_col]:
                # Already translated
                continue
            try:
                print(" * Translating %r" % row[self.french_col])
                spanish = []
                for segment in row[self.french_col].split(self.INNER_SEPARATOR):
                    segment = segment.strip()
                    if not segment:
                        segment_es = r""
                    else:
                        segment_es = self.translator.translate(segment)
                        if segment[0].isupper() and not segment_es[0].isupper():
                            segment_es = segment_es[0].upper() + segment_es[1:]
                    spanish.append(segment_es)
                row[self.spanish_col] = self.INNER_SEPARATOR.join(spanish)
            except Exception as e:
                raise Exception(f"Fail to translate row {i}:\n%s" % str(e)) from e
            self.translation_count += 1

    def save(self, filepath):
        print(
            " # Saving %i translations in file %r" % (self.translation_count, filepath)
        )
        with open(filepath, "w", newline="\n") as csvfile:
            writer = csv.writer(csvfile, delimiter=self.SEPARATOR)
            for row in self.rows:
                writer.writerow(row)


if __name__ == "__main__":
    if len(sys.argv[1:]) != 3:
        print("Usage: autotranslate_csv_es.py filepath.csv column_fr column_es")
    else:
        here = os.path.dirname(os.path.realpath(__file__))
        os.chdir(here)
        filepath, origin_column, target_column = sys.argv[1:]
        form = CsvLoader()
        form.load(filepath)
        form.initialize_headers(origin_column, target_column)
        form.translate()
        form.save(filepath)
