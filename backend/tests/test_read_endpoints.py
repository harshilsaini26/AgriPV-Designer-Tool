import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.data import load_app_data

client = TestClient(app)


def test_meta():
    m = client.get("/api/meta").json()
    assert m["data_version"] and m["preview_notice"].startswith("Preview")
    assert len(m["presets"]) == 6 and len(m["crops"]) == 20
    assert m["policy"] == {"default": 0.8, "min": 0.5, "max": 1.0, "step": 0.05}
    assert m["limits"]["height_m"] == [0.5, 6.0] and m["seasons"] == [
        "kharif",
        "rabi",
        "zaid",
    ]
    assert m["assumptions"]["interest_rate"]["flag"] == "assumption"
    assert any(s["id"] == "weather" for s in m["sources"])


def test_districts_list():
    d = client.get("/api/districts").json()
    assert len(d) == 785 and set(d[0]) == {"id", "name", "state"}


def test_district_with_a_state_tariff():
    d = client.get("/api/district/107_jodhpur").json()
    assert d["name"] == "Jodhpur" and d["state"] == "Rajasthan" and d["default_tilt_deg"] == 25.0
    assert d["tariff"]["tariff_per_kwh"] == 3.04 and d["tariff"]["flag"] == "state"
    assert d["economics"]["bajra"]["basis"] == "state" and "guar" not in d["economics"]
    assert d["example_rotation"] == {"basis": "state", "crops": [{"season": "kharif", "crop_id": "bajra"},
                                                              {"season": "rabi", "crop_id": "wheat"}]}  # fmt: skip


def test_district_with_fallbacks():
    d = client.get("/api/district/9_leh_ladakh").json()
    assert d["tariff"] == {"tariff_per_kwh": 3.11, "flag": "state_fallback"}
    assert d["economics"]["wheat"]["basis"] == "national_median"
    assert d["example_rotation"]["basis"] == "national"
    assert [c["crop_id"] for c in d["example_rotation"]["crops"]] == ["rice", "wheat"]


def test_unknown_district_is_404():
    r = client.get("/api/district/nowhere")
    assert r.status_code == 404 and r.json() == {"detail": "unknown district"}


def test_health_reports_the_data_version():
    assert client.get("/api/health").json()["data_version"] == load_app_data().manifest["data_version"]


def test_missing_data_names_the_path(tmp_path):
    with pytest.raises(RuntimeError, match="districts.json"):
        load_app_data(tmp_path)
