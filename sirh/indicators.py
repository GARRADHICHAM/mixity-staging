import logging

import distinctipy as distinctipy

from accounts.vocabularies import ADP_FILTERS
from sirh.models import ADPIndicator
from django.utils.translation import ugettext_lazy as _
import re


def hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip("#")
    r, g, b = (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )
    alpha = max(0.0, min(alpha, 1.0))
    return f"rgba({r}, {g}, {b}, {alpha})"


def add_alpha_to_rgb(rgb_string, alpha):
    match = re.match(r"rgb\((\d+(\.\d+)?), (\d+(\.\d+)?), (\d+(\.\d+)?)\)", rgb_string)
    if match:
        rgb_values = [float(val) for val in match.groups()[::2]]
        rgba_values = rgb_values + [alpha]
        rgba_string = f'rgba({", ".join(map(str, rgba_values))})'
        return rgba_string
    else:
        return rgb_string


# ages are stored raw (ex : we have all data for people aged 23). We need to group some ages together
def group_ages(data, workforce_data=None, mode="ratio"):
    final_data = {"less_26": {}, "26_39": {}, "40_54": {}, "from_55": {}}
    for key, values in data.items():
        try:
            age = int(key)
            if age < 26:
                final_age = "less_26"
            elif age < 40:
                final_age = "26_39"
            elif age < 55:
                final_age = "40_54"
            else:
                final_age = "from_55"
            for f, value in values.items():
                if workforce_data and not final_age in workforce_data:
                    workforce_data[final_age] = {}
                if not f in final_data[final_age]:
                    if not isinstance(value, dict):
                        final_data[final_age][f] = 0
                        if workforce_data:
                            workforce_data[final_age][f] = 0
                    elif mode == "ratio":
                        final_data[final_age][f] = {
                            "sum_F": 0,
                            "sum_M": 0,
                            "count_F": 0,
                            "count_M": 0,
                        }
                    elif mode == "percentage":
                        final_data[final_age][f] = {
                            "F": 0,
                            "M": 0,
                            "NA": 0,
                        }

                if not isinstance(value, dict):
                    final_data[final_age][f] += value
                    if workforce_data:
                        workforce_data[final_age][f] += workforce_data[key][f]
                else:
                    for k, v in value.items():
                        final_data[final_age][f][k] += v

        except ValueError as e:
            logging.exception(f"{e}")
    return final_data


# sum of salaries and amount of employees per gender are stored. So we need to compute the paygap based on these information
def compute_gender_pay_gap(data):
    for key, values in data.items():
        data[key] = (
            100
            * (
                (values.get("sum_M", 0) / values.get("count_M", 1))
                - (values.get("sum_F", 0) / values.get("count_F", 1))
            )
            / (
                (
                    (values.get("sum_M", 0) + values.get("sum_F", 0))
                    / ((values.get("count_M", 0) + values.get("count_F", 0)) or 1)
                )
                or 1
            )
        )
    return data


# in some indicators, the sum of salaries and the amount of employees are stored. So we need,based on these information, compute the paygap
def compute_age_pay_gap(data, mode):
    total_salary = 0
    count = 0
    final_paygap = {}
    if mode == "gender":
        for v in data.values():
            total_salary += v.get("sum_F", 0) + v.get("sum_M", 0)
            count += v.get("count_F", 0) + v.get("count_M", 0)
        final_salary = total_salary / (count or 1)
        for k, v in data.items():
            final_paygap[k] = {
                "M": 100
                * (v.get("sum_M", 0) / v.get("count_M", 1) - final_salary)
                / final_salary,
                "F": 100
                * (v.get("sum_F", 0) / v.get("count_F", 1) - final_salary)
                / final_salary,
            }
    else:
        tmp_data = {}
        for key, value in data.items():
            try:
                s = key.split("_")
                age = int(s[1])
                if age < 26:
                    final_age = "less_26"
                elif age < 40:
                    final_age = "26_39"
                elif age < 55:
                    final_age = "40_54"
                else:
                    final_age = "from_55"
                if not final_age in tmp_data:
                    tmp_data[final_age] = {"sum": 0, "count": 0}
                tmp_data[final_age][s[0]] += value
                if s[0] == "sum":
                    total_salary += value
                else:
                    count += value
            except ValueError as e:
                logging.exception(f"{e}")

        final_salary = total_salary / (count or 1)
        for key, value in tmp_data.items():
            final_paygap[key] = (
                100
                * ((value["sum"] / (value["count"] or 1)) - final_salary)
                / final_salary
            )

    return final_paygap


