import logging
from datetime import datetime
from json import JSONDecodeError

import requests
from django.conf import settings
from django.db.models import Q

from sirh.entities import Worker
from sirh.models import (
    ADPIndicator,
    ADPFieldMapping,
    ADPField,
    ADPIndicatorType,
    ADPStatus,
)


def incr_or_set(obj, field, key, value, increase=True):
    if not key in obj[field]:
        obj[field][key] = {}
    if not value in obj[field][key]:
        obj[field][key][value] = 0
    if increase:
        obj[field][key][value] += 1


def incr_or_set_remuneration(obj, field, key, gender, remuneration):
    if not key in obj[field]:
        obj[field][key] = {}
    if not f"count_{gender}" in obj[field][key]:
        obj[field][key][f"count_{gender}"] = 0
        obj[field][key][f"sum_{gender}"] = 0
    obj[field][key][f"count_{gender}"] += 1
    obj[field][key][f"sum_{gender}"] += remuneration


def incr_or_set_multiple(obj, field, key, value, sub_value):
    if not key in obj[field]:
        obj[field][key] = {}
    if not value in obj[field][key]:
        obj[field][key][value] = {}
    if sub_value not in obj[field][key][value]:
        obj[field][key][value][sub_value] = 0
    obj[field][key][value][sub_value] += 1


def compute_data_by_age(results):
    age_list = [int(key.split("_")[1]) for key in results.keys() if "None" not in key]
    age_list.sort()
    age_list = list(dict.fromkeys(age_list))
    global_value = 0

    def compute_gap(ages, is_global=False):
        sum = 0
        count = 0
        for age in ages:
            sum += results[f"sum_{age}"]
            count += results[f"count_{age}"]
        if sum == 0:
            return None
        if is_global:
            return sum / count
        else:
            return 100 * (global_value - (sum / count)) / min(global_value, sum / count)

    global_value = compute_gap(age_list, True)
    less_26 = compute_gap([i for i in age_list if i < 26])
    between_26_39 = compute_gap([i for i in age_list if (26 <= i < 40)])
    between_40_54 = compute_gap([i for i in age_list if (40 <= i < 55)])
    from_55 = compute_gap([i for i in age_list if i >= 55])
    return {
        "global": global_value,
        "less_26": less_26,
        "26_39": between_26_39,
        "40_54": between_40_54,
        "from_55": from_55,
    }


class ADPAPIException(Exception):
    pass


class APIConnection:
    ELEMENTS_PER_PAGE = 20

    def __init__(self, client_id, client_secret):
        self.HOST = "https://api.eu.adp.com"
        login = self.login(client_id, client_secret)
        if login.status_code == 200:
            self.token = login.json()["access_token"]
        else:
            raise ADPAPIException(
                f"Issue connecting to ADP API {login.status_code} {login.text}"
            )
        pass

    def login(self, client_id, client_secret):
        return requests.post(
            f"https://accounts.eu.adp.com/auth/oauth/v2/token",
            cert=(
                settings.ADP_CERTIFICATE.name,
                settings.ADP_PRIVATE_KEY.name,
            ),
            verify=True,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
            timeout=30,
        )

    def get_workers(self, page):
        return requests.get(
            f"{self.HOST}/hr/v2/workers?$top={self.ELEMENTS_PER_PAGE}&$skip={(page - 1) * self.ELEMENTS_PER_PAGE}",
            cert=(
                settings.ADP_CERTIFICATE.name,
                settings.ADP_PRIVATE_KEY.name,
            ),
            verify=True,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30,
        )


class ADP:
    def __init__(self, client: APIConnection, entity=None, structure=None):
        self.structure = structure or entity.entity_level.structure
        self.entity = entity or self.structure.get_main_entity
        self.partial_indicators = (
            []
        )  # indicators that need to have previous data to be computed that haven't (ex : remuneration_indcrease need data from the previous year)
        self.processed_indicators = []
        self.unprocessed_indicator_types = []
        self.client = client
        self.indicators_to_create = []
        self.mappings_to_create = {}
        self.is_partial = False
        self.status_object = ADPStatus.objects.filter(
            Q(entity=self.entity) | Q(structure=self.structure)
        ).first()

    # Method where you will get and transform all data from the API.
    def gather_data(self):
        raise NotImplementedError("You need to implement this method in child class")


class ADPSoftwareService(ADP):
    # gather_data will create new elements but they are not yet pushed to database for the sake of optimization. bulk_create_elements adds every necessary information to the database
    def bulk_create_elements(self):
        ADPIndicator.objects.bulk_create(self.indicators_to_create)
        ADPFieldMapping.objects.bulk_create(self.mappings_to_create.values())
        self.status_object.processed_indicators.set(self.processed_indicators)
        self.status_object.partial_indicators.set(self.partial_indicators)
        self.status_object.unprocessed_indicator_types.set(
            self.unprocessed_indicator_types
        )
        self.status_object.save()


