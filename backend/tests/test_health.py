from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health_reports_the_weather_packs():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["weather_packs"] == 785


def test_probe_runs_a_real_sweep():
    r = client.get("/api/_probe/sweep", params={"district_id": "107_jodhpur"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["ler_central"]) == 11 and body["ler_central"][0] == 1.0
    assert body["engine_ms"] > 0


def test_probe_unknown_district_is_404():
    r = client.get("/api/_probe/sweep", params={"district_id": "nowhere"})
    assert r.status_code == 404 and r.json() == {"detail": "unknown district"}


def test_deep_link_serves_the_page_when_the_frontend_is_built():
    import pytest

    from backend.app import WEB_DIST

    if not (WEB_DIST / "index.html").is_file():
        pytest.skip("web/dist not built")
    r = client.get("/model/107_jodhpur", headers={"Accept": "text/html"})  # as a browser navigation sends
    assert r.status_code == 200 and "AgriPV Lab" in r.text
    assert client.get("/api/nope").status_code == 404
