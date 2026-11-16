from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health_reports_the_weather_packs():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["weather_packs"] == 785


def test_deep_link_serves_the_page_when_the_frontend_is_built():
    import pytest

    from backend.app import WEB_DIST

    if not (WEB_DIST / "index.html").is_file():
        pytest.skip("web/dist not built")
    r = client.get("/model/107_jodhpur", headers={"Accept": "text/html"})  # as a browser navigation sends
    assert r.status_code == 200 and "AgriPV Lab" in r.text
    assert client.get("/api/nope").status_code == 404


def test_vercel_entrypoint_names_the_app():
    import tomllib
    from pathlib import Path

    config = tomllib.loads(
        (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(encoding="utf-8")
    )
    module, attr = config["tool"]["vercel"]["entrypoint"].split(":")
    assert (module, attr) == ("backend.app", "app")


def test_health_is_not_ok_without_weather_packs(tmp_path, monkeypatch):
    import backend.app as module

    monkeypatch.setattr(module, "WEATHER_DIR", tmp_path)
    r = client.get("/api/health")
    assert r.status_code == 503 and r.json()["status"] == "missing weather packs"


def test_missing_app_data_stops_the_app_at_start(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    code = (
        f"import pathlib, backend.data as d; d.APP_DATA_DIR = pathlib.Path(r'{tmp_path}'); import backend.app"
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True, check=False)
    assert r.returncode != 0 and "app data is missing" in r.stderr and "districts.json" in r.stderr
