import logging
import math
import time
from io import StringIO, BytesIO
from typing import List, Union

from django.conf import settings
import pandas as pd
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django_countries import countries
from pandas import DataFrame

from accounts.vocabularies import WRONG_CSV, TOO_MANY_COLLABORATORS
from mixity.services.namsor.models import NamsorEthnicity
from mixity.settings import NAMSOR_CONFIDENCE_LIMIT
from scoring.models import Evaluation, CollaboratorsStatistics, ZoneStatistics
from django.utils.translation import ugettext_lazy as _

import requests


def split_dataframe(df: DataFrame, limit) -> List[DataFrame]:
    """
    Method to split a dataframe into multiple
    uniform dataframes with a maximum number of rows equal to 'limit'
    """
    number_of_df = math.ceil(len(df.index) / limit)
    elements_per_df = math.ceil(len(df.index) / number_of_df)
    dfs = [
        df.iloc[index * elements_per_df : (index + 1) * elements_per_df, :]
        for index in range(0, number_of_df)
    ]
    return dfs


class NamsorException(Exception):
    pass


class NamsorApiException(Exception):
    pass


class Namsor:
    _instance = None
    _ethnicity_choices = None
    _regions = None
    LIMIT = 100  # 100 names are allowed per request
    CREDITS_PER_ACTION = {"world": 20, "us": 10}

    def __init__(self):
        self.url = "https://v2.namsor.com/NamSorAPIv2/api2/json/"

    # Ethnicity choices are fixed (at least between deployments) so we cache a dictionary of all ethnicities
    @classmethod
    def get_ethnicity_choices(cls):
        if cls._ethnicity_choices is None:
            cls._ethnicity_choices = {
                n.key: n
                for n in NamsorEthnicity.objects.select_related("country").all()
            }
        return cls._ethnicity_choices

    @classmethod
    def get_regions(cls):
        if cls._regions is None:
            cls._regions = [
                a["region"] for a in NamsorEthnicity.objects.values("region").distinct()
            ]
        return cls._regions

    def get_usage(self):
        try:
            if not settings.NAMSOR_API_KEY:
                return {"error": "Missing API key"}

            url = self.url + "apiUsage"
            headers = {
                "X-API-KEY": settings.NAMSOR_API_KEY,
                "Accept": "application/json",
            }
            response = requests.request("GET", url, headers=headers)

            if response.status_code != 200:
                return {
                    "error": f"Request failed with status code: {response.status_code}, content: {response.text}"
                }

            try:
                data = response.json()
            except ValueError as e:
                return {
                    "error": f"Invalid JSON reponse: {str(e)}, response content: {response.text}"
                }

            billing_data = data.get("billingPeriod", {})
            billing_data.pop("apiKey", None)
            return billing_data

        except Exception as e:
            return {"error": str(e)}

    def verify_content(self, df: DataFrame, evaluation: Evaluation) -> tuple:
        if len(df.columns) < 2 or len(df.columns) > 3:
            return (False, _("Le fichier n'a pas le bon nombre de colonnes, une virgule a peut être été oubliée dans une case"))

        if len(df.index) > (
            evaluation.ethnicity_limit_per_file
            or (2 * evaluation.get_workforce_from_evaluation)
        ):
            return (False, _(TOO_MANY_COLLABORATORS))

        status = ""

        individuals = []
        for i in range(len(df.index)):
            if df.loc[i]["country_iso2"] and df.loc[i]["country_iso2"] not in countries:
                status += "/" + _(
                    f"Le pays de résidence à la ligne {i + 1} n'est pas valide"
                )

            if not df.loc[i]["first_name"]:
                status += "/" + _(
                    f"Il manque un prénom à la ligne {i + 1}"
                )

            if not df.loc[i]["last_name"]:
                status += "/" + _(
                    f"Il manque un nom de famille à la ligne {i + 1}"
                )

            if (
                str(df.loc[i]["first_name"]).lower(),
                str(df.loc[i]["last_name"]).lower(),
                str(df.loc[i]["country_iso2"]).lower(),
            ) in individuals:
                status += "/" + _(
                    f"Une personne apparait deux fois dans le fichier, la deuxième occurence est à la ligne {i + 1}"
                )

            individuals.append(
                (
                    str(df.loc[i]["first_name"]).lower(),
                    str(df.loc[i]["last_name"]).lower(),
                    str(df.loc[i]["country_iso2"]).lower(),
                )
            )

        if status == "":
            return (True, _("La structure du fichier csv est bonne"))
        
        if status.count('/') == 1:
            status = "Le fichier contient une erreur" + status
        else:
            status = "Le fichier contient quelques erreurs" + status

        return (False, status)

    def compute_ethnicity_from_csv(
        self,
        csv: str,
        evaluation: Evaluation,
        separator: str,
        header: bool,
        csv_type: str,
    ):
        """
        Main method to compute data from CSV.
        csv: CSV file content as string (Name, Surname, Country)
        separator: csv separator (, in most cases)
        header: if first line of file is a header or not
        csv_type: interns, ... Correspond to TYPE_CHOICES (vocabularies)
        """
        CollaboratorsStatistics.objects.filter(
            evaluation=evaluation, type=csv_type
        ).delete()
        collaborator_statistics = CollaboratorsStatistics.objects.create(
            evaluation=evaluation, type=csv_type, status="processing"
        )
        columns = ["first_name", "last_name", "country_iso2"]
        try:
            if not header:
                first_line_count = csv.split("\n")[0].count(separator)
                if first_line_count < 1 or first_line_count > 2:
                    raise NamsorException(
                        _("Le fichier n'a pas le bon nombre de colonnes, une virgule a peut être été oubliée dans une case")
                    )
                csv = separator.join(columns) + "\n" + csv
            df: DataFrame = pd.read_csv(
                BytesIO(csv.encode("utf-8")),
                sep=separator,
                header=0,
                keep_default_na=False,
            )

            for i in range(min(len(columns), len(df.columns.values))):
                df.columns.values[i] = columns[i]

            is_valid, message = self.verify_content(df, evaluation)
            if not is_valid:
                raise NamsorException(message)

            tags = list(
                filter(
                    lambda x: x in countries,
                    [tag.name.upper() for tag in evaluation.tags.only("name")],
                )
            )
            default_country = (not len(tags) == 0) and tags[0] or ""

            df = df.sample(frac=1).reset_index(
                drop=True
            )  # We randomize the order of collaborators to prevent any issue in case of security breach
            if default_country != "US":
                results = self.compute_name_diaspora_from_dataframe(df, default_country)
                scope = "world"
            else:
                results = self.compute_us_ethnicity_from_dataframe(df, default_country)

                results = results.rename(
                    columns={
                        "raceEthnicity": "ethnicity",
                        "raceEthnicityAlt": "ethnicityAlt",
                    }
                )
                scope = "us"

            collaborator_statistics.statistics = self.aggregate_data(
                results, scope, evaluation
            )
            collaborator_statistics.status = "finished"
        except pd.errors.ParserError as e:
            collaborator_statistics.can_delete = True
            collaborator_statistics.status = _("Le fichier CSV est invalide")
        except NamsorException as e:
            collaborator_statistics.can_delete = True
            collaborator_statistics.status = e
        except NamsorApiException as e:
            collaborator_statistics.can_delete = (
                False  # Credits may have been used so we block the access
            )
            collaborator_statistics.status = e
        except Exception as e:
            logging.exception(e)
            collaborator_statistics.can_delete = (
                False  # Credits may have been used so we block the access
            )
            collaborator_statistics.status = _(
                "Une erreur inconnue est survenue, notre équipe technique a été informée. "
                "Nous vous recontacterons prochainement."
            )
        collaborator_statistics.save()
        return collaborator_statistics

    def aggregate_data(
        self, df: DataFrame, zone: str, evaluation: Evaluation
    ) -> ZoneStatistics:
        # We separate results that are relevant and not relevant.
        # For each name, if the probability of accuracy is less than the value we set in the settings, we ignore the value
        unprocessed_data = df[df["probabilityCalibrated"] < NAMSOR_CONFIDENCE_LIMIT]
        processed_data = df[df["probabilityCalibrated"] >= NAMSOR_CONFIDENCE_LIMIT]
        computed_data = processed_data["ethnicity"].value_counts().to_dict()
        amount_of_unknown = len(unprocessed_data.index)
        if amount_of_unknown > 0:
            computed_data["Unknown"] = (
                amount_of_unknown  # Any ignored value's ethnicity is considered as unknown
            )
        computed_data = [
            {"name": k, "value": v}
            for k, v in sorted(
                computed_data.items(), key=lambda item: item[1], reverse=True
            )
        ]  # we store the ethnicities sorted by frequency
        statistics = ZoneStatistics(
            processed_collaborators=len(processed_data.index),
            unprocessed_collaborators=len(unprocessed_data.index),
            confidence=processed_data["probabilityCalibrated"].mean(),
            median=processed_data["probabilityCalibrated"].median(),
            computed_data=computed_data,
            credits_used=len(df.index) * self.CREDITS_PER_ACTION[zone],
        )
        statistics.raw_data.save(
            f"{evaluation.__str__()}_{zone}_data_{get_random_string(length=64)}"[:100]
            + ".csv",
            ContentFile(df.to_csv()),
        )
        statistics.save()
        return statistics

    @staticmethod
    def format_dataframe(df: DataFrame, default_country: str) -> dict:
        batch = {"personalNames": []}
        for _, row in df.iterrows():
            if not "country_iso2" in row or row["country_iso2"] == "":
                row["country_iso2"] = default_country
            batch["personalNames"].append(
                {
                    "firstName": row["first_name"],
                    "lastName": row["last_name"],
                    "countryIso2": row["country_iso2"],
                }
            )
        return batch

    @staticmethod
    def filter_data(
        data: dict,
        attributes: tuple,
    ):
        return [
            {attr: row[attr] for attr in attributes} for row in data["personalNames"]
        ]

    def compute_name_diaspora_from_dataframe(
        self, initial_df: DataFrame, default_country: str
    ) -> Union[DataFrame, None]:
        dfs = split_dataframe(initial_df, self.LIMIT)
        result_dfs = []
        for df in dfs:
            payload = self.format_dataframe(df, default_country)
            try:
                headers = {
                    "X-API-KEY": settings.NAMSOR_API_KEY,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
                url = self.url + "diasporaBatch"

                response = requests.request("POST", url, json=payload, headers=headers)

                if response.status_code != 200:
                    raise Exception(
                        f"Request failed with status code: {response.status_code}"
                    )

                try:
                    data = response.json()
                except ValueError as e:
                    raise Exception(
                        f"Invalid JSON reponse: {str(e)}, response content: {response.text}"
                    )

                result_df = pd.DataFrame(
                    self.filter_data(
                        data,
                        (
                            "score",
                            "probabilityCalibrated",
                            "probabilityAltCalibrated",
                            "ethnicity",
                            "ethnicityAlt",
                            "countryIso2",
                        ),
                    )
                )
                result_dfs.append(result_df)
            except Exception as e:
                logging.exception(e)
                raise NamsorApiException(
                    _(
                        "Une erreur avec notre service partenaire est survenue, notre équipe technique a été informé. "
                        "Nous vous recontacterons prochainement."
                    )
                )
        return pd.concat(result_dfs)

    def compute_us_ethnicity_from_dataframe(
        self, initial_df: DataFrame, default_country: str
    ) -> Union[DataFrame, None]:
        dfs = split_dataframe(initial_df, self.LIMIT)
        result_dfs = []
        for df in dfs:
            payload = self.format_dataframe(df, default_country)
            try:
                headers = {
                    "X-API-KEY": settings.NAMSOR_API_KEY,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
                url = self.url + "usRaceEthnicityBatch"

                response = requests.request("POST", url, json=payload, headers=headers)

                if response.status_code != 200:
                    raise Exception(
                        f"Request failed with status code: {response.status_code}"
                    )

                try:
                    data = response.json()
                except ValueError as e:
                    raise Exception(
                        f"Invalid JSON reponse: {str(e)}, response content: {response.text}"
                    )

                result_df = pd.DataFrame(
                    self.filter_data(
                        data,
                        (
                            "score",
                            "probabilityCalibrated",
                            "probabilityAltCalibrated",
                            "raceEthnicity",
                            "raceEthnicityAlt",
                        ),
                    )
                )
                result_dfs.append(result_df)
            except Exception as e:
                logging.exception(e)
                raise NamsorApiException(
                    _(
                        "Une erreur avec notre service partenaire est survenue, notre équipe technique a été informé. "
                        "Nous vous recontacterons prochainement."
                    )
                )
        return pd.concat(result_dfs)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Namsor()
        return cls._instance
