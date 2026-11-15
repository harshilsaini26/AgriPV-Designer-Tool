"""Build the web app's data files.

Usage: python -m pipeline.appdata.build_app_data <repo_root>

Reads the research tables and data/weather/index.json and writes, to data/app/: districts.json, crops.json,
crop_economics.json, finance_defaults.json, structures.json, sources.json and manifest.json (model-slice
spec §5). The outputs are committed; rebuild them when the research data changes.
"""

import csv
import hashlib
import json
import sys
from pathlib import Path

from pipeline.appdata.crops import build_crops
from pipeline.appdata.districts import build_districts
from pipeline.appdata.economics import build_crop_economics, build_example_rotations
from pipeline.appdata.finance import SOURCES, build_finance_defaults, build_structures

DATA_VERSION = "2026-11-15"


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _write(path: Path, payload) -> str:
    text = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(repo: Path) -> dict:
    research = repo / "research"
    shade = research / "09_crop_shade_response"
    finance_dir = research / "11_finance_policy"
    structures_dir = research / "12_structures_technology"
    economics_rows = _rows(
        research / "07_crop_economics" / "cost_of_cultivation" / "idp_des_cost_of_cultivation_1996-2022.csv"
    )
    index = json.loads((repo / "data" / "weather" / "index.json").read_text(encoding="utf-8"))["districts"]
    capex_rows = _rows(finance_dir / "capex_om" / "capex_om_benchmarks.csv")

    crops = build_crops(
        _rows(shade / "parameters" / "crop_parameters_draft.csv"),
        _rows(shade / "papers" / "bibliography.csv"),
    )
    economics = build_crop_economics(economics_rows)
    economics["example_rotation"] = build_example_rotations(economics_rows, crops)
    finance = build_finance_defaults(_rows(finance_dir / "kusum" / "kusum_a_state_tariffs.csv"), capex_rows)
    structures = build_structures(
        _rows(structures_dir / "structure_presets.csv"),
        _rows(structures_dir / "module_parameters.csv"),
        capex_rows,
    )
    outputs = {
        "districts.json": (build_districts(index), lambda p: len(p)),
        "crops.json": (crops, lambda p: len(p)),
        "crop_economics.json": (economics, lambda p: len(p["by_state"])),
        "finance_defaults.json": (finance, lambda p: len(p["tariffs"])),
        "structures.json": (structures, lambda p: len(p["presets"])),
        "sources.json": (SOURCES, lambda p: len(p)),
    }
    out_dir = repo / "data" / "app"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"data_version": DATA_VERSION, "files": {}}
    for name, (payload, count) in outputs.items():
        manifest["files"][name] = {"sha256": _write(out_dir / name, payload), "count": count(payload)}
    _write(out_dir / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    result = main(Path(sys.argv[1]))
    for name, info in result["files"].items():
        print(f"{name:<24} {info['count']:>4}")
