import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.tests.test_sweep import BASE

client = TestClient(app, raise_server_exceptions=False)


def loc_of(**changes):
    r = client.post("/api/sweep", json={**BASE, **changes})
    assert r.status_code == 422, r.text
    return r.json()["detail"][0]["loc"]


def test_layout_errors_name_the_field():
    assert loc_of(layout={"preset_id": "elevated_fixed_3m", "height_m": 9.0}) == [
        "body",
        "layout",
        "height_m",
    ]
    assert loc_of(layout={"preset_id": "tracker_2.5m", "height_m": 1.0}) == [
        "body",
        "layout",
        "height_m",
    ]
    assert loc_of(layout={"preset_id": "elevated_fixed_3m", "module": {"efficiency": 0.5, "bifaciality": 0.8,
                                                      "temp_coeff_per_c": -0.003}})[:3] == ["body", "layout", "module"]  # fmt: skip


def test_finance_errors_name_the_field():
    assert loc_of(finance={"tariff_per_kwh": 0}) == ["body", "finance", "tariff_per_kwh"]
    assert loc_of(finance={"capex_per_kwp": -5}) == ["body", "finance", "capex_per_kwp"]
    assert loc_of(finance={"tarif": 3.0}) == ["body", "finance", "tarif"]


def test_policy_and_farmable_fraction_limits():
    assert loc_of(policy_limit=0.3) == ["body", "policy_limit"]
    assert loc_of(a_farm=1.4) == ["body", "a_farm"]


def test_unexpected_failure_is_a_plain_500(monkeypatch):
    from backend import service

    monkeypatch.setattr(service, "physics_for", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    r = client.post("/api/sweep", json=BASE)
    assert r.status_code == 500 and r.json() == {"detail": "internal error"} and "boom" not in r.text


def test_zero_revenue_rotation_is_a_422_not_a_500():
    zero = {"yield_q_per_acre": 0, "price_per_q": 0, "cost_per_acre": 0}
    assert loc_of(rotation=[{"season": "kharif", "crop_id": "bajra", "economics": zero}]) == [
        "body",
        "rotation",
    ]


def test_negative_economics_name_the_field():
    bad = {"yield_q_per_acre": 4.0, "price_per_q": -1, "cost_per_acre": 8000}
    loc = loc_of(rotation=[{"season": "kharif", "crop_id": "bajra", "economics": bad}])
    assert loc == ["body", "rotation", 0, "economics", "price_per_q"]


@pytest.mark.parametrize("raw", ['"a_farm": NaN', '"policy_limit": Infinity', '"land_acres": 1e400'])
def test_non_finite_numbers_are_a_422_not_a_500(raw):
    import json

    body = json.dumps(BASE)[:-1] + ", " + raw + "}"
    r = client.post("/api/sweep", content=body, headers={"Content-Type": "application/json"})
    assert r.status_code == 422, r.text
    json.loads(r.text)  # the error body itself is valid JSON


def test_a_structure_preset_is_required():
    assert loc_of(layout={"tilt_deg": 20.0}) == ["body", "layout", "preset_id"]
    assert loc_of(layout={"preset_id": "pergola"}) == ["body", "layout", "preset_id"]
