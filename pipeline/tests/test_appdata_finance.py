import csv
import json
import shutil
from pathlib import Path

from pipeline.appdata.build_app_data import main
from pipeline.appdata.finance import ASSUMPTIONS, SOURCES, build_finance_defaults, build_structures

REPO = Path(__file__).resolve().parents[2]
FIN = REPO / "research" / "11_finance_policy"
STRUCT = REPO / "research" / "12_structures_technology"


def rows(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_finance_defaults():
    out = build_finance_defaults(
        rows(FIN / "kusum" / "kusum_a_state_tariffs.csv"), rows(FIN / "capex_om" / "capex_om_benchmarks.csv")
    )
    assert len(out["tariffs"]) == 11 and "NATIONAL_FALLBACK" not in out["tariffs"]
    assert (
        out["tariffs"]["Rajasthan"]["tariff_per_kwh"] == 3.04
        and out["tariffs"]["Rajasthan"]["flag"] == "state"
    )
    assert out["national_fallback"] == {"tariff_per_kwh": 3.11, "flag": "state_fallback"}
    assert out["base_capex_per_kwp"] == {"central": 31550, "low": 28390, "high": 34700}
    assert out["base_om_per_kwp_year"]["central"] == 640 and out["om_escalation"] == 0.0525
    assert out["assumptions"]["interest_rate"] == {"value": 0.10, "flag": "assumption"}
    assert set(out["assumptions"]) == set(ASSUMPTIONS)


def test_structures():
    out = build_structures(rows(STRUCT / "structure_presets.csv"), rows(STRUCT / "module_parameters.csv"),
                           rows(FIN / "capex_om" / "capex_om_benchmarks.csv"))  # fmt: skip
    by_id = {p["id"]: p for p in out["presets"]}
    assert list(by_id) == ["elevated_fixed_2.5m", "elevated_fixed_3m", "elevated_fixed_4m", "tracker_2.5m",
                           "tracker_4m", "vertical_bifacial_ew"]  # fmt: skip
    fixed = by_id["elevated_fixed_3m"]
    assert (fixed["kind"], fixed["height_m"], fixed["collector_width_m"], fixed["tilt_rule"]) == (
        "fixed",
        3.0,
        4.56,
        "optimum_10_25",
    )
    assert (
        fixed["a_farm"] == {"central": 0.92, "low": 0.9, "high": 0.95} and fixed["capex_multiplier"] == 1.24
    )
    tracker = by_id["tracker_4m"]
    assert (tracker["kind"], tracker["height_m"], tracker["max_angle_deg"], tracker["azimuth_deg"]) == (
        "tracker",
        4.0,
        55.0,
        None,
    )
    vertical = by_id["vertical_bifacial_ew"]
    assert (vertical["kind"], vertical["azimuth_deg"], vertical["unfarmed_strip_m"]) == (
        "vertical",
        90.0,
        1.0,
    )
    assert out["modules"]["bifacial"] == {"efficiency": 0.225, "bifaciality": 0.8, "temp_coeff_per_c": -0.003}
    assert out["cost_points"]["fixed"] == [[2.5, 1.19], [3.0, 1.24], [4.0, 1.33]]
    assert out["limits"]["height_m"] == [0.5, 6.0] and out["limits"]["tilt_deg"] == [0.0, 40.0]


def test_sources_cover_what_the_app_shows():
    ids = {s["id"] for s in SOURCES}
    assert {"weather", "crop_shade", "crop_economics", "tariffs", "costs", "structures", "pvlib"} <= ids
    assert all(s["attribution"] and s["licence"] for s in SOURCES)


def test_build_writes_all_files(tmp_path):
    for part in ("research", "data/weather/index.json"):
        src, dst = REPO / part, tmp_path / part
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(
                src, dst, ignore=shutil.ignore_patterns("raw", "*.pdf", "*.xls", "*.shp", "*.dbf")
            )
        else:
            shutil.copy2(src, dst)
    manifest = main(tmp_path)
    app = tmp_path / "data" / "app"
    assert {p.name for p in app.iterdir()} == {"districts.json", "crops.json", "crop_economics.json", "finance_defaults.json",
                                                "structures.json", "sources.json", "manifest.json"}  # fmt: skip
    assert (
        manifest["files"]["districts.json"]["count"] == 785 and manifest["files"]["crops.json"]["count"] == 20
    )
    assert json.loads((app / "manifest.json").read_text(encoding="utf-8")) == manifest
    assert b"\r\n" not in (app / "crops.json").read_bytes()
    economics = json.loads((app / "crop_economics.json").read_text(encoding="utf-8"))
    assert economics["example_rotation"]["by_state"]["Rajasthan"][0] == {
        "season": "kharif",
        "crop_id": "bajra",
    }
