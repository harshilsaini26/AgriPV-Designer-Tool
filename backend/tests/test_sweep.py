import json
import math

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.service import cost_multiplier, physics_for

client = TestClient(app)
BASE = {
    "district_id": "107_jodhpur",
    "business_model": "kusum_a",
    "layout": {"preset_id": "elevated_fixed_3m", "kind": "fixed"},
    "rotation": [{"season": "kharif", "crop_id": "bajra"}, {"season": "rabi", "crop_id": "wheat"}],
}


def post(**changes):
    return client.post("/api/sweep", json={**BASE, **changes})


def used(body, name):
    return next(i for i in body["inputs_used"] if i["name"] == name)


def test_default_sweep_shape():
    r = post()
    assert r.status_code == 200
    b = r.json()
    assert b["gcr"] == [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    assert {"farm_income", "energy_income", "ler", "project_irr", "kwp_per_acre"} <= set(b["metrics"])
    assert all(len(v) == 11 for v in b["metrics"].values())
    assert set(b["retention"]) == {"kharif", "rabi"} == set(b["light"])
    assert b["metrics"]["ler"][0] == {"low": 1.0, "central": 1.0, "high": 1.0}
    assert b["metrics"]["farm_income"][0]["central"] == pytest.approx(b["baseline_farm_income"])
    assert b["light"]["rabi"]["mean"][0] == 1.0 and b["clear_gap_m"][0] is None
    assert b["light"]["rabi"]["darkest_tenth"][5] <= b["light"]["rabi"]["mean"][5] < 1.0
    assert b["custom_layout"] is False and b["engine_ms"] > 0 and b["data_version"]


def test_defaults_are_reported_with_their_source():
    b = post().json()
    tariff = used(b, "finance.tariff_per_kwh")
    assert set(tariff) == {"name", "value", "flag", "source", "year"}
    assert (tariff["value"], tariff["flag"], tariff["year"]) == (3.04, "state", 2025) and tariff[
        "source"
    ].startswith("RERC")
    assert used(b, "finance.interest_rate")["flag"] == "assumption"
    assert used(b, "finance.capex_per_kwp")["value"] == pytest.approx(31550 * 1.24)
    assert used(b, "layout.tilt_deg") == {"name": "layout.tilt_deg", "value": 25.0, "flag": "preset",
                                          "source": "optimum tilt limited to 10-25 degrees", "year": None}  # fmt: skip
    assert used(b, "rotation.kharif.bajra.yield_q_per_acre")["flag"] == "state"
    assert used(b, "rotation.rabi.wheat.yield_q_per_acre")["year"] == 2021


def test_overrides_are_flagged_and_change_the_result():
    base = post().json()
    b = post(finance={"tariff_per_kwh": 4.0}, layout={**BASE["layout"], "height_m": 3.5}).json()
    assert used(b, "finance.tariff_per_kwh")["flag"] == "user" and b["custom_layout"] is True
    assert used(b, "finance.capex_per_kwp")["flag"] == "interpolated"
    assert b["metrics"]["energy_income"][5]["central"] > base["metrics"]["energy_income"][5]["central"]
    # height changes how even the light is, not its mean
    assert b["light"]["rabi"]["mean"] == pytest.approx(base["light"]["rabi"]["mean"], abs=0.005)


def test_matches_a_direct_model_call():
    from apv_core import run_sweep
    from backend.schemas import SweepRequest
    from backend.service import build_sweep_inputs

    direct = run_sweep(build_sweep_inputs(SweepRequest(**BASE))[0])
    b = post().json()
    for key in ("ler", "farm_income", "project_irr"):
        assert b["metrics"][key][5]["central"] == pytest.approx(direct.metrics[key][5].central)
    assert b["allowed_gcr"]["central"] == direct.allowed_gcr.central


def test_physics_is_reused_when_only_finance_changes():
    post()
    hits = physics_for.cache_info().hits
    post(finance={"tariff_per_kwh": 3.5}, policy_limit=0.7)
    assert physics_for.cache_info().hits == hits + 1


def test_user_economics_and_lease():
    guar = [{"season": "kharif", "crop_id": "guar",
             "economics": {"yield_q_per_acre": 4.0, "price_per_q": 5000, "cost_per_acre": 8000}}]  # fmt: skip
    # at the state tariff the project earns about 11%, below the assumed 12% target: no lease is affordable
    b = post(business_model="lease", rotation=guar).json()
    assert b["metrics"]["max_affordable_lease"][6]["central"] is None
    assert any(n["code"] == "lease_not_viable" for n in b["notices"])
    assert any(n["code"] == "user_entered_values" for n in b["notices"])
    assert used(b, "rotation.kharif.guar.price_per_q")["flag"] == "user"
    # at a higher tariff it is
    b = post(business_model="lease", rotation=guar, finance={"tariff_per_kwh": 4.0}).json()
    assert b["metrics"]["max_affordable_lease"][6]["central"] > 0


def test_state_without_economics_uses_national_median():
    b = post(district_id="9_leh_ladakh", rotation=[{"season": "rabi", "crop_id": "wheat"}]).json()
    assert used(b, "rotation.rabi.wheat.yield_q_per_acre")["flag"] == "national_median"
    assert used(b, "finance.tariff_per_kwh")["flag"] == "state_fallback"


def test_loss_making_crop_returns_valid_json():
    r = post(district_id="490_pune", rotation=[{"season": "kharif", "crop_id": "rice"}])
    assert r.status_code == 200
    json.loads(r.text, parse_constant=lambda c: pytest.fail(f"non-finite number in the response: {c}"))
    b = r.json()
    assert b["baseline_farm_income"] < 0
    assert all(v["central"] is None or math.isfinite(v["central"]) for v in b["metrics"]["farm_income"])


def test_rotation_errors_name_the_entry():
    cases = [
        ([], ["body", "rotation"]),
        ([{"season": "kharif", "crop_id": "wheat"}], ["body", "rotation", 0, "season"]),
        ([{"season": "kharif", "crop_id": "sugarcane"}], ["body", "rotation", 0, "crop_id"]),
        ([{"season": "kharif", "crop_id": "guar"}], ["body", "rotation", 0, "economics"]),
        ([{"season": "kharif", "crop_id": "bajra"}, {"season": "kharif", "crop_id": "maize"}], ["body", "rotation", 1, "season"]),
    ]  # fmt: skip
    for rotation, loc in cases:
        r = post(rotation=rotation)
        assert r.status_code == 422 and r.json()["detail"][0]["loc"] == loc, rotation


def test_unknown_district_is_404():
    assert post(district_id="nowhere").status_code == 404


def test_cost_multiplier():
    points = {"fixed": [[2.5, 1.19], [3.0, 1.24], [4.0, 1.33]], "vertical": [[0.8, 1.2]]}
    assert cost_multiplier("fixed", 3.0, points) == (1.24, "preset")
    assert cost_multiplier("fixed", 3.5, points) == (pytest.approx(1.285), "interpolated")
    assert cost_multiplier("fixed", 5.0, points) == (1.33, "outside_benchmark_range")
    assert cost_multiplier("vertical", 2.0, points) == (1.2, "outside_benchmark_range")
