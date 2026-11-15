import csv
from pathlib import Path

import pytest

from pipeline.appdata.economics import build_crop_economics

REPO = Path(__file__).resolve().parents[2]
SOURCE = (
    REPO
    / "research"
    / "07_crop_economics"
    / "cost_of_cultivation"
    / "idp_des_cost_of_cultivation_1996-2022.csv"
)


def row(state, crop, year, y, value, cost):
    return {"state_name": state, "crop_name": crop, "year": year, "derived_yield": y,
            "main_product_value": value, "cul_cost_a2fl": cost}  # fmt: skip


def test_units_and_latest_year():
    out = build_crop_economics([
        row("Punjab", "Wheat", "2019-20", "40.0", "80000", "36000"),
        row("Punjab", "Wheat", "2021-22", "42.45", "91300.6", "37600.8"),
    ])  # fmt: skip
    assert out["by_state"]["Punjab"]["wheat"] == {
        "yield_q_per_acre": 17.18, "price_per_q": 2151, "cost_per_acre": 15216, "year": "2021-22", "basis": "state"}  # fmt: skip


def test_rows_that_are_old_incomplete_or_unmapped_are_ignored():
    out = build_crop_economics([
        row("Bihar", "Wheat", "2013-14", "30", "50000", "20000"),
        row("Bihar", "Maize", "2021-22", "30", "", "20000"),
        row("Bihar", "Jute", "2021-22", "30", "50000", "20000"),
    ])  # fmt: skip
    assert out["by_state"] == {} and out["national"] == {}


def test_national_median_and_state_names():
    out = build_crop_economics([
        row("ORISSA", "Paddy", "2021-22", "24.711", "49422", "24711"),
        row("Punjab", "Paddy", "2021-22", "74.133", "148266", "49422"),
        row("Bihar", "Paddy", "2020-21", "49.422", "98844", "74133"),
    ])  # fmt: skip
    assert set(out["by_state"]) == {"Odisha", "Punjab", "Bihar"}
    assert out["national"]["rice"] == {"yield_q_per_acre": 20.0, "price_per_q": 2000, "cost_per_acre": 20000,
                                       "year": "2021-22", "basis": "national_median", "n_states": 3}  # fmt: skip


def test_example_rotations_from_the_real_file():
    from pipeline.appdata.crops import build_crops
    from pipeline.appdata.economics import build_example_rotations

    shade = REPO / "research" / "09_crop_shade_response"
    with (
        (shade / "parameters" / "crop_parameters_draft.csv").open(encoding="utf-8") as a,
        (shade / "papers" / "bibliography.csv").open(encoding="utf-8") as b,
        SOURCE.open(encoding="utf-8") as c,
    ):
        out = build_example_rotations(
            list(csv.DictReader(c)), build_crops(list(csv.DictReader(a)), list(csv.DictReader(b)))
        )
    pair = lambda entries: [(e["season"], e["crop_id"]) for e in entries]
    assert pair(out["by_state"]["Rajasthan"]) == [("kharif", "bajra"), ("rabi", "wheat")]
    assert pair(out["by_state"]["Maharashtra"]) == [("kharif", "soybean"), ("rabi", "gram")]
    assert pair(out["by_state"]["Punjab"]) == [("kharif", "rice"), ("rabi", "wheat")]
    assert pair(out["national"]) == [("kharif", "rice"), ("rabi", "wheat")]
    assert all(e["crop_id"] != "sugarcane" for entries in out["by_state"].values() for e in entries)


def test_real_file_coverage():
    with SOURCE.open(encoding="utf-8") as fh:
        out = build_crop_economics(list(csv.DictReader(fh)))
    assert out["by_state"]["Punjab"]["wheat"]["yield_q_per_acre"] == pytest.approx(17.18)
    assert len(out["by_state"]) >= 19
    assert set(out["national"]) == {"rice", "wheat", "soybean", "cotton", "maize", "gram", "mustard", "bajra",
                                    "sugarcane", "moong", "groundnut", "tur", "jowar", "urad", "potato", "onion",
                                    "lentil", "sesame"}  # fmt: skip