# we do a ratio of each data based on the workforce
def do_ratio(data, workforce_data):
    for key, values in data.items():
        for f, value in values.items():
            data[key][f] = data[key][f] * 100 / (workforce_data[key][f] or 1)

    return data


def invert_filters(data):
    final_data = {}
    for key, values in data.items():
        for key2, values2 in values.items():
            if key2 not in final_data:
                final_data[key2] = {}
            final_data[key2][key] = values2
    return final_data


# mainly used to do stats about gender repartition. We most likely have the sum of employees for each gender. We just convert these numbers into percentage
def compute_percentage_genders(data):
    for k, v in data.items():
        sum_employees = sum(list(v.values())) or 1
        for g in ["M", "F", "NA"]:
            if g not in v:
                v[g] = 0
        for key in v:
            data[k][key] = data[k][key] * 100 / sum_employees
    return data


def compute_percentage_citizenships(data, cz_list):
    for k, v in data.items():
        sum_employees = sum(list(v.values())) or 1
        for g in cz_list:
            if g not in v:
                v[g] = 0
        for key in v:
            data[k][key] = data[k][key] * 100 / sum_employees
    return data


def to_css(color):
    return f"rgb({color[0] * 255},{color[1] * 255}, {color[2] * 255})"


"""
The goal is to convert ADPIndicator data to a format readable for ChartJS or at least.
Understanding of the ADP API, current ADPIndicator content and requested displayed indicator is recommended
"""


