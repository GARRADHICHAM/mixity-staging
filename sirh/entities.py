from datetime import datetime


class Worker:
    def __init__(self, worker: dict):
        self.worker = worker
        self.department = None
        self.business_unit = None
        assignment = self.get_assignment()
        if assignment:
            for unit in assignment["assignedOrganizationalUnits"]:
                value = (
                    "shortName" in unit["nameCode"]
                    and unit["nameCode"]["shortName"]
                    or (
                        "codeValue" in unit["nameCode"]
                        and unit["nameCode"]["codeValue"]
                    )
                )
                if unit["itemID"] == "departmentId":
                    self.department = value
                elif unit["itemID"] == "strucAffectationId":
                    self.business_unit = value

    def get_age(self):
        try:
            delta = datetime.now() - datetime.strptime(
                self.worker["person"]["birthDate"], "%Y-%m-%d"
            )
            return int(
                delta.days / 365.2425
            )  # https://stackoverflow.com/questions/765797/convert-timedelta-to-years#comment1872614_765990
        except KeyError:
            return None

    def get_seniority(self):
        return int(
            (
                datetime.now()
                - datetime.strptime(
                    self.worker["workerDates"]["firstHireDate"], "%Y-%m-%d"
                )
            ).days
            / 365.2425
        )

    def get_recruiting_year(self):
        return datetime.strptime(
            self.worker["workerDates"]["firstHireDate"], "%Y-%m-%d"
        ).year

    def get_exiting_year(self):
        if "terminationDate" in self.worker["workerDates"]:
            return datetime.strptime(
                self.worker["workerDates"]["terminationDate"], "%Y-%m-%d"
            ).year
        return None

    def get_assignment(self):
        return (
            len(self.worker["workAssignments"]) > 0
            and self.worker["workAssignments"][0]
        )

    def get_job(self):
        assignment = self.get_assignment()
        if assignment:
            return "jobTitle" in assignment and assignment["jobTitle"] or "Unknown"
        return "Unknown"

    def get_classification(self):
        assignment = self.get_assignment()
        if (
            "occupationalClassifications" in assignment
            and len(assignment["occupationalClassifications"]) > 0
        ):  # yes, ADP prefers to delete the field if empty
            return assignment["occupationalClassifications"][0]["classificationCode"][
                "shortName"
            ]
        return None

    def get_gender(self):
        return (
            "codeValue" in self.worker["person"]["genderCode"]
            and self.worker["person"]["genderCode"]["codeValue"]
            or "NA"
        )

    def get_worker_citizenships(self):
        if "citizenshipCountryCodes" in self.worker["person"]:
            return [
                c["codeValue"] for c in self.worker["person"]["citizenshipCountryCodes"]
            ]
        return []

    def get_contract_type(self):
        assignment = self.get_assignment()
        if "workerTypeCode" in assignment:
            return (
                "shortName" in assignment["workerTypeCode"]
                and assignment["workerTypeCode"]["shortName"]
                or None
            )
        return None

    def get_base_remuneration(self):
        assignment = self.get_assignment()
        if (
            assignment
            and "amountValue" in assignment["baseRemuneration"]["monthlyRateAmount"]
        ):  # yes, sometimes the field can be empty
            return assignment["baseRemuneration"]["monthlyRateAmount"]["amountValue"]
        return None

    def get_currency(self):
        assignment = self.get_assignment()
        if assignment:
            return assignment["baseRemuneration"]["monthlyRateAmount"]["currencyCode"]
        return None

    def get_id(self):
        return self.worker["workerID"]["idValue"]

    def is_active(self):
        return (
            not self.get_exiting_year()
            or self.get_exiting_year() >= datetime.now().year
        )
