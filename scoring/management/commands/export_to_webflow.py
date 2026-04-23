from django.core.management.base import BaseCommand
from django.conf import settings
from scoring.models import Evaluation
import requests
import uuid


class Command(BaseCommand):
    help = "export all evaluations data to webflow"

    def delete_item(self, item_id, is_live=False):
        url = (
            "https://api.webflow.com/v2/collections/"
            + settings.WEBFLOW_COLLECTION_ID
            + "/items/"
            + item_id
            + ("/live" if is_live else "")
        )
        headers = {
            "authorization": "Bearer " + settings.WEBFLOW_API_KEY,
        }
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            return True
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to delete item {item_id}: {response.json()}")
            )
            return False

    def get_items_list(self, is_live=False):
        all_items = []
        url = (
            "https://api.webflow.com/v2/collections/"
            + settings.WEBFLOW_COLLECTION_ID
            + (
                "/items/live?cmsLocaleIds=&limit=100"
                if is_live
                else "/items/?cmsLocaleIds=&limit=100"
            )
        )
        headers = {
            "accept": "application/json",
            "authorization": "Bearer " + settings.WEBFLOW_API_KEY,
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json()["items"]
            all_items.extend(items)
            while (
                response.json()["pagination"]["limit"]
                * (response.json()["pagination"]["offset"] + 1)
                < response.json()["pagination"]["total"]
            ):
                url = (
                    "https://api.webflow.com/v2/collections/"
                    + settings.WEBFLOW_COLLECTION_ID
                    + "/items?cmsLocaleIds=&limit=100&offset="
                    + str(response.json()["pagination"]["offset"] + 1)
                )
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    items = response.json()["items"]
                    all_items.extend(items)
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to get items list: {response.json()}")
                    )
                    return None
            return all_items
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to get items list: {response.json()}")
            )
            return None

    def clean_collection(self):
        self.stdout.write(self.style.HTTP_INFO("Cleaning collection"))
        items = self.get_items_list()
        items_live = self.get_items_list(is_live=True)
        if len(items) == 0 and len(items_live) == 0:
            self.stdout.write(self.style.SUCCESS("Collection is already clean"))
            return
        if items:
            for item in items:
                if not self.delete_item(item["id"]):
                    return
        if items_live:
            for item in items_live:
                if not self.delete_item(item["id"], is_live=True):
                    return
        self.stdout.write(self.style.SUCCESS("Collection cleaned"))

    def get_all_evaluations_data(self):
        self.stdout.write(self.style.HTTP_INFO("Getting all evaluations data"))
        evaluations_data = []
        evaluations = Evaluation.objects.all()

        for evaluation in evaluations:
            if (
                evaluation.public_display == True
                and evaluation.footprint.name != ""
                and len(evaluation.scores_categories.all()) >= 6
            ):
                if evaluation.is_human:
                    eval_type = "human"
                elif evaluation.is_diag:
                    eval_type = "diag"
                else:
                    eval_type = ""
                gender = evaluation.scores_categories.filter(
                    category__slug="gender"
                ).first()
                disability = evaluation.scores_categories.filter(
                    category__slug="disability"
                ).first()
                cultural_diversity = evaluation.scores_categories.filter(
                    category__slug="cultural_diversity"
                ).first()
                generational_diversity = evaluation.scores_categories.filter(
                    category__slug="generational_diversity"
                ).first()
                lgbt = evaluation.scores_categories.filter(
                    category__slug="lgbt"
                ).first()
                evaluation_data = {
                    "data---1---couleur": gender.category.color if gender else None,
                    "data---2---couleur": (
                        disability.category.color if disability else None
                    ),
                    "data---3---couleur": (
                        cultural_diversity.category.color
                        if cultural_diversity
                        else None
                    ),
                    "data---4---couleur": (
                        generational_diversity.category.color
                        if generational_diversity
                        else None
                    ),
                    "data---5---couleur": lgbt.category.color if lgbt else None,
                    "data---1---chiffre": gender.display_value() if gender else None,
                    "data---2---chiffre": (
                        disability.display_value() if disability else None
                    ),
                    "data---3---chiffre": (
                        cultural_diversity.display_value()
                        if cultural_diversity
                        else None
                    ),
                    "data---4---chiffre": (
                        generational_diversity.display_value()
                        if generational_diversity
                        else None
                    ),
                    "data---5---chiffre": lgbt.display_value() if lgbt else None,
                    "name": evaluation.entity.name,
                    "nom-de-l-evaluation": evaluation.name,
                    "date": evaluation.created_date.strftime("%m-%y"),
                    "secteur": evaluation.entity.entity_level.structure.business_line.name,
                    "url-vers-le-site-du-client": evaluation.entity.entity_level.structure.website,
                    "url-vers-page-publique": "https://www.app.mixity.co/scoring/"
                    + evaluation.entity.slug
                    + "/"
                    + evaluation.display_version_slugified
                    + "/"
                    + eval_type,
                    "seo-title": "Empreinte de l'inclusion & diversité pour "
                    + evaluation.entity.name,
                    "seo-description": "Découvrez les principaux indicateurs diversité et inclusion chez notre client "
                    + evaluation.entity.name
                    + " pour un effectif de "
                    + str(evaluation.entity.workforce)
                    + " personnes au total",
                    "description-de-l-activite": evaluation.entity.entity_level.structure.description,
                    "annee-de-creation": str(
                        evaluation.entity.entity_level.structure.creation_year
                    ),
                    "effectif": str(evaluation.entity.entity_level.structure.workforce),
                    "temoignage": evaluation.entity.entity_level.structure.commitment,
                    "evaluation-type-3": evaluation.sheet.type.name,
                    "score-global": evaluation.get_global_score_delta,
                    "slug": evaluation.entity.slug,
                    "image": [
                        {
                            "url": evaluation.get_footprint_url(),
                        }
                    ],
                }
                evaluations_data.append(evaluation_data)
        self.stdout.write(self.style.SUCCESS("All evaluations data fetched"))
        return evaluations_data

    def update_collection(self, evaluations_data):
        self.stdout.write(self.style.HTTP_INFO("Updating collection"))
        url = (
            "https://api.webflow.com/v2/collections/"
            + settings.WEBFLOW_COLLECTION_ID
            + "/items"
        )
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer " + settings.WEBFLOW_API_KEY,
        }
        items_ids = []
        for evaluation_data in evaluations_data:
            data = {
                "fieldData": evaluation_data,
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 202:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Item {evaluation_data['name']} added successfully"
                    )
                )
                response_data = response.json()
                items_ids.append(response_data["id"])
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to add item {evaluation_data['name']}: {response.json()}"
                    )
                )
                return None
        self.stdout.write(self.style.SUCCESS("Collection updated"))
        return items_ids

    def publish_items(self, items_ids):
        self.stdout.write(self.style.HTTP_INFO("Publishing collection"))
        url = (
            "https://api.webflow.com/v2/collections/"
            + settings.WEBFLOW_COLLECTION_ID
            + "/items/publish"
        )
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer " + settings.WEBFLOW_API_KEY,
        }
        body = {"itemIds": items_ids}
        response = requests.post(url, headers=headers, json=body)
        response_data = response.json()
        if response.status_code == 202:
            self.stdout.write(self.style.SUCCESS("Collection published"))
            for error in response_data["errors"]:
                self.stdout.write(self.style.ERROR(error))
        else:
            self.stdout.write(self.style.ERROR("Failed to publish collection"))

    def handle(self, *args, **options):
        if settings.WEBFLOW_COLLECTION_ID == "":
            self.stdout.write(
                self.style.ERROR(
                    "WEBFLOW_COLLECTION_ID is not set in .env file (mixity/settings/.env)"
                )
            )
            return
        if settings.WEBFLOW_API_KEY == "":
            self.stdout.write(
                self.style.ERROR(
                    "WEBFLOW_API_KEY is not set in .env file (mixity/settings/.env)"
                )
            )
            return
        self.clean_collection()
        evaluations_data = self.get_all_evaluations_data()
        if (len(evaluations_data)) == 0:
            self.stdout.write(self.style.SUCCESS("No evaluations data to export"))
            return
        items_ids = self.update_collection(evaluations_data)
        if items_ids:
            self.publish_items(items_ids)