class ADPIndicatorAdapter:
    @classmethod
    def get_indicator(cls, name, entity):
        try:
            indicator_instance = ADPIndicator.objects.filter(
                entity=entity,
                type__name=name,
            ).last()
            if not indicator_instance:
                raise Exception("No indicator matching query")
            return getattr(cls, f"get_{name}_indicator")(entity, indicator_instance)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return {"message": f"{e}"}

    @classmethod
    def get_exiting_indicator(cls, entity, instance):
        return cls.get_barchart_indicator(
            entity,
            instance,
            _("Taux de sortie"),
            _("Taux de sortie au sein de l’organisation"),
        )

    @classmethod
    def get_hiring_indicator(cls, entity, instance):
        return cls.get_barchart_indicator(
            entity,
            instance,
            _("Taux d'entrées"),
            _("Taux d'entrées au sein de l’organisation"),
        )

    """
        Doesn't compute turnover directly. Stores amount of  hired/exited employees per year and per filter.
        You need to compute the turnover in the indicator itself
        [( Nombre de départs sur l'année N + nombre d'arrivées sur l'année N) / 2 ] / Effectif au 1er janvier de l'année N

        Workforce per filter is stored in the workforce_per_year key of the JSON (same structure as base data)
    """

    @classmethod
    def get_turnover_indicator(cls, entity, instance):
        for key1, category in instance.data["data"].items():
            if key1 == "workforce_per_year":
                continue
            for key2, datas in category.items():
                for year in datas:
                    calcul = 0
                    try:
                        calcul = (
                            instance.data["data"][key1][key2][year]["hired"]
                            + instance.data["data"][key1][key2][year]["exited"]
                        )
                    except Exception:
                        calcul = instance.data["data"][key1][key2][year]["hired"]
                    if (
                        str(int(year) - 1)
                        in instance.data["data"]["workforce_per_year"][key1][key2]
                    ):
                        instance.data["data"][key1][key2][year] = (
                            calcul
                            / 2
                            / instance.data["data"]["workforce_per_year"][key1][key2][
                                str(int(year) - 1)
                            ]
                            * 100
                        )

                    else:
                        instance.data["data"][key1][key2][year] = 100 * ((calcul / 2))
        return cls.get_barchart_indicator(
            entity,
            instance,
            _("Taux de renouvellement"),
            _("Taux de turn over au sein de l’organisation"),
        )

    @classmethod
    def get_gender_repartition_indicator(cls, entity, instance):
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "series" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        final_indicator = {}
        for key, f in instance.data["data"].items():
            values = f
            if key == "age":
                values = group_ages(f, mode="percentage")
            values = compute_percentage_genders(values)
            values = {
                "title": _("Répartition des genres au sein de l'organisation"),
                "indicator_type": "MultiplePieChart",
                "data": [
                    {
                        "label": ADP_FILTERS.get(k, k),
                        "labels": [
                            ADP_FILTERS.get(gender, gender)
                            for gender in ["F", "M", "NA"]
                        ],
                        "series": [
                            {
                                "data": [v[gender] for gender in ["F", "M", "NA"]],
                                "backgroundColor": ["#994343", "#FF6F6F", "#FFE2E2"],
                                "label": ADP_FILTERS.get(k, k),
                            }
                        ],
                    }
                    for k, v in values.items()
                ],
            }
            final_indicator[key] = values
        return {"filters": list(filters.values()), "indicators": final_indicator}

    @classmethod
    def get_citizenships_indicator(cls, entity, instance):
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "series" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        final_indicator = {}
        cz_list = list(instance.data["data"]["global"]["all"].keys())
        for key, f in instance.data["data"].items():
            values = f
            if key == "age":
                values = group_ages(f, mode="percentage")
            values = compute_percentage_citizenships(values, cz_list)
            values = {
                "title": _("Répartition des nationalités au sein de l'organisation"),
                "indicator_type": "MultiplePieChart",
                "data": [
                    {
                        "label": ADP_FILTERS.get(k, k),
                        "labels": [ADP_FILTERS.get(cz, cz) for cz in cz_list],
                        "series": [
                            {
                                "data": [v[cz] for cz in cz_list],
                                "backgroundColor": ["#994343", "#FF6F6F", "#FFE2E2"],
                                "label": ADP_FILTERS.get(k, k),
                            }
                        ],
                    }
                    for k, v in values.items()
                ],
            }
            final_indicator[key] = values
        return {"filters": list(filters.values()), "indicators": final_indicator}

    @classmethod
    def get_age_pyramid_indicator(cls, entity, instance):
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "series" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        final_indicator = {}
        for key, f in instance.data["data"].items():
            for k, v in f.items():
                v = group_ages(v, mode="percentage")
                compute_percentage_genders(v)
                f[k] = v
            values = {
                "title": _("Répartition des générations dans l'organisation"),
                "indicator_type": "MultipleHorizontalBarChart",
                "data": [
                    {
                        "label": ADP_FILTERS.get(third_filter, third_filter),
                        "labels": [ADP_FILTERS.get(k, k) for k in v.keys()],
                        "series": [
                            {
                                "data": [round(age[gender], 2) for age in v.values()],
                                "backgroundColor": color,
                                "label": ADP_FILTERS.get(gender, gender),
                                "datalabels": {
                                    "align": "center",
                                    "anchor": "center",
                                    "color": "#fff",
                                    "font": {
                                        "weight": "bold",
                                    },
                                    "offset": 8,
                                    "textAlign": "center",
                                },
                            }
                            for color, gender in {
                                "#272440": "F",
                                "#7A7697": "M",
                                "#ECEBF0": "NA",
                            }.items()
                        ],
                    }
                    for third_filter, v in f.items()
                ],
            }
            # print(key)
            final_indicator[key] = values
        return {"filters": list(filters.values()), "indicators": final_indicator}

    @classmethod
    def get_age_paygap_indicator(cls, entity, instance):
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "series" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        final_indicator = {}
        for key, f in instance.data["data"].items():
            if key == "gender":
                f = group_ages(f, mode="ratio")
                f = compute_age_pay_gap(f, "gender")

                values = {
                    "title": _("Écart de salaire par âge sur les 12 derniers mois"),
                    "indicator_type": "LineChart",
                    "labels": [ADP_FILTERS.get(k, k) for k in f.keys()],
                    "series": [
                        {
                            "data": [age[gender] for age in f.values()],
                            "gradient": {
                                "backgroundColor": {
                                    "axis": "y",
                                    "colors": {
                                        "0": "transparent",
                                        "10": hex_to_rgba(color, 0.1),
                                        "50": hex_to_rgba(color, 0.5),
                                        "100": color,
                                        "-10": hex_to_rgba(color, 0.1),
                                        "-50": hex_to_rgba(color, 0.5),
                                        "-100": color,
                                    },
                                },
                            },
                            "borderColor": color,
                            "fill": {
                                "target": "origin",
                            },
                            "tension": 0.4,
                            "label": ADP_FILTERS.get(gender, gender),
                        }
                        for color, gender in {
                            "#331616": "F",
                            "#FF6F6F": "M",
                        }.items()
                    ],
                }
            else:
                for k, v in f.items():
                    f[k] = compute_age_pay_gap(v, key)
                colors_tmp = distinctipy.get_colors(len(f.values()))
                colors = {k: to_css(colors_tmp.pop()) for k in f.keys()}
                values = {
                    "title": _("Écart de salaire par âge sur les 12 derniers mois"),
                    "indicator_type": "LineChart",
                    "labels": [
                        ADP_FILTERS.get(k, k)
                        for k in ["less_26", "26_39", "40_54", "from_55"]
                    ],
                    "series": [
                        {  # TODO : How to manage colors for business units, ...
                            "data": [
                                v.get(k, None)
                                for k in ["less_26", "26_39", "40_54", "from_55"]
                            ],
                            "gradient": {
                                "backgroundColor": {
                                    "axis": "y",
                                    "colors": {
                                        "0": "transparent",
                                        "10": add_alpha_to_rgb(colors[k], 0.1),
                                        "50": add_alpha_to_rgb(colors[k], 0.5),
                                        "100": colors[k],
                                        "-10": add_alpha_to_rgb(colors[k], 0.1),
                                        "-50": add_alpha_to_rgb(colors[k], 0.5),
                                        "-100": colors[k],
                                    },
                                },
                            },
                            "borderColor": colors[k],
                            "fill": {
                                "target": "origin",
                            },
                            "tension": 0.4,
                            # "borderColor": colors[k],
                            "label": ADP_FILTERS.get(k, k),
                        }
                        for k, v in f.items()
                    ],
                }
            # print(key)
            final_indicator[key] = values
        return {"filters": list(filters.values()), "indicators": final_indicator}

    @classmethod
    def get_gender_paygap_indicator(cls, entity, instance):
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "labels" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        final_indicator = {}
        for key, f in instance.data["data"].items():
            values = f
            if key == "age":
                values = group_ages(f)
            values = compute_gender_pay_gap(values)
            values = {
                "title": _("Écart de salaire par genre sur les 12 derniers mois"),
                "indicator_type": "GapChart",
                "labels": [ADP_FILTERS.get(k, k) for k in values.keys()],
                "series": [
                    {
                        "data": list(values.values()),
                        "label": _("Ecart de salaire"),
                    }
                ],
            }
            # print(key)
            final_indicator[key] = values
        return {"filters": list(filters.values()), "indicators": final_indicator}

    @classmethod
    def get_remuneration_increase_gender_indicator(cls, entity, instance):
        if instance.data["data"] == None:
            return {"filters": [], "indicators": {}}
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "labels" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        final_indicator = {}
        for key, f in instance.data["data"].items():
            values = f
            if key == "age":
                values = group_ages(f)
            values = compute_gender_pay_gap(values)
            values = {
                "title": _("Écart d'augmentation par genre sur les 12 derniers mois"),
                "indicator_type": "GapChart",
                "labels": [ADP_FILTERS.get(k, k) for k in values.keys()],
                "series": [
                    {
                        "data": list(values.values()),
                        "label": _(
                            "Écart d'augmentation par genre sur les 12 derniers mois"
                        ),
                    }
                ],
            }
            # print(key)
            final_indicator[key] = values
        return {"filters": list(filters.values()), "indicators": final_indicator}

    @classmethod
    def get_remuneration_increase_age_indicator(cls, entity, instance):
        if instance.data["data"] == None:
            return {"filters": [], "indicators": {}}
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "labels" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        final_indicator = {}
        for key, f in instance.data["data"].items():
            values = f
            if key == "age":
                values = group_ages(f)
            values = compute_gender_pay_gap(values)
            values = {
                "title": _("Écart d'augmentation par âge sur les 12 derniers mois"),
                "indicator_type": "GapChart",
                "labels": [ADP_FILTERS.get(k, k) for k in values.keys()],
                "series": [
                    {
                        "data": list(values.values()),
                        "label": _(
                            "Écart d'augmentation par âge sur les 12 derniers mois"
                        ),
                    }
                ],
            }
            # print(key)
            final_indicator[key] = values
        return {"filters": list(filters.values()), "indicators": final_indicator}

    @classmethod
    def get_promotion_gender_indicator(cls, entity, instance):
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "labels" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        final_indicator = {}
        for key, f in instance.data["data"].items():
            values = f
            if key == "age":
                values = group_ages(f)
            values = compute_gender_pay_gap(values)
            values = {
                "title": _("Écart de promotion par genre sur les 12 derniers mois"),
                "indicator_type": "GapChart",
                "labels": [ADP_FILTERS.get(k, k) for k in values.keys()],
                "series": [
                    {
                        "data": list(values.values()),
                        "label": _(
                            "Écart de promotion par genre sur les 12 derniers mois"
                        ),
                    }
                ],
            }
            # print(key)
            final_indicator[key] = values
        return {"filters": list(filters.values()), "indicators": final_indicator}

    @classmethod
    def get_promotion_age_indicator(cls, entity, instance):
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "labels" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        final_indicator = {}
        for key, f in instance.data["data"].items():
            values = f
            if key == "age":
                values = group_ages(f)
            values = compute_gender_pay_gap(values)
            values = {
                "title": _("Écart de promotion par âge sur les 12 derniers mois"),
                "indicator_type": "GapChart",
                "labels": [ADP_FILTERS.get(k, k) for k in values.keys()],
                "series": [
                    {
                        "data": list(values.values()),
                        "label": _(
                            "Écart de promotion par âge sur les 12 derniers mois"
                        ),
                    }
                ],
            }
            # print(key)
            final_indicator[key] = values
        return {"filters": list(filters.values()), "indicators": final_indicator}

    @classmethod
    def get_barchart_indicator(cls, entity, instance, label, title):
        filters = {
            f: {
                "name": ADP_FILTERS.get(f, f),
                "key": f,
                "third_filter": "labels" if f != "global" else False,
            }
            for f in instance.data["data"]
        }
        del filters["workforce_per_year"]
        final_indicator = {}
        for key, f in instance.data["data"].items():
            if key == "workforce_per_year":
                continue
            secondary_filters = set()
            values = f
            if key == "age":
                values = group_ages(f, instance.data["data"]["workforce_per_year"][key])
            if label != "Taux de renouvellement":
                values = do_ratio(
                    values, instance.data["data"]["workforce_per_year"][key]
                )
            final_values = invert_filters(values)
            for year, values in final_values.items():
                secondary_filters.add(year)
                if key != "global":
                    final_values[year] = {
                        "title": title,
                        "indicator_type": "HorizontalBarChart",
                        "labels": [
                            ADP_FILTERS.get(k, k) for k in final_values[year].keys()
                        ],
                        "series": [
                            {
                                "data": [
                                    round(value, 2)
                                    for value in final_values[year].values()
                                ],
                                "borderColor": "#ffffff00",
                                "backgroundColor": "#8888E2",
                                "label": label,
                                "borderRadius": 100,
                                "datalabels": {
                                    "align": "end",
                                    "anchor": "start",
                                    "color": "#000",
                                    "font": {
                                        "weight": "bold",
                                    },
                                    "textAlign": "center",
                                },
                            }
                        ],
                    }
                else:
                    final_values[year] = {
                        "title": title,
                        "indicator_type": "CircularChart",
                        "color": "#8888E2",
                        "data": [
                            0,
                            0,
                            [round(value, 2) for value in final_values[year].values()],
                        ],  # TODO : Mean scores
                    }
            filters[key]["secondary_filters"] = sorted(
                list(secondary_filters), reverse=True
            )
            # print(key)
            final_indicator[key] = final_values

        return {"filters": list(filters.values()), "indicators": final_indicator}
