from fastapi.testclient import TestClient

from backend.app import app
from backend.tests.test_sweep import BASE

client = TestClient(app, raise_server_exceptions=False)


def loc_of(**changes):
    r = client.post("/api/sweep", json={**BASE, **changes})
    assert r.status_code == 422, r.text
    return r.json()["detail"][0]["loc"]


def test_layout_errors_name_the_field():
    assert loc_of(layout={"kind": "fixed", "height_m": 9.0}) == ["body", "layout", "height_m"]
    assert loc_of(layout={"kind": "tracker", "height_m": 1.0, "collector_width_m": 2.28}) == [
        "body",
        "layout",
        "height_m",
    ]
    assert loc_of(layout={"kind": "fixed", "module": {"efficiency": 0.5, "bifaciality": 0.8,
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
