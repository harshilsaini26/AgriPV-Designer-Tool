"""The app's data: the JSON files in data/app/ and the weather packs in data/weather/ (model-slice spec §5)."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from backend._paths import REPO_ROOT

APP_DATA_DIR = REPO_ROOT / "data" / "app"
WEATHER_DIR = REPO_ROOT / "data" / "weather"
FILES = (
    "districts.json",
    "crops.json",
    "crop_economics.json",
    "finance_defaults.json",
    "structures.json",
    "sources.json",
    "manifest.json",
)
PREVIEW_NOTICE = (
    "Preview: crop shade parameters are draft, crop economics are state-level figures for 2021-22, "
    "and loan terms are assumptions."
)
DEFAULT_TILT_RANGE_DEG = (10.0, 25.0)


@dataclass(frozen=True)
class AppData:
    districts: dict[str, dict]
    crops: dict[str, dict]
    economics: dict
    finance: dict
    structures: dict
    sources: list[dict]
    manifest: dict


def _read(directory: Path) -> AppData:
    for name in FILES:
        if not (directory / name).is_file():
            raise RuntimeError(f"app data is missing: {directory / name}")
    raw = {name: json.loads((directory / name).read_text(encoding="utf-8")) for name in FILES}
    return AppData(
        districts={d["id"]: d for d in raw["districts.json"]},
        crops={c["id"]: c for c in raw["crops.json"]},
        economics=raw["crop_economics.json"],
        finance=raw["finance_defaults.json"],
        structures=raw["structures.json"],
        sources=raw["sources.json"],
        manifest=raw["manifest.json"],
    )


@lru_cache(maxsize=1)
def load_app_data() -> AppData:
    """The app data, read once. Raises RuntimeError naming the first missing file."""
    return _read(APP_DATA_DIR)


def economics_for(app: AppData, state: str, crop_id: str) -> dict | None:
    """The state's figures for a crop, else the national median, else None."""
    state_entry = app.economics["by_state"].get(state, {}).get(crop_id)
    if state_entry is not None:
        return state_entry
    return app.economics["national"].get(crop_id)


def tariff_for(app: AppData, state: str) -> dict:
    """The state's PM-KUSUM A tariff entry, else the national fallback."""
    return app.finance["tariffs"].get(state, app.finance["national_fallback"])


def example_rotation_for(app: AppData, state: str) -> dict:
    """Example crops: the state's kharif and rabi pair when it has both, otherwise the national pair."""
    examples = app.economics["example_rotation"]
    pair = examples["by_state"].get(state, [])
    if {e["season"] for e in pair} >= {"kharif", "rabi"}:
        return {"basis": "state", "crops": pair}
    return {"basis": "national", "crops": examples["national"]}


def default_tilt_deg(district: dict) -> float:
    lo, hi = DEFAULT_TILT_RANGE_DEG
    return float(min(max(district["optimum_tilt_deg"], lo), hi))


def weather_path(district_id: str) -> Path:
    return WEATHER_DIR / f"{district_id}.npz"