class ADPDecidium(ADPSoftwareService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indicator_types = {
            i.name: i
            for i in ADPIndicatorType.objects.filter(softwares__name="decidium")
        }

    def get_data(self, page=1):
        workers = self.client.get_workers(page).json()["workers"]
        # workers = requests.get(
        #     "https://raw.githubusercontent.com/marketplace-esi/postman-samples/master/decidium/Worker/workers-all-workers-http-200-response.json"
        # ).json()["workers"] # this is the big test sample from ADP
        return workers

    def gather_data(self):
        self.status_object.steps["gathering"] = {
            "status": "ongoing",
            "date": datetime.now().timestamp(),
        }
        self.status_object.save()
        page = 1
        success = True
        indicator_types = self.indicator_types.values()
        while True:
            try:
                is_exc = False
                workers = self.get_data(page)
            except JSONDecodeError:
                is_exc = False
                workers = None
            except Exception as e:
                workers = None
                is_exc = True
                print(
                    f"Unexpected exception on ADP for {self.entity} {self.structure} : {e}"
                )
                logging.exception(
                    f"Unexpected exception on ADP for {self.entity} {self.structure} : {e}"
                )
                self.status_object.steps["gathering"] = {
                    "status": "failed",
                    "date": datetime.now().timestamp(),
                }
                success = False
            if not workers:
                for indicator_type in indicator_types:
                    try:
                        getattr(self, f"get_{indicator_type.name}")(final=True)
                    except Exception as e:
                        print(f"{e}")
                        import traceback

                        self.is_partial = True
                        self.unprocessed_indicator_types.append(indicator_type)
                        traceback.print_exc()
                        logging.exception(f"{e}")
                if not is_exc:
                    # status is success if no error happened and if there are at least some processed or partial indicators
                    self.status_object.steps["gathering"] = {
                        "status": "success"
                        if len(self.processed_indicators) + len(self.partial_indicators)
                        > 0
                        else "failed",
                        "date": datetime.now().timestamp(),
                    }
                    self.status_object.last_updated = datetime.now()
                self.status_object.steps["processing"] = {
                    "status": "partial"
                    if self.is_partial or len(self.partial_indicators) > 0
                    else "success",
                    "date": datetime.now().timestamp(),
                }
                self.status_object.save()
                return success
            for indicator_type in indicator_types:
                try:
                    for (
                        worker
                    ) in (
                        workers
                    ):  # For each page, and for each indicator, we go through each worker which means each worker will be treated individually in each indicator function
                        getattr(self, f"get_{indicator_type.name}")(Worker(worker))
                except Exception as e:
                    print(f"{e}")
                    import traceback

                    traceback.print_exc()
                    logging.exception(f"{e}")

            page += 1

    """
        Age pyramid. Go to self.age_pyramid to see available filters. Every age found in the API is stored.
        Ex : To access all 55 years old of business unit "test", you'll have to access :
        age_pyramid["business_unit"]["test"][55]
        global filter represent non-filtered data. It has an attribute "all" which contains all ages like other
        filters.
    """

    def get_age_pyramid(self, worker=None, final=False):
        # do gender winke
        if not hasattr(self, "age_pyramid"):
            self.age_pyramid = {
                "global": {},
                "contract": {},
                "seniority": {},
                "business_unit": {},
                "job": {},
                "department": {},
                "classification": {},
            }
        if worker and worker.is_active():
            age = worker.get_age()
            gender = worker.get_gender()
            seniority = worker.get_seniority()
            assignment = worker.get_assignment()
            incr_or_set_multiple(self.age_pyramid, "global", "all", age, gender)
            incr_or_set_multiple(self.age_pyramid, "seniority", seniority, age, gender)
            if assignment:
                job = worker.get_job()
                incr_or_set_multiple(self.age_pyramid, "job", job, age, gender)
                classification = worker.get_classification()
                contract = worker.get_contract_type()
                if classification:
                    incr_or_set_multiple(
                        self.age_pyramid, "classification", classification, age, gender
                    )
                if worker.department:
                    incr_or_set_multiple(
                        self.age_pyramid, "department", worker.department, age, gender
                    )
                if worker.business_unit:
                    incr_or_set_multiple(
                        self.age_pyramid,
                        "business_unit",
                        worker.business_unit,
                        age,
                        gender,
                    )
                if contract:
                    incr_or_set_multiple(
                        self.age_pyramid,
                        "contract",
                        contract,
                        age,
                        gender,
                    )
        if (
            final
            and self.indicator_types["age_pyramid"]
            not in self.unprocessed_indicator_types
        ):
            final_indicator = {
                "data": self.age_pyramid,
            }
            self.indicators_to_create.append(
                ADPIndicator(
                    entity=self.entity,
                    data=final_indicator,
                    type=self.indicator_types["age_pyramid"],
                )
            )
            self.processed_indicators.append(self.indicators_to_create[-1])

    # we store the amount of employees per gender and per filter, not the percentage. Percentage will be computed on the go
    def get_gender_repartition(self, worker=None, final=False):
        if not hasattr(self, "gender_repartition"):
            self.gender_repartition = {
                "global": {},
                "age": {},
                "contract": {},
                "seniority": {},
                "business_unit": {},
                "job": {},
                "department": {},
                "classification": {},
            }
        if worker and worker.is_active():
            gender = worker.get_gender()
            age = worker.get_age()
            seniority = worker.get_seniority()
            assignment = worker.get_assignment()
            incr_or_set(self.gender_repartition, "global", "all", gender)
            incr_or_set(self.gender_repartition, "age", age, gender)
            incr_or_set(self.gender_repartition, "seniority", seniority, gender)

            if assignment:
                job = worker.get_job()
                incr_or_set(self.gender_repartition, "job", job, gender)
                classification = worker.get_classification()
                contract = worker.get_contract_type()
                if classification:
                    incr_or_set(
                        self.gender_repartition,
                        "classification",
                        classification,
                        gender,
                    )
                if worker.department:
                    incr_or_set(
                        self.gender_repartition, "department", worker.department, gender
                    )
                if worker.business_unit:
                    incr_or_set(
                        self.gender_repartition,
                        "business_unit",
                        worker.business_unit,
                        gender,
                    )
                if contract:
                    incr_or_set(
                        self.gender_repartition,
                        "contract",
                        contract,
                        gender,
                    )
        if (
            final
            and self.indicator_types["gender_repartition"]
            not in self.unprocessed_indicator_types
        ):
            final_indicator = {
                "data": self.gender_repartition,
            }
            self.indicators_to_create.append(
                ADPIndicator(
                    entity=self.entity,
                    data=final_indicator,
                    type=self.indicator_types["gender_repartition"],
                )
            )
            self.processed_indicators.append(self.indicators_to_create[-1])

    """
        Doesn't compute the gender paygap directly. Contains for each filter the sum of remuneration for each gender
        and the amount of people per gender (count_X and sum_X where X is the gender. Genders should be M & F)
    """

    def get_gender_paygap(self, worker=None, final=False):
        return self.get_paygap_by("gender_paygap", "gender", "age", worker, final)

    def get_age_paygap(self, worker=None, final=False):
        return self.get_paygap_by("age_paygap", "age", "gender", worker, final)

    def get_paygap_by(
        self,
        indicator_name,
        main_variable,
        secondary_variable,
        worker=None,
        final=False,
    ):
        if not hasattr(self, "paygap"):
            self.paygap = {}

        if not main_variable in self.paygap:
            self.paygap[main_variable] = {
                "global": {},
                secondary_variable: {},
                "contract": {},
                "job": {},
                "seniority": {},
                "business_unit": {},
                "department": {},
                "classification": {},
            }
        if worker and worker.is_active():
            remuneration = worker.get_base_remuneration()
            gender = worker.get_gender()
            age = worker.get_age()
            seniority = worker.get_seniority()
            classification = worker.get_classification()
            contract = worker.get_contract_type()
            job = worker.get_job()

            assignment = worker.get_assignment()
            main_value = age if main_variable == "age" else gender
            secondary_value = gender if main_variable == "age" else age
            if assignment and remuneration is not None:
                incr_or_set_remuneration(
                    self.paygap[main_variable],
                    "global",
                    "all",
                    main_value,
                    remuneration,
                )
                incr_or_set_remuneration(
                    self.paygap[main_variable],
                    secondary_variable,
                    main_value,
                    secondary_value,
                    remuneration,
                )
                incr_or_set_remuneration(
                    self.paygap[main_variable],
                    "seniority",
                    seniority,
                    main_value,
                    remuneration,
                )
                if worker.department:
                    incr_or_set_remuneration(
                        self.paygap[main_variable],
                        "department",
                        worker.department,
                        main_value,
                        remuneration,
                    )
                if worker.business_unit:
                    incr_or_set_remuneration(
                        self.paygap[main_variable],
                        "business_unit",
                        worker.business_unit,
                        main_value,
                        remuneration,
                    )
                if classification:
                    incr_or_set_remuneration(
                        self.paygap[main_variable],
                        "classification",
                        classification,
                        main_value,
                        remuneration,
                    )
                if job:
                    incr_or_set_remuneration(
                        self.paygap[main_variable],
                        "job",
                        job,
                        main_value,
                        remuneration,
                    )
                if contract:
                    incr_or_set_remuneration(
                        self.paygap[main_variable],
                        "contract",
                        contract,
                        main_value,
                        remuneration,
                    )
        if final and (
            self.indicator_types[indicator_name] not in self.unprocessed_indicator_types
        ):
            # TODO : compute paygap
            final_indicator = {
                "data": self.paygap[main_variable],
                "computed_values": {"global": None},
            }
            if "all" in self.paygap[main_variable]["global"]:
                data = self.paygap[main_variable]["global"]["all"]
                if main_variable == "gender":
                    final_indicator["computed_values"]["global"] = (
                        100
                        * abs(
                            (data.get("sum_M", 0) / data.get("count_M", 1))
                            - (data.get("sum_F", 0) / data.get("count_F", 1))
                        )
                        / (data.get("sum_M", 0) / data.get("count_M", 1))
                    )
                elif main_variable == "age":
                    final_indicator["computed_values"]["global"] = compute_data_by_age(
                        data
                    )
            if (
                self.indicator_types[indicator_name]
                not in self.unprocessed_indicator_types
            ):
                self.indicators_to_create.append(
                    ADPIndicator(
                        entity=self.entity,
                        data=final_indicator,
                        type=self.indicator_types[indicator_name],
                    )
                )
                self.processed_indicators.append(self.indicators_to_create[-1])

    """
    Doesn't compute remuneration increase directly. It stores current remuneration per worker. Remuneration increase is
    computed in comparison of a previous gathering of the data. When computed, it'll store the sum of remuneration increase
    percentage per gender and the amount of employees per gender.
    To compute the remuneration increase gap, you'll need to do (sum_M / count_M) - (sum_F / count_F)
    """

    def get_remuneration_increase_gender(self, worker=None, final=False):
        return self.get_remuneration_increase_by(
            "remuneration_increase_gender", "gender", "age", worker, final
        )

    def get_remuneration_increase_age(self, worker=None, final=False):
        return self.get_remuneration_increase_by(
            "remuneration_increase_age", "age", "gender", worker, final
        )

    def get_remuneration_increase_by(
        self,
        indicator_name,
        main_variable,
        secondary_variable,
        worker=None,
        final=False,
    ):
        if not hasattr(self, "remuneration_increase"):
            self.remuneration_increase = {}
        if not hasattr(self, "remuneration_increase_indicator"):
            self.remuneration_increase_indicator = {}

        if not main_variable in self.remuneration_increase:
            self.remuneration_increase[main_variable] = {"workers": {}}
        if not main_variable in self.remuneration_increase_indicator:
            self.remuneration_increase_indicator[main_variable] = {
                "business_unit": {},
                "department": {},
                "classification": {},
                "seniority": {},
                secondary_variable: {},
                "global": {},
            }
        if worker and worker.is_active():
            remuneration = worker.get_base_remuneration()
            gender = worker.get_gender()
            age = worker.get_age()
            seniority = worker.get_seniority()
            classification = worker.get_classification()
            worker_id = worker.get_id()
            worker_obj = {
                "remuneration": remuneration,
                "gender": gender,
                "age": age,
                "seniority": seniority,
                "classification": classification,
                "id": worker_id,
                "business_unit": worker.business_unit,
                "department": worker.department,
                "job": worker.get_job(),
            }
            self.remuneration_increase[main_variable]["workers"][worker_id] = worker_obj

        if (
            final
            and self.indicator_types[indicator_name]
            not in self.unprocessed_indicator_types
        ):
            previous_indicator = ADPIndicator.objects.filter(
                entity=self.entity,
                type__name=indicator_name,
                date__lte=datetime(datetime.now().year, 1, 1),
            ).last()
            final_indicator = {
                "data": None,
                "additional_data": self.remuneration_increase[main_variable],
                "computed_values": {"global": None},
            }
            if previous_indicator:
                previous_workers = previous_indicator.data["additional_data"]["workers"]
                for worker_id, worker in previous_workers.items():
                    if (
                        worker["remuneration"]
                        and worker_id
                        in self.remuneration_increase[main_variable]["workers"]
                    ):
                        remuneration_increase = (
                            100
                            * (
                                self.remuneration_increase[main_variable]["workers"][
                                    worker_id
                                ]["remuneration"]
                                - worker["remuneration"]
                            )
                            / worker["remuneration"]
                        )
                        incr_or_set_remuneration(
                            self.remuneration_increase_indicator[main_variable],
                            "global",
                            "all",
                            worker[main_variable],
                            remuneration_increase,
                        )
                        incr_or_set_remuneration(
                            self.remuneration_increase_indicator[main_variable],
                            secondary_variable,
                            worker[secondary_variable],
                            worker[main_variable],
                            remuneration_increase,
                        )
                        incr_or_set_remuneration(
                            self.remuneration_increase_indicator[main_variable],
                            "business_unit",
                            worker["business_unit"],
                            worker[main_variable],
                            remuneration_increase,
                        )
                        incr_or_set_remuneration(
                            self.remuneration_increase_indicator[main_variable],
                            "seniority",
                            worker["seniority"],
                            worker[main_variable],
                            remuneration_increase,
                        )
                        incr_or_set_remuneration(
                            self.remuneration_increase_indicator[main_variable],
                            "department",
                            worker["department"],
                            worker[main_variable],
                            remuneration_increase,
                        )
                        incr_or_set_remuneration(
                            self.remuneration_increase_indicator[main_variable],
                            "classification",
                            worker["classification"],
                            worker[main_variable],
                            remuneration_increase,
                        )
                global_results = self.remuneration_increase_indicator[main_variable][
                    "global"
                ]["all"]
                if main_variable == "gender":
                    final_indicator["computed_values"]["global"] = abs(
                        global_results.get("sum_M", 0)
                        / global_results.get("count_M", 1)
                        - global_results.get("sum_F", 0)
                        / global_results.get("count_F", 1)
                    )
                elif main_variable == "age":
                    final_indicator["computed_values"]["global"] = compute_data_by_age(
                        global_results
                    )
                final_indicator["data"] = self.remuneration_increase_indicator[
                    main_variable
                ]
                partial = False
            else:
                partial = True

            self.indicators_to_create.append(
                ADPIndicator(
                    entity=self.entity,
                    data=final_indicator,
                    type=self.indicator_types[indicator_name],
                )
            )
            if partial:
                self.partial_indicators.append(self.indicators_to_create[-1])
            else:
                self.processed_indicators.append(self.indicators_to_create[-1])

    """
    this method will use the workers data from the remuneration_increase indicator. We need previous data that are at least 1 year old in order to compute the promotion rate
    """

    def get_promotion_gender(self, worker=None, final=False):
        return self.get_promotion_by("promotion_gender", "gender", "age", worker, final)

    def get_promotion_age(self, worker=None, final=False):
        return self.get_promotion_by("promotion_age", "age", "gender", worker, final)

    def get_promotion_by(
        self,
        indicator_name,
        main_variable,
        secondary_variable,
        worker=None,
        final=False,
    ):
        if (
            final
            and self.indicator_types[indicator_name]
            not in self.unprocessed_indicator_types
        ):
            previous_indicator = ADPIndicator.objects.filter(
                entity=self.entity,
                type__name=f"remuneration_increase_{main_variable}",
                date__lte=datetime(datetime.now().year, 1, 1),
            ).last()
            if previous_indicator:
                final_indicator = {
                    "data": {
                        "business_unit": {},
                        "department": {},
                        "classification": {},
                        "seniority": {},
                        secondary_variable: {},
                        "global": {},
                    },
                    "computed_values": {"global": None},
                }
                previous_workers = previous_indicator.data["additional_data"]["workers"]
                for worker_id, worker in previous_workers.items():
                    if (
                        worker["remuneration"]
                        and worker_id
                        in self.remuneration_increase[main_variable]["workers"]
                    ):
                        remuneration_increase = (
                            100
                            * (
                                self.remuneration_increase[main_variable]["workers"][
                                    worker_id
                                ]["remuneration"]
                                - worker["remuneration"]
                            )
                            / worker["remuneration"]
                        )
                        has_remuneration_increase = (
                            0
                            if (
                                remuneration_increase
                                < settings.ADP_MINIMUM_REMUNERATION_INCREASE
                            )
                            or worker["job"]
                            == self.remuneration_increase[main_variable]["workers"][
                                worker_id
                            ]["job"]
                            else 1
                        )
                        incr_or_set_remuneration(
                            final_indicator["data"],
                            "global",
                            "all",
                            worker[main_variable],
                            has_remuneration_increase,
                        )
                        incr_or_set_remuneration(
                            final_indicator["data"],
                            secondary_variable,
                            worker[secondary_variable],
                            worker[main_variable],
                            has_remuneration_increase,
                        )
                        incr_or_set_remuneration(
                            final_indicator["data"],
                            "business_unit",
                            worker["business_unit"],
                            worker[main_variable],
                            has_remuneration_increase,
                        )
                        incr_or_set_remuneration(
                            final_indicator["data"],
                            "seniority",
                            worker["seniority"],
                            worker[main_variable],
                            has_remuneration_increase,
                        )
                        incr_or_set_remuneration(
                            final_indicator["data"],
                            "department",
                            worker["department"],
                            worker[main_variable],
                            has_remuneration_increase,
                        )
                global_results = final_indicator["data"]["global"]["all"]
                if main_variable == "gender":
                    men = global_results.get("sum_M", 0) / global_results.get(
                        "count_M", 1
                    )
                    women = global_results.get("sum_F", 0) / global_results.get(
                        "count_F", 1
                    )
                    final_indicator["computed_values"]["global"] = (
                        100 * abs(men - women) / ((men + women) or 1)
                    )
                elif main_variable == "age":
                    final_indicator["computed_values"]["global"] = compute_data_by_age(
                        global_results
                    )
                self.indicators_to_create.append(
                    ADPIndicator(
                        entity=self.entity,
                        data=final_indicator,
                        type=self.indicator_types[f"promotion_{main_variable}"],
                    )
                )

                self.processed_indicators.append(self.indicators_to_create[-1])
            else:
                self.unprocessed_indicator_types.append(
                    self.indicator_types[indicator_name]
                )

    def get_hiring(self, worker=None, final=False):
        if not hasattr(self, "hiring"):
            self.hiring = {
                "global": {},
                "gender": {},
                "age": {},
                "contract": {},
                "job": {},
                "department": {},
                "business_unit": {},
                "classification": {},
                "seniority": {},
                "citizenship": {},
            }
        if worker:
            gender = worker.get_gender()
            age = worker.get_age()
            recruiting_year = worker.get_recruiting_year()
            citizenships = worker.get_worker_citizenships()
            incr_or_set(self.hiring, "global", "all", recruiting_year)
            incr_or_set(self.hiring, "age", age, recruiting_year)
            incr_or_set(self.hiring, "gender", gender, recruiting_year)
            contract = worker.get_contract_type()
            job = worker.get_job()
            seniority = worker.get_seniority()
            classification = worker.get_classification()
            if classification:
                incr_or_set(
                    self.hiring,
                    "classification",
                    classification,
                    recruiting_year,
                )
            if worker.business_unit:
                incr_or_set(
                    self.hiring,
                    "business_unit",
                    worker.business_unit,
                    recruiting_year,
                )
            if contract:
                incr_or_set(
                    self.hiring,
                    "contract",
                    contract,
                    recruiting_year,
                )
            if job:
                incr_or_set(
                    self.hiring,
                    "job",
                    job,
                    recruiting_year,
                )
            if worker.department:
                incr_or_set(
                    self.hiring,
                    "department",
                    worker.department,
                    recruiting_year,
                )
            if seniority:
                incr_or_set(
                    self.hiring,
                    "seniority",
                    seniority,
                    recruiting_year,
                )
            for citizenship in citizenships:
                incr_or_set(
                    self.hiring,
                    "citizenship",
                    citizenship,
                    recruiting_year,
                )

        if (
            final
            and self.indicator_types["hiring"] not in self.unprocessed_indicator_types
        ):
            self.hiring["workforce_per_year"] = self.turnover["workforce_per_year"]
            final_indicator = {
                "data": self.hiring,
            }
            self.indicators_to_create.append(
                ADPIndicator(
                    entity=self.entity,
                    data=final_indicator,
                    type=self.indicator_types["hiring"],
                )
            )
            self.processed_indicators.append(self.indicators_to_create[-1])

    def get_exiting(self, worker=None, final=False):
        if not hasattr(self, "exiting"):
            self.exiting = {
                "global": {},
                "gender": {},
                "age": {},
                "contract": {},
                "job": {},
                "department": {},
                "business_unit": {},
                "classification": {},
                "seniority": {},
            }
        if worker:
            gender = worker.get_gender()
            age = worker.get_age()
            exiting_year = worker.get_exiting_year()
            if not exiting_year:
                return
            incr_or_set(self.exiting, "global", "all", exiting_year)
            incr_or_set(self.exiting, "age", age, exiting_year)
            incr_or_set(self.exiting, "gender", gender, exiting_year)
            contract = worker.get_contract_type()
            job = worker.get_job()
            seniority = worker.get_seniority()
            classification = worker.get_classification()
            if classification:
                incr_or_set(
                    self.exiting,
                    "classification",
                    classification,
                    exiting_year,
                )
            if worker.business_unit:
                incr_or_set(
                    self.exiting,
                    "business_unit",
                    worker.business_unit,
                    exiting_year,
                )
            if contract:
                incr_or_set(
                    self.exiting,
                    "contract",
                    contract,
                    exiting_year,
                )
            if job:
                incr_or_set(
                    self.exiting,
                    "job",
                    job,
                    exiting_year,
                )
            if worker.department:
                incr_or_set(
                    self.exiting,
                    "department",
                    worker.department,
                    exiting_year,
                )
            if seniority:
                incr_or_set(
                    self.exiting,
                    "seniority",
                    seniority,
                    exiting_year,
                )

        if (
            final
            and self.indicator_types["exiting"] not in self.unprocessed_indicator_types
        ):
            self.exiting["workforce_per_year"] = self.turnover["workforce_per_year"]
            final_indicator = {
                "data": self.exiting,
            }
            self.indicators_to_create.append(
                ADPIndicator(
                    entity=self.entity,
                    data=final_indicator,
                    type=self.indicator_types["exiting"],
                )
            )
            self.processed_indicators.append(self.indicators_to_create[-1])

    def get_citizenships(self, worker=None, final=False):
        if not hasattr(self, "citizenships"):
            self.citizenships = {
                "global": {},
                "gender": {},
                "age": {},
                "contract": {},
                "job": {},
                "department": {},
                "business_unit": {},
                "classification": {},
                "seniority": {},
            }
        if worker and worker.is_active():
            gender = worker.get_gender()
            age = worker.get_age()
            citizenships = worker.get_worker_citizenships()
            contract = worker.get_contract_type()
            job = worker.get_job()
            seniority = worker.get_seniority()
            # if worker has multiple citizenships (which is very rare), they will be counted multiple times
            for citizenship in citizenships:
                incr_or_set(self.citizenships, "global", "all", citizenship)
                incr_or_set(self.citizenships, "age", age, citizenship)
                incr_or_set(self.citizenships, "gender", gender, citizenship)
                classification = worker.get_classification()
                if classification:
                    incr_or_set(
                        self.citizenships,
                        "classification",
                        classification,
                        citizenship,
                    )
                if worker.business_unit:
                    incr_or_set(
                        self.citizenships,
                        "business_unit",
                        worker.business_unit,
                        citizenship,
                    )
                if contract:
                    incr_or_set(
                        self.citizenships,
                        "contract",
                        contract,
                        citizenship,
                    )
                if job:
                    incr_or_set(
                        self.citizenships,
                        "job",
                        job,
                        citizenship,
                    )
                if worker.department:
                    incr_or_set(
                        self.citizenships,
                        "department",
                        worker.department,
                        citizenship,
                    )
                if seniority:
                    incr_or_set(
                        self.citizenships,
                        "seniority",
                        seniority,
                        citizenship,
                    )

        if (
            final
            and self.indicator_types["citizenships"]
            not in self.unprocessed_indicator_types
        ):
            final_indicator = {
                "data": self.citizenships,
            }
            self.indicators_to_create.append(
                ADPIndicator(
                    entity=self.entity,
                    data=final_indicator,
                    type=self.indicator_types["citizenships"],
                )
            )
            self.processed_indicators.append(self.indicators_to_create[-1])

    """
        Doesn't compute turnover directly. Stores amount of  hired/exited employees per year and per filter.
        You need to compute the turnover in the indicator itself
        [( Nombre de départs sur l'année N + nombre d'arrivées sur l'année N) / 2 ] / Effectif au 1er janvier de l'année N

        Workforce per filter is stored in the workforce_per_year key of the JSON (same structure as base data)
    """

    def get_turnover(self, worker=None, final=False):
        if not hasattr(self, "turnover"):
            self.turnover = {
                "global": {},
                "gender": {},
                "age": {},
                "contract": {},
                "job": {},
                "department": {},
                "seniority": {},
                "classification": {},
                "business_unit": {},
                "citizenship": {},
                "workforce_per_year": {
                    "global": {},
                    "gender": {},
                    "age": {},
                    "contract": {},
                    "job": {},
                    "department": {},
                    "seniority": {},
                    "classification": {},
                    "business_unit": {},
                    "citizenship": {},
                },
            }
        if worker:
            gender = worker.get_gender()
            age = worker.get_age()
            exiting_year = worker.get_exiting_year()
            recruiting_year = worker.get_recruiting_year()
            if exiting_year:
                incr_or_set_multiple(
                    self.turnover, "global", "all", exiting_year, "exited"
                )
                incr_or_set_multiple(self.turnover, "age", age, exiting_year, "exited")
                incr_or_set_multiple(
                    self.turnover, "gender", gender, exiting_year, "exited"
                )
            incr_or_set_multiple(
                self.turnover, "global", "all", recruiting_year, "hired"
            )
            incr_or_set_multiple(self.turnover, "age", age, recruiting_year, "hired")
            incr_or_set_multiple(
                self.turnover, "gender", gender, recruiting_year, "hired"
            )
            classification = worker.get_classification()
            contract = worker.get_contract_type()
            job = worker.get_job()
            seniority = worker.get_seniority()
            if classification:
                incr_or_set_multiple(
                    self.turnover,
                    "classification",
                    classification,
                    recruiting_year,
                    "hired",
                )
                if exiting_year:
                    incr_or_set_multiple(
                        self.turnover,
                        "classification",
                        classification,
                        exiting_year,
                        "exited",
                    )
            if worker.business_unit:
                incr_or_set_multiple(
                    self.turnover,
                    "business_unit",
                    worker.business_unit,
                    recruiting_year,
                    "hired",
                )
                if exiting_year:
                    incr_or_set_multiple(
                        self.turnover,
                        "business_unit",
                        worker.business_unit,
                        exiting_year,
                        "exited",
                    )
            if contract:
                incr_or_set_multiple(
                    self.turnover,
                    "contract",
                    contract,
                    recruiting_year,
                    "hired",
                )
                if exiting_year:
                    incr_or_set_multiple(
                        self.turnover,
                        "contract",
                        contract,
                        exiting_year,
                        "exited",
                    )
            if job:
                incr_or_set_multiple(
                    self.turnover,
                    "job",
                    job,
                    recruiting_year,
                    "hired",
                )
                if exiting_year:
                    incr_or_set_multiple(
                        self.turnover,
                        "job",
                        job,
                        exiting_year,
                        "exited",
                    )
            if worker.department:
                incr_or_set_multiple(
                    self.turnover,
                    "department",
                    worker.department,
                    recruiting_year,
                    "hired",
                )
                if exiting_year:
                    incr_or_set_multiple(
                        self.turnover,
                        "department",
                        worker.department,
                        exiting_year,
                        "exited",
                    )
            if seniority:
                incr_or_set_multiple(
                    self.turnover,
                    "seniority",
                    seniority,
                    recruiting_year,
                    "hired",
                )
                if exiting_year:
                    incr_or_set_multiple(
                        self.turnover,
                        "seniority",
                        seniority,
                        exiting_year,
                        "exited",
                    )
            citizenships = worker.get_worker_citizenships()
            if citizenships:
                for citizenship in citizenships:
                    incr_or_set_multiple(
                        self.turnover,
                        "citizenship",
                        citizenship,
                        recruiting_year,
                        "hired",
                    )
                    if exiting_year:
                        incr_or_set_multiple(
                            self.turnover,
                            "citizenship",
                            citizenship,
                            exiting_year,
                            "exited",
                        )

            # we increment the workforce by 1 for each year the worker has been present
            for i in range(recruiting_year, (exiting_year or datetime.now().year) + 1):
                will_increase = True
                if i == exiting_year:
                    will_increase = False
                incr_or_set(
                    self.turnover["workforce_per_year"],
                    "global",
                    "all",
                    i,
                    will_increase,
                )
                incr_or_set(
                    self.turnover["workforce_per_year"], "age", age, i, will_increase
                )
                incr_or_set(
                    self.turnover["workforce_per_year"],
                    "gender",
                    gender,
                    i,
                    will_increase,
                )
                if classification:
                    incr_or_set(
                        self.turnover["workforce_per_year"],
                        "classification",
                        classification,
                        i,
                        will_increase,
                    )
                if contract:
                    incr_or_set(
                        self.turnover["workforce_per_year"],
                        "contract",
                        contract,
                        i,
                        will_increase,
                    )
                if job:
                    incr_or_set(
                        self.turnover["workforce_per_year"],
                        "job",
                        job,
                        i,
                        will_increase,
                    )
                if worker.department:
                    incr_or_set(
                        self.turnover["workforce_per_year"],
                        "department",
                        worker.department,
                        i,
                        will_increase,
                    )
                if seniority:
                    incr_or_set(
                        self.turnover["workforce_per_year"],
                        "seniority",
                        seniority,
                        i,
                        will_increase,
                    )
                if worker.business_unit:
                    incr_or_set(
                        self.turnover["workforce_per_year"],
                        "business_unit",
                        worker.business_unit,
                        i,
                        will_increase,
                    )
                if citizenships:
                    for citizenship in citizenships:
                        incr_or_set(
                            self.turnover["workforce_per_year"],
                            "citizenship",
                            citizenship,
                            i,
                            will_increase,
                        )
                will_increase = True
        if (
            final
            and self.indicator_types["turnover"] not in self.unprocessed_indicator_types
        ):
            final_indicator = {
                "data": self.turnover,
                "computed_values": {"global": None},
            }
            # We compute the turnover for the overall company the past year. Can be useful if we want to mark the question
            if "all" in self.turnover["global"]:
                year = datetime.now().year - 1
                if year in self.turnover["global"]["all"]:
                    y_data = self.turnover["global"]["all"][year]
                    final_indicator["computed_values"]["global"] = (
                        100
                        * ((y_data.get("hired", 0) + y_data.get("exited", 0)) / 2)
                        / (
                            self.turnover["workforce_per_year"]["global"]["all"][
                                year - 1
                            ]
                            or 1
                        )
                    )
            self.indicators_to_create.append(
                ADPIndicator(
                    entity=self.entity,
                    data=final_indicator,
                    type=self.indicator_types["turnover"],
                )
            )
            self.processed_indicators.append(self.indicators_to_create[-1])


# This class helps to route to the correct software. Currently, we only have ADPDecidium but we'll probably have more in the future
# Every software class needs to inherit from ADPSoftwareService and implement gather_data and bulk_create_elements
class ADPAdapter(ADP):
    def get_software(self):
        return self.entity.adp_software or self.structure.adp_software

    def gather_data(self):
        software = self.get_software()
        software_instance = None
        if software:
            if software.name == "decidium":
                software_instance = ADPDecidium(
                    self.client, entity=self.entity, structure=self.structure
                )
            if software_instance:
                success = software_instance.gather_data()
                software_instance.bulk_create_elements()
            else:
                raise NotImplementedError(
                    f"ADP software {software} is not yet implemented"
                )
