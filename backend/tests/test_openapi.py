import json
from pathlib import Path

from backend.app import app


def test_committed_contract_is_current():
    committed = json.loads((Path(__file__).resolve().parents[1] / "openapi.json").read_text(encoding="utf-8"))
    assert app.openapi() == committed, "run: python -m backend.export_openapi"
