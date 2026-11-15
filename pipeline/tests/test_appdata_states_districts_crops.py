import csv
import json
from pathlib import Path

import pytest
from apv_core import CropParams, EvidenceGrade, Range, Season

from pipeline.appdata.crops import build_crops
from pipeline.appdata.districts import build_districts
from pipeline.appdata.states import canonical_state

REPO = Path(__file__).resolve().parents[2]
SHADE = REPO / "research" / "09_crop_shade_response"


def rows(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize("raw, want", [
    ("ODISHA", "Odisha"), ("Orissa", "Odisha"), (" RAJASTHAN ", "Rajasthan"), ("DELHI", "Delhi"),
    ("NCT of Delhi", "Delhi"), ("Chattisgarh", "Chhattisgarh"), ("JAMMU & KASHMIR", "Jammu & Kashmir"),
    ("DADRA,NAGAR HAVELI,DAMAN & DIU", "Dadra, Nagar Haveli, Daman & Diu"), ("Uttaranchal", "Uttarakhand"),
])  # fmt: skip
def test_canonical_state(raw, want):
    assert canonical_state(raw) == want


def test_districts_from_the_real_index():
    index = json.loads((REPO / "data" / "weather" / "index.json").read_text(encoding="utf-8"))["districts"]
    out = build_districts(index)
    assert len(out) == 785 and len({d["id"] for d in out}) == 785
    jodhpur = next(d for d in out if d["id"] == "107_jodhpur")
    assert jodhpur == {"id": "107_jodhpur", "lgd": "107", "name": "Jodhpur", "state": "Rajasthan",
                       "lat": 26.3522, "lon": 73.0996, "elevation_m": 222.0, "optimum_tilt_deg": 29.9}  # fmt: skip
    assert [d["state"] for d in out] == sorted(d["state"] for d in out)


def test_duplicate_district_id_is_an_error():
    entry = {"file": "1_x.npz", "dist_lgd": "1", "district": "X", "state": "GOA", "lat": 1.0, "lon": 2.0,
             "elevation_m": 3.0, "optimum_tilt_deg": 4.0}  # fmt: skip
    with pytest.raises(ValueError, match="1_x"):
        build_districts([entry, entry])


@pytest.fixture(scope="module")
def crops():
    built = build_crops(
        rows(SHADE / "parameters" / "crop_parameters_draft.csv"), rows(SHADE / "papers" / "bibliography.csv")
    )
    return {c["id"]: c for c in built}


def test_twenty_crops_in_file_order(crops):
    assert len(crops) == 20 and list(crops)[:3] == ["rice", "wheat", "soybean"]


def test_wheat(crops):
    w = crops["wheat"]
    assert w["seasons"] == ["rabi"] and w["grade"] == "A" and w["selectable"] is True
    assert w["l_t"] == {"pessimistic": 0.93, "central": 0.89, "optimistic": 0.76}
    assert w["k"] == {"pessimistic": 1.36, "central": 1.18, "optimistic": 1.1}
    assert w["tolerance"] == "neutral" and w["n_indian_studies"] == 2
    assert any("Laub" in c for c in w["citations"]) and len(w["citations"]) == len(set(w["citations"]))


def test_seasons_and_tolerance(crops):
    assert crops["rice"]["seasons"] == ["kharif", "rabi", "zaid"]
    assert crops["onion"]["seasons"] == ["kharif", "rabi"]
    assert crops["mustard"]["tolerance"] == "sensitive" and crops["cotton"]["tolerance"] == "tolerant"
    assert crops["gram"]["name"] == "Gram (chickpea)"


def test_crops_that_cannot_be_selected(crops):
    assert (
        crops["sugarcane"]["selectable"] is False
        and "whole-year" in crops["sugarcane"]["not_selectable_reason"]
    )
    assert crops["cumin"]["selectable"] is False and "grade D" in crops["cumin"]["not_selectable_reason"]
    assert crops["cumin"]["l_t"] is None and sum(c["selectable"] for c in crops.values()) == 18


def test_every_selectable_crop_is_valid_for_the_model(crops):
    for c in crops.values():
        if c["selectable"]:
            CropParams(c["id"], c["name"], frozenset(Season(s) for s in c["seasons"]), c["tolerance"],
                       Range(**c["l_t"]), Range(**c["k"]), EvidenceGrade(c["grade"]))  # fmt: skip
